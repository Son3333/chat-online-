"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.PythonBridge = void 0;
const net = __importStar(require("net"));
class PythonBridge {
    host;
    port;
    socket = null;
    connected = false;
    buffer = Buffer.alloc(0);
    pendingRequests = new Map();
    eventCallbacks = [];
    reconnectTimer = null;
    currentUserId = null;
    constructor(host = '127.0.0.1', port = 8888) {
        this.host = host;
        this.port = port;
    }
    setEndpoint(host, port) {
        this.host = host;
        this.port = port;
    }
    getEndpoint() {
        return { host: this.host, port: this.port };
    }
    connect() {
        return new Promise((resolve) => {
            if (this.socket) {
                this.socket.destroy();
            }
            this.socket = new net.Socket();
            this.socket.setTimeout(5000);
            this.socket.connect(this.port, this.host, () => {
                this.connected = true;
                this.socket?.setTimeout(0);
                this.socket?.setKeepAlive(true, 5000);
                this.buffer = Buffer.alloc(0);
                if (this.reconnectTimer) {
                    clearInterval(this.reconnectTimer);
                    this.reconnectTimer = null;
                }
                // Auto re-identify if we have a current session
                if (this.currentUserId) {
                    this.sendRequest('identify', { user_id: this.currentUserId }).catch(() => { });
                }
                this.emitEvent({ type: 'connection_status', connected: true });
                resolve(true);
            });
            this.socket.on('data', (data) => {
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
    handleDisconnect() {
        this.connected = false;
        this.emitEvent({ type: 'connection_status', connected: false });
        this.scheduleReconnect();
    }
    scheduleReconnect() {
        if (this.reconnectTimer)
            return;
        this.reconnectTimer = setInterval(async () => {
            if (!this.connected) {
                await this.connect();
            }
        }, 2500);
    }
    processBuffer() {
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
                const packet = JSON.parse(jsonStr);
                this.handleIncomingPacket(packet);
            }
            catch (e) {
                console.error('[PythonBridge] Failed to parse JSON packet:', e);
            }
        }
    }
    handleIncomingPacket(packet) {
        const action = packet.action;
        // 1. Precise match by file_id for file downloads (prevents concurrent download race conditions)
        if (packet.file_id !== undefined) {
            const keyStr = `download_file_${String(packet.file_id)}`;
            const keyNum = `download_file_${Number(packet.file_id)}`;
            const matchedKey = this.pendingRequests.has(keyStr) ? keyStr : (this.pendingRequests.has(keyNum) ? keyNum : null);
            if (matchedKey) {
                const req = this.pendingRequests.get(matchedKey);
                clearTimeout(req.timeoutId);
                this.pendingRequests.delete(matchedKey);
                req.resolve(packet);
                return;
            }
        }
        // 1.5. Precise match by conversation_id for get_messages (prevents cross-conversation history leakage)
        if (packet.conversation_id !== undefined && (action === 'messages_history' || action === 'get_messages_response' || action === 'get_messages')) {
            const keyStr = `get_messages_${String(packet.conversation_id)}`;
            const keyNum = `get_messages_${Number(packet.conversation_id)}`;
            const matchedKey = this.pendingRequests.has(keyStr) ? keyStr : (this.pendingRequests.has(keyNum) ? keyNum : null);
            if (matchedKey) {
                const req = this.pendingRequests.get(matchedKey);
                clearTimeout(req.timeoutId);
                this.pendingRequests.delete(matchedKey);
                req.resolve(packet);
                return;
            }
        }
        // Fallback: match any pending download_file request if action is download_response
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
        const ACTION_RESPONSE_MAP = {
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
        };
        // Check if there is an in-flight request waiting for this action response directly
        if (action && this.pendingRequests.has(action)) {
            const req = this.pendingRequests.get(action);
            clearTimeout(req.timeoutId);
            this.pendingRequests.delete(action);
            if (packet.success && packet.user?.id) {
                this.currentUserId = Number(packet.user.id);
            }
            req.resolve(packet);
            return;
        }
        // Match response variants like 'login_response' for 'login', or aliases in ACTION_RESPONSE_MAP
        for (const [reqAction, req] of this.pendingRequests.entries()) {
            const aliases = ACTION_RESPONSE_MAP[reqAction] || [];
            if (action === `${reqAction}_response` ||
                action === reqAction ||
                (action && aliases.includes(action))) {
                clearTimeout(req.timeoutId);
                this.pendingRequests.delete(reqAction);
                if (packet.success && packet.user?.id) {
                    this.currentUserId = Number(packet.user.id);
                }
                req.resolve(packet);
                return;
            }
        }
        // Otherwise it is a push event broadcast from server (new_message, user_status_changed, etc.)
        this.emitEvent(packet);
    }
    async sendRequest(action, payload = {}, timeoutMs = 25000) {
        // Tự động thử kết nối lại ngay nếu hiện tại chưa kết nối
        if (!this.connected || !this.socket || this.socket.destroyed) {
            console.log(`[PythonBridge] Socket not connected for '${action}', attempting to connect to ${this.host}:${this.port}...`);
            await this.connect();
        }
        if (!this.connected || !this.socket) {
            throw new Error(`Chưa kết nối đến máy chủ (${this.host}:${this.port})! Vui lòng kiểm tra lại địa chỉ máy chủ.`);
        }
        return new Promise((resolve, reject) => {
            // Extended timeout for large media/file transfers over WAN
            const isFileTransfer = action === 'download_file' || action === 'upload_file';
            const isCallAction = action.startsWith('call_') || action === 'check_call_status';
            const actualTimeout = isFileTransfer ? 90000 : (isCallAction ? 35000 : timeoutMs);
            // Unique tracking key for download_file by file_id, get_messages by conversation_id
            let trackingKey = action;
            if (action === 'download_file' && payload.file_id !== undefined) {
                trackingKey = `download_file_${payload.file_id}`;
            }
            else if (action === 'get_messages' && payload.conversation_id !== undefined) {
                trackingKey = `get_messages_${payload.conversation_id}`;
            }
            const reqPayload = { action, ...payload };
            const jsonBuffer = Buffer.from(JSON.stringify(reqPayload), 'utf-8');
            const header = Buffer.alloc(4);
            header.writeUInt32BE(jsonBuffer.length, 0);
            // Fire-and-forget for real-time video frames (no timeout overhead)
            if (action === 'call_media') {
                try {
                    if (this.socket) {
                        this.socket.write(Buffer.concat([header, jsonBuffer]));
                    }
                    return resolve({ success: true });
                }
                catch (err) {
                    return reject(err);
                }
            }
            const timeoutId = setTimeout(() => {
                this.pendingRequests.delete(trackingKey);
                reject(new Error(`Yêu cầu '${action}' quá thời gian chờ (${actualTimeout}ms)`));
            }, actualTimeout);
            this.pendingRequests.set(trackingKey, { resolve, reject, timeoutId });
            try {
                if (!this.socket) {
                    clearTimeout(timeoutId);
                    this.pendingRequests.delete(trackingKey);
                    return reject(new Error('Socket không khả dụng'));
                }
                this.socket.write(Buffer.concat([header, jsonBuffer]));
            }
            catch (err) {
                clearTimeout(timeoutId);
                this.pendingRequests.delete(trackingKey);
                reject(err);
            }
        });
    }
    onEvent(callback) {
        this.eventCallbacks.push(callback);
    }
    emitEvent(event) {
        for (const cb of this.eventCallbacks) {
            try {
                cb(event);
            }
            catch (err) {
                console.error('[PythonBridge] Error in event callback:', err);
            }
        }
    }
    disconnect() {
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
    isConnected() {
        return this.connected;
    }
}
exports.PythonBridge = PythonBridge;
