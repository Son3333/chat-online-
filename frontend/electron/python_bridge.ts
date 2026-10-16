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
    const type = packet.type;

    // Check if there is an in-flight request waiting for this action response
    if (action && this.pendingRequests.has(action)) {
      const req = this.pendingRequests.get(action)!;
      clearTimeout(req.timeoutId);
      this.pendingRequests.delete(action);
      req.resolve(packet);
      return;
    }

    // Also match response variants like 'login_response' for 'login'
    for (const [reqAction, req] of this.pendingRequests.entries()) {
      if (action === `${reqAction}_response` || action === reqAction) {
        clearTimeout(req.timeoutId);
        this.pendingRequests.delete(reqAction);
        req.resolve(packet);
        return;
      }
    }

    // Otherwise it is a push event broadcast from server (new_message, user_status_changed, etc.)
    this.emitEvent(packet);
  }

  public sendRequest(action: string, payload: Record<string, any> = {}, timeoutMs = 8000): Promise<PythonPacket> {
    return new Promise((resolve, reject) => {
      if (!this.connected || !this.socket) {
        return reject(new Error('Chưa kết nối đến máy chủ Python!'));
      }

      const reqPayload = { action, ...payload };
      const jsonBuffer = Buffer.from(JSON.stringify(reqPayload), 'utf-8');
      const header = Buffer.alloc(4);
      header.writeUInt32BE(jsonBuffer.length, 0);

      const timeoutId = setTimeout(() => {
        this.pendingRequests.delete(action);
        reject(new Error(`Yêu cầu '${action}' quá thời gian chờ (${timeoutMs}ms)`));
      }, timeoutMs);

      this.pendingRequests.set(action, { resolve, reject, timeoutId });

      try {
        this.socket.write(Buffer.concat([header, jsonBuffer]));
      } catch (err) {
        clearTimeout(timeoutId);
        this.pendingRequests.delete(action);
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

