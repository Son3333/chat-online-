import * as net from 'net';

export interface PythonPacket {
  action?: string;
  type?: string;
  success?: boolean;
  error?: string;
  [key: string]: any;
}

export class PythonBridge {
  private host: string;
  private port: number;

  // Dual-Socket Architecture: 2 Kênh băng thông độc lập
  // Kênh 1: Data & Chat Socket (Tin nhắn, Đăng nhập, Bạn bè, Lịch sử, Tải file nặng)
  private dataSocket: net.Socket | null = null;
  private dataConnected: boolean = false;
  private dataBuffer: Buffer = Buffer.alloc(0);

  // Kênh 2: Real-time Media Socket (Chuyên dụng cho Mic PCM, Webcam, Báo hiệu gọi)
  private mediaSocket: net.Socket | null = null;
  private mediaConnected: boolean = false;
  private mediaBuffer: Buffer = Buffer.alloc(0);

  private pendingRequests = new Map<string, { resolve: (val: any) => void; reject: (err: any) => void; timeoutId: NodeJS.Timeout }>();
  private eventCallbacks: ((event: PythonPacket) => void)[] = [];
  private reconnectTimer: NodeJS.Timeout | null = null;
  private connectingPromise: Promise<boolean> | null = null;
  public currentUserId: number | null = null;

  constructor(host = '127.0.0.1', port = 8888) {
    this.host = host;
    this.port = port;
  }

  public setEndpoint(host: string, port: number) {
    this.host = host;
    this.port = port;
  }

  public getEndpoint(): { host: string; port: number } {
    return { host: this.host, port: this.port };
  }

  public connect(): Promise<boolean> {
    if (this.dataConnected && this.dataSocket && !this.dataSocket.destroyed) {
      // Đảm bảo kênh media cũng được kết nối nếu chưa có
      if (!this.mediaConnected || !this.mediaSocket || this.mediaSocket.destroyed) {
        this.connectMediaChannel().catch(() => {});
      }
      return Promise.resolve(true);
    }

    if (this.connectingPromise) {
      return this.connectingPromise;
    }

    this.connectingPromise = new Promise(async (resolve) => {
      const dataOk = await this.connectDataChannel();
      if (dataOk) {
        this.connectMediaChannel().catch(() => {});
        this.emitEvent({ type: 'connection_status', connected: true });
        this.connectingPromise = null;
        resolve(true);
      } else {
        this.connectingPromise = null;
        resolve(false);
      }
    });

    return this.connectingPromise;
  }

  /**
   * KẾT NỐI KÊNH 1: Data & Chat Socket
   */
  private connectDataChannel(): Promise<boolean> {
    return new Promise((resolve) => {
      if (this.dataSocket) {
        try { this.dataSocket.destroy(); } catch {}
      }

      this.dataSocket = new net.Socket();
      this.dataSocket.setTimeout(6000);

      this.dataSocket.connect(this.port, this.host, () => {
        this.dataConnected = true;
        this.dataSocket?.setTimeout(0);
        this.dataSocket?.setKeepAlive(true, 5000);
        this.dataBuffer = Buffer.alloc(0);

        if (this.reconnectTimer) {
          clearInterval(this.reconnectTimer);
          this.reconnectTimer = null;
        }

        // Tự động định danh kênh Data
        if (this.currentUserId) {
          this.sendSocketPacket(this.dataSocket, {
            action: 'identify',
            user_id: this.currentUserId,
            channel_type: 'data',
          });
        }

        resolve(true);
      });

      this.dataSocket.on('data', (data: Buffer) => {
        this.dataBuffer = Buffer.concat([this.dataBuffer, data]);
        this.processDataBuffer();
      });

      this.dataSocket.on('error', (err) => {
        console.warn('[PythonBridge] Data Socket error:', err.message);
        this.handleDataDisconnect();
        resolve(false);
      });

      this.dataSocket.on('close', () => {
        this.handleDataDisconnect();
        resolve(false);
      });

      this.dataSocket.on('timeout', () => {
        if (!this.dataConnected) {
          try { this.dataSocket?.destroy(); } catch {}
          resolve(false);
        }
      });
    });
  }

  /**
   * KẾT NỐI KÊNH 2: Real-time Media Socket (Độc lập cho Voice & Video)
   */
  private connectMediaChannel(): Promise<boolean> {
    return new Promise((resolve) => {
      if (this.mediaSocket) {
        try { this.mediaSocket.destroy(); } catch {}
      }

      this.mediaSocket = new net.Socket();
      this.mediaSocket.setTimeout(6000);

      this.mediaSocket.connect(this.port, this.host, () => {
        this.mediaConnected = true;
        this.mediaSocket?.setTimeout(0);
        this.mediaSocket?.setKeepAlive(true, 5000);
        this.mediaBuffer = Buffer.alloc(0);

        // Tự động định danh kênh Media
        if (this.currentUserId) {
          this.sendSocketPacket(this.mediaSocket, {
            action: 'identify',
            user_id: this.currentUserId,
            channel_type: 'media',
          });
        }
        resolve(true);
      });

      this.mediaSocket.on('data', (data: Buffer) => {
        this.mediaBuffer = Buffer.concat([this.mediaBuffer, data]);
        this.processMediaBuffer();
      });

      this.mediaSocket.on('error', (err) => {
        console.warn('[PythonBridge] Media Socket error:', err.message);
        this.mediaConnected = false;
        resolve(false);
      });

      this.mediaSocket.on('close', () => {
        this.mediaConnected = false;
        resolve(false);
      });

      this.mediaSocket.on('timeout', () => {
        if (!this.mediaConnected) {
          try { this.mediaSocket?.destroy(); } catch {}
          resolve(false);
        }
      });
    });
  }

  private handleDataDisconnect() {
    this.dataConnected = false;
    this.connectingPromise = null;
    this.emitEvent({ type: 'connection_status', connected: false });
    this.scheduleReconnect();
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setInterval(async () => {
      if (!this.dataConnected) {
        await this.connect();
      }
    }, 2500);
  }

  private processDataBuffer() {
    while (this.dataBuffer.length >= 4) {
      const packetLength = this.dataBuffer.readUInt32BE(0);
      if (this.dataBuffer.length < 4 + packetLength) {
        break;
      }

      const packetData = this.dataBuffer.subarray(4, 4 + packetLength);
      const remaining = this.dataBuffer.subarray(4 + packetLength);
      this.dataBuffer = remaining.length > 0 ? Buffer.from(remaining) : Buffer.alloc(0);

      try {
        const jsonStr = packetData.toString('utf-8');
        const packet: PythonPacket = JSON.parse(jsonStr);
        this.handleIncomingPacket(packet);
      } catch (e) {
        console.error('[PythonBridge] Failed to parse Data JSON packet:', e);
      }
    }
  }

  private processMediaBuffer() {
    while (this.mediaBuffer.length >= 4) {
      const packetLength = this.mediaBuffer.readUInt32BE(0);
      if (this.mediaBuffer.length < 4 + packetLength) {
        break;
      }

      const packetData = this.mediaBuffer.subarray(4, 4 + packetLength);
      const remaining = this.mediaBuffer.subarray(4 + packetLength);
      this.mediaBuffer = remaining.length > 0 ? Buffer.from(remaining) : Buffer.alloc(0);

      try {
        const jsonStr = packetData.toString('utf-8');
        const packet: PythonPacket = JSON.parse(jsonStr);
        this.handleIncomingPacket(packet);
      } catch (e) {
        console.error('[PythonBridge] Failed to parse Media JSON packet:', e);
      }
    }
  }

  private handleIncomingPacket(packet: PythonPacket) {
    const action = packet.action;

    // 1. Khớp chính xác theo file_id cho download file
    if (packet.file_id !== undefined) {
      const keyStr = `download_file_${String(packet.file_id)}`;
      const keyNum = `download_file_${Number(packet.file_id)}`;
      const matchedKey = this.pendingRequests.has(keyStr) ? keyStr : (this.pendingRequests.has(keyNum) ? keyNum : null);
      if (matchedKey) {
        const req = this.pendingRequests.get(matchedKey)!;
        clearTimeout(req.timeoutId);
        this.pendingRequests.delete(matchedKey);
        req.resolve(packet);
        return;
      }
    }

    // 1.5. Khớp chính xác theo conversation_id cho get_messages
    if (action === 'messages_history' || action === 'get_messages_response' || action === 'get_messages') {
      if (packet.conversation_id !== undefined) {
        const keyStr = `get_messages_${String(packet.conversation_id)}`;
        const keyNum = `get_messages_${Number(packet.conversation_id)}`;
        const matchedKey = this.pendingRequests.has(keyStr) ? keyStr : (this.pendingRequests.has(keyNum) ? keyNum : null);
        if (matchedKey) {
          const req = this.pendingRequests.get(matchedKey)!;
          clearTimeout(req.timeoutId);
          this.pendingRequests.delete(matchedKey);
          req.resolve(packet);
          return;
        }
      }

      for (const [key, req] of this.pendingRequests.entries()) {
        if (key === 'get_messages' || key.startsWith('get_messages_')) {
          clearTimeout(req.timeoutId);
          this.pendingRequests.delete(key);
          req.resolve(packet);
          return;
        }
      }
    }

    // Fallback cho download_file
    if (action === 'download_response' || action === 'download_file_response') {
      for (const [key, req] of this.pendingRequests.entries()) {
        if (key.startsWith('download_file_')) {
          clearTimeout(req.timeoutId);
          this.pendingRequests.delete(key);
          req.resolve(packet);
          return;
        }
      }
    }

    const ACTION_RESPONSE_MAP: Record<string, string[]> = {
      get_conversations: ['conversations_list', 'get_conversations_response', 'get_conversations'],
      get_messages: ['messages_history', 'get_messages_response', 'get_messages'],
      search_users: ['search_results', 'search_users_response', 'search_users'],
      upload_file: ['upload_response', 'upload_file_response', 'upload_file'],
      download_file: ['download_response', 'download_file_response', 'download_file'],
      start_direct_chat: ['direct_chat_started', 'start_direct_chat_response', 'start_direct_chat'],
      create_group: ['create_group_response', 'create_group'],
      check_call_status: ['check_call_status_response', 'check_call_status'],
      call_invite: ['call_invite_response', 'call_invite'],
      call_accept: ['call_accept_response', 'call_accept'],
      call_end: ['call_end_response', 'call_end'],
      call_reject: ['call_reject_response', 'call_reject'],
      get_friends: ['get_friends_response', 'get_friends'],
      add_friend: ['add_friend_response', 'add_friend'],
      accept_friend: ['accept_friend_response', 'accept_friend'],
      reject_friend: ['reject_friend_response', 'reject_friend'],
      remove_friend: ['remove_friend_response', 'remove_friend'],
      check_friend: ['check_friend_response', 'check_friend'],
      get_pinned_message: ['get_pinned_message_response', 'get_pinned_message'],
    };

    if (action && this.pendingRequests.has(action)) {
      const req = this.pendingRequests.get(action)!;
      clearTimeout(req.timeoutId);
      this.pendingRequests.delete(action);
      if (packet.success && packet.user?.id) {
        this.currentUserId = Number(packet.user.id);
        this.reIdentifyBothChannels(this.currentUserId);
      }
      req.resolve(packet);
      return;
    }

    for (const [reqAction, req] of this.pendingRequests.entries()) {
      const baseAction = reqAction.replace(/_\d+$/, '');
      const aliases = ACTION_RESPONSE_MAP[baseAction] || ACTION_RESPONSE_MAP[reqAction] || [];
      if (
        action === `${reqAction}_response` ||
        action === `${baseAction}_response` ||
        action === reqAction ||
        action === baseAction ||
        (action && aliases.includes(action))
      ) {
        clearTimeout(req.timeoutId);
        this.pendingRequests.delete(reqAction);
        if (packet.success && packet.user?.id) {
          this.currentUserId = Number(packet.user.id);
          this.reIdentifyBothChannels(this.currentUserId);
        }
        req.resolve(packet);
        return;
      }
    }

    // Sự kiện push từ server (new_message, call_media_relay, call_incoming, user_status_changed,...)
    this.emitEvent(packet);
  }

  private reIdentifyBothChannels(userId: number) {
    if (this.dataSocket && this.dataConnected) {
      this.sendSocketPacket(this.dataSocket, { action: 'identify', user_id: userId, channel_type: 'data' });
    }
    if (this.mediaSocket && this.mediaConnected) {
      this.sendSocketPacket(this.mediaSocket, { action: 'identify', user_id: userId, channel_type: 'media' });
    } else {
      this.connectMediaChannel().catch(() => {});
    }
  }

  private sendSocketPacket(sock: net.Socket | null, payload: Record<string, any>): boolean {
    try {
      if (!sock || sock.destroyed) return false;
      const jsonBuffer = Buffer.from(JSON.stringify(payload), 'utf-8');
      const header = Buffer.alloc(4);
      header.writeUInt32BE(jsonBuffer.length, 0);
      sock.write(Buffer.concat([header, jsonBuffer]));
      return true;
    } catch {
      return false;
    }
  }

  public async sendRequest(action: string, payload: Record<string, any> = {}, timeoutMs = 25000): Promise<PythonPacket> {
    if (!this.dataConnected || !this.dataSocket || this.dataSocket.destroyed) {
      await this.connect();
    }

    if (!this.dataConnected || !this.dataSocket) {
      throw new Error(`Chưa kết nối đến máy chủ (${this.host}:${this.port})! Vui lòng kiểm tra lại địa chỉ máy chủ.`);
    }

    // Phân loại luồng lưu lượng:
    // Cuộc gọi (call_media, call_invite, call_accept, call_end, check_call_status) -> Đi Kênh 2 (Media Socket)
    // Toàn bộ tác vụ khác (tin nhắn, tải file, kết bạn, lịch sử) -> Đi Kênh 1 (Data Socket)
    const isCallTraffic = action === 'call_media' || action.startsWith('call_') || action === 'check_call_status';
    const targetSocket = (isCallTraffic && this.mediaSocket && this.mediaConnected && !this.mediaSocket.destroyed)
      ? this.mediaSocket
      : this.dataSocket;

    return new Promise((resolve, reject) => {
      const isFileTransfer = action === 'download_file' || action === 'upload_file';
      const actualTimeout = isFileTransfer ? 90000 : (isCallTraffic ? 35000 : timeoutMs);

      let trackingKey = action;
      if (action === 'download_file' && payload.file_id !== undefined) {
        trackingKey = `download_file_${payload.file_id}`;
      } else if (action === 'get_messages' && payload.conversation_id !== undefined) {
        trackingKey = `get_messages_${payload.conversation_id}`;
      }

      const reqPayload = { action, ...payload };
      const jsonBuffer = Buffer.from(JSON.stringify(reqPayload), 'utf-8');
      const header = Buffer.alloc(4);
      header.writeUInt32BE(jsonBuffer.length, 0);

      // Dữ liệu âm thanh/video thời gian thực: Gửi siêu tốc trực tiếp trên kênh Media
      if (action === 'call_media') {
        try {
          targetSocket.write(Buffer.concat([header, jsonBuffer]));
          return resolve({ success: true });
        } catch (err) {
          return reject(err);
        }
      }

      const timeoutId = setTimeout(() => {
        this.pendingRequests.delete(trackingKey);
        reject(new Error(`Yêu cầu '${action}' quá thời gian chờ (${actualTimeout}ms)`));
      }, actualTimeout);

      this.pendingRequests.set(trackingKey, { resolve, reject, timeoutId });

      try {
        targetSocket.write(Buffer.concat([header, jsonBuffer]));
      } catch (err) {
        clearTimeout(timeoutId);
        this.pendingRequests.delete(trackingKey);
        reject(err);
      }
    });
  }

  public onEvent(callback: (event: PythonPacket) => void) {
    this.eventCallbacks.push(callback);
  }

  private emitEvent(event: PythonPacket) {
    for (const cb of this.eventCallbacks) {
      try {
        cb(event);
      } catch (err) {
        console.error('[PythonBridge] Error in event callback:', err);
      }
    }
  }

  public disconnect() {
    if (this.reconnectTimer) {
      clearInterval(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.dataConnected = false;
    this.mediaConnected = false;
    this.currentUserId = null;
    if (this.dataSocket) {
      try { this.dataSocket.destroy(); } catch {}
      this.dataSocket = null;
    }
    if (this.mediaSocket) {
      try { this.mediaSocket.destroy(); } catch {}
      this.mediaSocket = null;
    }
  }

  public isConnected(): boolean {
    return this.dataConnected;
  }
}
