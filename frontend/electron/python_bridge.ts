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
  private socket: net.Socket | null = null;
  private connected: boolean = false;
  private buffer: Buffer = Buffer.alloc(0);
  private pendingRequests = new Map<string, { resolve: (val: any) => void; reject: (err: any) => void; timeoutId: NodeJS.Timeout }>();
  private eventCallbacks: ((event: PythonPacket) => void)[] = [];
  private reconnectTimer: NodeJS.Timeout | null = null;
  public currentUserId: number | null = null;

  constructor(host = '127.0.0.1', port = 8888) {
    this.host = host;
    this.port = port;
  }

  public connect(): Promise<boolean> {
    return new Promise((resolve) => {
      if (this.socket) {
        this.socket.destroy();
      }

      this.socket = new net.Socket();
      this.socket.setTimeout(5000);

      this.socket.connect(this.port, this.host, () => {
        this.connected = true;
        this.buffer = Buffer.alloc(0);
        if (this.reconnectTimer) {
          clearInterval(this.reconnectTimer);
          this.reconnectTimer = null;
        }

        // Auto re-identify if we have a current session
        if (this.currentUserId) {
          this.sendRequest('identify', { user_id: this.currentUserId }).catch(() => {});
        }

        this.emitEvent({ type: 'connection_status', connected: true });
        resolve(true);
      });

      this.socket.on('data', (data: Buffer) => {
        this.buffer = Buffer.concat([this.buffer, data]);
        this.processBuffer();
      });

      this.socket.on('error', (err) => {
        console.warn('[PythonBridge] Socket error:', err.message);
        this.handleDisconnect();
        resolve(false);
      });

      this.socket.on('close', () => {
        this.handleDisconnect();
      });

      this.socket.on('timeout', () => {
        if (!this.connected) {
          this.socket?.destroy();
          resolve(false);
        }
      });
    });
  }

  private handleDisconnect() {
    this.connected = false;
    this.emitEvent({ type: 'connection_status', connected: false });
    this.scheduleReconnect();
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setInterval(async () => {
      if (!this.connected) {
        await this.connect();
      }
    }, 2500);
  }

  private processBuffer() {
    while (this.buffer.length >= 4) {
      const packetLength = this.buffer.readUInt32BE(0);
      if (this.buffer.length < 4 + packetLength) {
        // Chờ thêm data phân mảnh
        break;
      }

      const packetData = this.buffer.subarray(4, 4 + packetLength);
      this.buffer = this.buffer.subarray(4 + packetLength);

      try {
        const jsonStr = packetData.toString('utf-8');
        const packet: PythonPacket = JSON.parse(jsonStr);
        this.handleIncomingPacket(packet);
      } catch (e) {
        console.error('[PythonBridge] Failed to parse JSON packet:', e);
      }
    }
  }

  private handleIncomingPacket(packet: PythonPacket) {
    const action = packet.action;

    // 1. Precise match by file_id for file downloads (prevents concurrent download race conditions)
    if (packet.file_id !== undefined) {
      const fileKey = `download_file_${packet.file_id}`;
      if (this.pendingRequests.has(fileKey)) {
        const req = this.pendingRequests.get(fileKey)!;
        clearTimeout(req.timeoutId);
        this.pendingRequests.delete(fileKey);
        req.resolve(packet);
        return;
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
    };

    // Check if there is an in-flight request waiting for this action response directly
    if (action && this.pendingRequests.has(action)) {
      const req = this.pendingRequests.get(action)!;
      clearTimeout(req.timeoutId);
      this.pendingRequests.delete(action);
      req.resolve(packet);
      return;
    }

    // Match response variants like 'login_response' for 'login', or aliases in ACTION_RESPONSE_MAP
    for (const [reqAction, req] of this.pendingRequests.entries()) {
      const aliases = ACTION_RESPONSE_MAP[reqAction] || [];
      if (
        action === `${reqAction}_response` ||
        action === reqAction ||
        (action && aliases.includes(action))
      ) {
        clearTimeout(req.timeoutId);
        this.pendingRequests.delete(reqAction);
        req.resolve(packet);
        return;
      }
    }

    // Otherwise it is a push event broadcast from server (new_message, user_status_changed, etc.)
    this.emitEvent(packet);
  }

  public sendRequest(action: string, payload: Record<string, any> = {}, timeoutMs = 12000): Promise<PythonPacket> {
    return new Promise((resolve, reject) => {
      if (!this.connected || !this.socket) {
        return reject(new Error('Chưa kết nối đến máy chủ Python!'));
      }

      // Extended timeout for large media/file transfers over WAN
      const isFileTransfer = action === 'download_file' || action === 'upload_file';
      const actualTimeout = isFileTransfer ? 60000 : timeoutMs;

      // Unique tracking key for download_file by file_id
      const trackingKey = (action === 'download_file' && payload.file_id !== undefined)
        ? `download_file_${payload.file_id}`
        : action;

      const reqPayload = { action, ...payload };
      const jsonBuffer = Buffer.from(JSON.stringify(reqPayload), 'utf-8');
      const header = Buffer.alloc(4);
      header.writeUInt32BE(jsonBuffer.length, 0);

      const timeoutId = setTimeout(() => {
        this.pendingRequests.delete(trackingKey);
        reject(new Error(`Yêu cầu '${action}' quá thời gian chờ (${actualTimeout}ms)`));
      }, actualTimeout);

      this.pendingRequests.set(trackingKey, { resolve, reject, timeoutId });

      try {
        this.socket.write(Buffer.concat([header, jsonBuffer]));
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
    this.connected = false;
    this.currentUserId = null;
    if (this.socket) {
      this.socket.destroy();
      this.socket = null;
    }
  }

  public isConnected(): boolean {
    return this.connected;
  }
}

