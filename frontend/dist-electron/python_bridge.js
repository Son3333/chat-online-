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
    // Dual-Socket Architecture: 2 Kênh băng thông độc lập
    // Kênh 1: Data & Chat Socket (Tin nhắn, Đăng nhập, Bạn bè, Lịch sử, Tải file nặng)
    dataSocket = null;
    dataConnected = false;
    dataBuffer = Buffer.alloc(0);
    // Kênh 2: Real-time Media Socket (Chuyên dụng cho Mic PCM, Webcam, Báo hiệu gọi)
    mediaSocket = null;
    mediaConnected = false;
    mediaIdentified = false;
    mediaBuffer = Buffer.alloc(0);
    pendingRequests = new Map();
    eventCallbacks = [];
    reconnectTimer = null;
    mediaReconnectTimer = null;
    connectingPromise = null;
    currentUserId = null;
    sessionToken = null;
    constructor(host = '127.0.0.1', port = 8888) {
        this.host = host;
        this.port = port;
    }
    async clearSession() {
        this.currentUserId = null;
        this.sessionToken = null;
        this.disconnect();
        await this.connect();
    }
    setEndpoint(host, port) {
        const changed = this.host !== host || this.port !== port;
        this.host = host;
        this.port = port;
        if (changed) {
            this.dataConnected = false;
            this.mediaConnected = false;
            this.mediaIdentified = false;
            this.connectingPromise = null;
            if (this.dataSocket) {
                try {
                    this.dataSocket.destroy();
                }
                catch { }
                this.dataSocket = null;
            }
            if (this.mediaSocket) {
                try {
                    this.mediaSocket.destroy();
                }
                catch { }
                this.mediaSocket = null;
            }
        }
    }
    getEndpoint() {
        return { host: this.host, port: this.port };
    }
    connect() {
        if (this.dataConnected && this.dataSocket && !this.dataSocket.destroyed) {
            // Đảm bảo kênh media cũng được kết nối nếu chưa có
            if (!this.mediaConnected || !this.mediaSocket || this.mediaSocket.destroyed) {
                this.connectMediaChannel().catch(() => { });
            }
            return Promise.resolve(true);
        }
        if (this.connectingPromise) {
            return this.connectingPromise;
        }
        this.connectingPromise = new Promise(async (resolve) => {
            const dataOk = await this.connectDataChannel();
            if (dataOk) {
                this.connectMediaChannel().catch(() => { });
                this.emitEvent({ type: 'connection_status', connected: true });
                this.connectingPromise = null;
                resolve(true);
            }
            else {
                this.connectingPromise = null;
                resolve(false);
            }
        });
        return this.connectingPromise;
    }
    /**
     * KẾT NỐI KÊNH 1: Data & Chat Socket
     */
    connectDataChannel() {
        return new Promise((resolve) => {
            if (this.dataSocket) {
                try {
                    this.dataSocket.destroy();
                }
                catch { }
            }
            this.dataSocket = new net.Socket();
            this.dataSocket.setTimeout(6000);
            this.dataSocket.connect(this.port, this.host, () => {
                this.dataConnected = true;
                this.dataSocket?.setTimeout(0);
                this.dataSocket?.setNoDelay(true);
                this.dataSocket?.setKeepAlive(true, 5000);
                this.dataBuffer = Buffer.alloc(0);
                if (this.reconnectTimer) {
                    clearInterval(this.reconnectTimer);
                    this.reconnectTimer = null;
                }
                if (this.currentUserId && this.sessionToken) {
                    this.sendSocketPacket(this.dataSocket, {
                        action: 'identify',
                        user_id: this.currentUserId,
                        session_token: this.sessionToken,
                        channel_type: 'data',
                    });
                }
                resolve(true);
            });
            this.dataSocket.on('data', (data) => {
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
                    try {
                        this.dataSocket?.destroy();
                    }
                    catch { }
                    resolve(false);
                }
            });
        });
    }
    /**
     * KẾT NỐI KÊNH 2: Real-time Media Socket (Độc lập cho Voice & Video)
     */
    connectMediaChannel() {
        return new Promise((resolve) => {
            this.mediaIdentified = false;
            if (this.mediaSocket) {
                try {
                    this.mediaSocket.destroy();
                }
                catch { }
            }
            this.mediaSocket = new net.Socket();
            this.mediaSocket.setTimeout(6000);
            this.mediaSocket.connect(this.port, this.host, () => {
                this.mediaConnected = true;
                this.mediaSocket?.setTimeout(0);
                this.mediaSocket?.setNoDelay(true);
                this.mediaSocket?.setKeepAlive(true, 5000);
                this.mediaBuffer = Buffer.alloc(0);
                if (this.mediaReconnectTimer) {
                    clearTimeout(this.mediaReconnectTimer);
                    this.mediaReconnectTimer = null;
                }
                if (this.currentUserId && this.sessionToken) {
                    this.sendSocketPacket(this.mediaSocket, {
                        action: 'identify',
                        user_id: this.currentUserId,
                        session_token: this.sessionToken,
                        channel_type: 'media',
                    });
                }
                resolve(true);
            });
            this.mediaSocket.on('data', (data) => {
                this.mediaBuffer = Buffer.concat([this.mediaBuffer, data]);
                this.processMediaBuffer();
            });
            this.mediaSocket.on('error', (err) => {
                console.warn('[PythonBridge] Media Socket error:', err.message);
                this.mediaConnected = false;
                this.mediaIdentified = false;
                this.scheduleMediaReconnect();
                resolve(false);
            });
            this.mediaSocket.on('close', () => {
                this.mediaConnected = false;
                this.mediaIdentified = false;
                this.scheduleMediaReconnect();
                resolve(false);
            });
            this.mediaSocket.on('timeout', () => {
                if (!this.mediaConnected) {
                    try {
                        this.mediaSocket?.destroy();
                    }
                    catch { }
                    resolve(false);
                }
            });
        });
    }
    scheduleMediaReconnect() {
        if (this.mediaReconnectTimer || !this.currentUserId || !this.sessionToken || !this.dataConnected) {
            return;
        }
        this.mediaReconnectTimer = setTimeout(() => {
            this.mediaReconnectTimer = null;
            if (!this.mediaConnected && this.currentUserId && this.sessionToken && this.dataConnected) {
                this.connectMediaChannel().catch(() => { });
            }
        }, 2500);
    }
    handleDataDisconnect() {
        this.dataConnected = false;
        this.connectingPromise = null;
        this.emitEvent({ type: 'connection_status', connected: false });
        this.scheduleReconnect();
    }
    scheduleReconnect() {
        if (this.reconnectTimer)
            return;
        this.reconnectTimer = setInterval(async () => {
            if (!this.dataConnected) {
                await this.connect();
            }
        }, 2500);
    }
    processDataBuffer() {
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
                const packet = JSON.parse(jsonStr);
                this.handleIncomingPacket(packet);
            }
            catch (e) {
                console.error('[PythonBridge] Failed to parse Data JSON packet:', e);
            }
        }
    }
    processMediaBuffer() {
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
                const packet = JSON.parse(jsonStr);
                if (packet.action === 'identify_response') {
                    this.mediaIdentified = Boolean(packet.success);
                    continue;
                }
                this.handleIncomingPacket(packet);
            }
            catch (e) {
                console.error('[PythonBridge] Failed to parse Media JSON packet:', e);
            }
        }
    }
    handleIncomingPacket(packet) {
        const action = packet.action;
        // 1. Khớp chính xác theo file_id cho download file
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
        // 1.5. Khớp chính xác theo conversation_id cho get_messages
        if (action === 'messages_history' || action === 'get_messages_response' || action === 'get_messages') {
            if (packet.conversation_id !== undefined) {
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
            get_pinned_message: ['get_pinned_message_response', 'get_pinned_message'],
        };
        if (action && this.pendingRequests.has(action)) {
            const req = this.pendingRequests.get(action);
            clearTimeout(req.timeoutId);
            this.pendingRequests.delete(action);
            if (packet.success && packet.user?.id) {
                this.currentUserId = Number(packet.user.id);
                if (packet.session_token || packet.user.session_token) {
                    this.sessionToken = String(packet.session_token || packet.user.session_token);
                }
                this.ensureMediaChannelIdentified();
            }
            req.resolve(packet);
            return;
        }
        for (const [reqAction, req] of this.pendingRequests.entries()) {
            const baseAction = reqAction.replace(/_\d+$/, '');
            const aliases = ACTION_RESPONSE_MAP[baseAction] || ACTION_RESPONSE_MAP[reqAction] || [];
            if (action === `${reqAction}_response` ||
                action === `${baseAction}_response` ||
                action === reqAction ||
                action === baseAction ||
                (action && aliases.includes(action))) {
                clearTimeout(req.timeoutId);
                this.pendingRequests.delete(reqAction);
                if (packet.success && packet.user?.id) {
                    this.currentUserId = Number(packet.user.id);
                    if (packet.session_token || packet.user.session_token) {
                        this.sessionToken = String(packet.session_token || packet.user.session_token);
                    }
                    this.ensureMediaChannelIdentified();
                }
                req.resolve(packet);
                return;
            }
        }
        // Sự kiện push từ server (new_message, call_media_relay, call_incoming, user_status_changed,...)
        this.emitEvent(packet);
    }
    ensureMediaChannelIdentified() {
        if (!this.sessionToken || !this.currentUserId)
            return;
        if (this.mediaSocket && this.mediaConnected && !this.mediaSocket.destroyed) {
            if (!this.mediaIdentified) {
                this.sendSocketPacket(this.mediaSocket, {
                    action: 'identify',
                    user_id: this.currentUserId,
                    session_token: this.sessionToken,
                    channel_type: 'media',
                });
            }
        }
        else {
            this.connectMediaChannel().catch(() => { });
        }
    }
    sendSocketPacket(sock, payload) {
        try {
            if (!sock || sock.destroyed)
                return false;
            const jsonBuffer = Buffer.from(JSON.stringify(payload), 'utf-8');
            const header = Buffer.alloc(4);
            header.writeUInt32BE(jsonBuffer.length, 0);
            sock.write(Buffer.concat([header, jsonBuffer]));
            return true;
        }
        catch {
            return false;
        }
    }
    async sendRequest(action, payload = {}, timeoutMs = 25000) {
        if (!this.dataConnected || !this.dataSocket || this.dataSocket.destroyed) {
            await this.connect();
        }
        if (!this.dataConnected || !this.dataSocket) {
            throw new Error(`Chưa kết nối đến máy chủ (${this.host}:${this.port})! Vui lòng kiểm tra lại địa chỉ máy chủ.`);
        }
        const dataSock = this.dataSocket;
        // Phân loại luồng lưu lượng:
        // Stream call_media -> Kênh 2 (Media Socket)
        // Tín hiệu cuộc gọi (call_invite, call_accept, call_end, check_call_status) -> Kênh 2 nếu đã xác thực xong, ngược lại đi Kênh 1 (Data Socket) đã xác thực
        const isCallMedia = action === 'call_media';
        const isCallTraffic = isCallMedia || action.startsWith('call_') || action === 'check_call_status';
        const mediaSock = this.mediaSocket;
        const canUseMediaForControl = Boolean(mediaSock && this.mediaConnected && this.mediaIdentified && !mediaSock.destroyed);
        const canUseMediaForStream = Boolean(mediaSock && this.mediaConnected && !mediaSock.destroyed);
        const targetSocket = isCallMedia
            ? (canUseMediaForStream && mediaSock ? mediaSock : dataSock)
            : (isCallTraffic && canUseMediaForControl && mediaSock ? mediaSock : dataSock);
        return new Promise((resolve, reject) => {
            const isFileTransfer = action === 'download_file' || action === 'upload_file';
            const actualTimeout = isFileTransfer ? 90000 : (isCallTraffic ? 35000 : timeoutMs);
            let trackingKey = action;
            if (action === 'download_file' && payload.file_id !== undefined) {
                trackingKey = `download_file_${payload.file_id}`;
            }
            else if (action === 'get_messages' && payload.conversation_id !== undefined) {
                trackingKey = `get_messages_${payload.conversation_id}`;
            }
            if (action === 'identify' && payload.user_id && payload.session_token) {
                this.currentUserId = Number(payload.user_id);
                this.sessionToken = String(payload.session_token);
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
                targetSocket.write(Buffer.concat([header, jsonBuffer]));
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
        if (this.mediaReconnectTimer) {
            clearTimeout(this.mediaReconnectTimer);
            this.mediaReconnectTimer = null;
        }
        this.dataConnected = false;
        this.mediaConnected = false;
        this.mediaIdentified = false;
        this.currentUserId = null;
        this.sessionToken = null;
        if (this.dataSocket) {
            try {
                this.dataSocket.destroy();
            }
            catch { }
            this.dataSocket = null;
        }
        if (this.mediaSocket) {
            try {
                this.mediaSocket.destroy();
            }
            catch { }
            this.mediaSocket = null;
        }
    }
    isConnected() {
        return this.dataConnected;
    }
}
exports.PythonBridge = PythonBridge;
