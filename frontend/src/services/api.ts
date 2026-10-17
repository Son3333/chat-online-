import { User, Conversation, Message, Friend, CallPacket, ServerEvent } from '../types';

declare global {
  interface Window {
    api?: {
      sendRequest: (action: string, payload?: Record<string, any>) => Promise<any>;
      onServerEvent: (callback: (event: any) => void) => () => void;
      minimizeWindow: () => void;
      maximizeWindow: () => void;
      closeWindow: () => void;
      setAlwaysOnTop: (enabled: boolean) => Promise<boolean>;
      isAlwaysOnTop: () => Promise<boolean>;
      selectLocalFile: () => Promise<{ canceled: boolean; fileName?: string; fileData?: string; fileSize?: number }>;
      saveDownloadedFile: (fileName: string, base64Data: string) => Promise<{ success: boolean; path?: string }>;
      onUpdateAvailable: (callback: (updateInfo: { remoteHash: string; localHash: string; message: string }) => void) => () => void;
      applyUpdate: () => Promise<{ success: boolean; error?: string }>;
      checkUpdateNow: () => Promise<any>;
      getServerInfo?: () => Promise<{ isWan: boolean; address: string; host?: string; port?: number }>;
      getServerConfig?: () => Promise<{ host: string; port: number; isWan: boolean }>;
      setServerConfig?: (config: { host: string; port: number }) => Promise<{ host: string; port: number; isWan: boolean; connected: boolean }>;
      openExternal?: (url: string) => Promise<boolean>;
    };
  }
}

// Fallback in-memory mock for web testing when running directly in browser without Electron
const isElectron = typeof window !== 'undefined' && Boolean(window.api);
const imageCache = new Map<string, string>();
const inFlightImageRequests = new Map<string, Promise<string | null>>();

export const apiService = {
  isElectron,

  async sendRequest(action: string, payload: Record<string, any> = {}): Promise<any> {
    if (window.api) {
      return await window.api.sendRequest(action, payload);
    }
    console.warn(`[API] Not running in Electron, mocking action '${action}'`, payload);
    return { success: true };
  },

  onServerEvent(callback: (event: ServerEvent) => void): () => void {
    if (window.api) {
      return window.api.onServerEvent(callback);
    }
    return () => {};
  },

  async getServerInfo(): Promise<{ isWan: boolean; address: string; host?: string; port?: number }> {
    if (window.api?.getServerInfo) {
      return await window.api.getServerInfo();
    }
    return { isWan: false, address: '127.0.0.1:8888', host: '127.0.0.1', port: 8888 };
  },

  async getServerConfig(): Promise<{ host: string; port: number; isWan: boolean }> {
    if (window.api?.getServerConfig) {
      return await window.api.getServerConfig();
    }
    return { host: '127.0.0.1', port: 8888, isWan: false };
  },

  async setServerConfig(host: string, port: number): Promise<{ host: string; port: number; isWan: boolean; connected: boolean }> {
    if (window.api?.setServerConfig) {
      return await window.api.setServerConfig({ host, port });
    }
    return { host, port, isWan: false, connected: true };
  },

  // Auth
  async login(username: string, password: string): Promise<{ success: boolean; user?: User; error?: string }> {
    const cleanUsername = username.trim().toLowerCase().replace(/^@+/, '');
    return await this.sendRequest('login', { username: cleanUsername, password });
  },

  async register(username: string, password: string, full_name: string): Promise<{ success: boolean; user?: User; error?: string }> {
    const cleanUsername = username.trim().toLowerCase().replace(/^@+/, '');
    return await this.sendRequest('register', { username: cleanUsername, password, full_name: full_name.trim() });
  },

  async updateProfile(userId: number, data: {
    full_name?: string;
    avatar_color?: string;
    avatar_url?: string;
    phone_number?: string;
    is_phone_verified?: number | boolean;
    new_password?: string;
    pin_code?: string;
  }): Promise<{ success: boolean; user?: User; error?: string }> {
    return await this.sendRequest('update_profile', { user_id: userId, ...data });
  },

  async requestPhoneOtp(userId: number, phoneNumber: string): Promise<{ success: boolean; otp_code?: string; error?: string; message?: string }> {
    return await this.sendRequest('request_phone_otp', { user_id: userId, phone_number: phoneNumber });
  },

  async verifyPhoneOtp(userId: number, phoneNumber: string, otpCode: string): Promise<{ success: boolean; user?: User; error?: string; message?: string }> {
    return await this.sendRequest('verify_phone_otp', { user_id: userId, phone_number: phoneNumber, otp_code: otpCode });
  },

  // Conversations
  async getConversations(userId: number): Promise<{ success: boolean; conversations: Conversation[] }> {
    const res = await this.sendRequest('get_conversations', { user_id: userId });
    const rawList: any[] = res?.conversations || [];
    const normalized: Conversation[] = rawList.map((c: any) => ({
      ...c,
      id: c.id,
      title: c.title || c.name || 'Cuộc trò chuyện',
      type: c.type || 'direct',
      last_message: c.last_message
        ? {
            ...c.last_message,
            msg_type: c.last_message.msg_type || c.last_message.message_type || 'text',
          }
        : null,
    }));
    return {
      success: res?.success !== false,
      conversations: normalized,
    };
  },

  async getSavedConversation(userId: number): Promise<{ success: boolean; conversation_id: number }> {
    return await this.sendRequest('get_saved_conversation', { user_id: userId });
  },

  async getMessages(convId: string | number, limit = 60): Promise<{ success: boolean; messages: Message[] }> {
    const res = await this.sendRequest('get_messages', { conversation_id: convId, limit });
    const rawMessages: any[] = res?.messages || [];
    const normalized: Message[] = rawMessages.map((m: any) => ({
      ...m,
      msg_type: m.msg_type || m.message_type || 'text',
      original_name: m.original_name || m.file_name,
    }));
    return {
      success: res?.success !== false,
      messages: normalized,
    };
  },

  async sendMessage(params: {
    conversation_id: string | number;
    sender_id: number;
    content: string;
    msg_type?: 'text' | 'image' | 'video' | 'file' | 'location';
    file_id?: string | null;
    original_name?: string;
    file_size?: number;
    reply_to_id?: number | null;
    reply_preview?: string | null;
  }): Promise<{ success: boolean; message?: Message; error?: string }> {
    return await this.sendRequest('send_message', {
      ...params,
      message_type: params.msg_type,
      msg_type: params.msg_type,
    });
  },

  async recallMessage(messageId: number, userId: number): Promise<{ success: boolean; error?: string }> {
    return await this.sendRequest('recall_message', { message_id: messageId, user_id: userId });
  },

  async toggleReaction(messageId: number, userId: number, reaction: string): Promise<{ success: boolean }> {
    return await this.sendRequest('toggle_reaction', { message_id: messageId, user_id: userId, reaction });
  },

  async pinMessage(convId: string | number, messageId: number): Promise<{ success: boolean }> {
    return await this.sendRequest('pin_message', { conversation_id: convId, message_id: messageId });
  },

  async unpinMessage(convId: string | number): Promise<{ success: boolean }> {
    return await this.sendRequest('unpin_message', { conversation_id: convId });
  },

  async getPinnedMessage(convId: string | number): Promise<{ success: boolean; pinned?: Message | null }> {
    return await this.sendRequest('get_pinned_message', { conversation_id: convId });
  },

  // Files
  async uploadFile(
    originalName: string,
    fileData: string,
    fileSize: number,
    fileType: string,
    conversationId?: string | number,
    senderId?: number
  ): Promise<{ success: boolean; file_id?: string; error?: string }> {
    return await this.sendRequest('upload_file', {
      original_name: originalName,
      filename: originalName,
      file_data: fileData,
      file_size: fileSize,
      file_type: fileType,
      conversation_id: conversationId,
      sender_id: senderId,
    });
  },

  async downloadFile(fileId: string | number): Promise<{ success: boolean; file_data?: string; original_name?: string; filename?: string; file_type?: string }> {
    return await this.sendRequest('download_file', { file_id: fileId });
  },

  cacheImage(fileId: string | number, dataUrl: string) {
    imageCache.set(String(fileId), dataUrl);
  },

  async getImageUrl(fileId: string | number): Promise<string | null> {
    if (!fileId) return null;
    const key = String(fileId);
    if (imageCache.has(key)) {
      return imageCache.get(key)!;
    }
    if (inFlightImageRequests.has(key)) {
      return inFlightImageRequests.get(key)!;
    }

    const promise = (async () => {
      try {
        const res = await this.downloadFile(key);
        if (res && res.file_data) {
          let mime = res.file_type || 'image/png';
          if (!mime.startsWith('image/')) {
            const fn = (res.filename || res.original_name || '').toLowerCase();
            if (fn.endsWith('.jpg') || fn.endsWith('.jpeg')) mime = 'image/jpeg';
            else if (fn.endsWith('.gif')) mime = 'image/gif';
            else if (fn.endsWith('.webp')) mime = 'image/webp';
            else mime = 'image/png';
          }
          const dataUrl = `data:${mime};base64,${res.file_data}`;
          imageCache.set(key, dataUrl);
          return dataUrl;
        }
      } catch (err) {
        console.error('[API] Error loading image thumbnail:', err);
      } finally {
        inFlightImageRequests.delete(key);
      }
      return null;
    })();

    inFlightImageRequests.set(key, promise);
    return promise;
  },

  // Contacts
  async searchUsers(query: string, currentUserId?: number): Promise<{ success: boolean; users: User[] }> {
    const res = await this.sendRequest('search_users', { keyword: query, query, user_id: currentUserId });
    return {
      success: res?.success !== false,
      users: res?.users || [],
    };
  },

  async getFriends(userId: number): Promise<{ success: boolean; friends: Friend[]; pending_requests?: User[]; sent_request_ids?: number[] }> {
    return await this.sendRequest('get_friends', { user_id: userId });
  },

  async sendFriendRequest(senderId: number, targetId: number): Promise<{ success: boolean; message?: string; error?: string }> {
    return await this.sendRequest('add_friend', { user_id: senderId, friend_id: targetId, sender_id: senderId, target_id: targetId });
  },

  async acceptFriendRequest(userId: number, requesterId: number): Promise<{ success: boolean; message?: string; error?: string }> {
    return await this.sendRequest('accept_friend', { user_id: userId, requester_id: requesterId });
  },

  async rejectFriendRequest(userId: number, requesterId: number): Promise<{ success: boolean; message?: string; error?: string }> {
    return await this.sendRequest('reject_friend', { user_id: userId, requester_id: requesterId });
  },

  async removeFriend(userId: number, friendId: number): Promise<{ success: boolean; message?: string }> {
    return await this.sendRequest('remove_friend', { user_id: userId, friend_id: friendId });
  },

  async blockUser(userId: number, targetId: number): Promise<{ success: boolean }> {
    return await this.sendRequest('block_user', { user_id: userId, target_id: targetId });
  },

  async unblockUser(userId: number, targetId: number): Promise<{ success: boolean }> {
    return await this.sendRequest('unblock_user', { user_id: userId, target_id: targetId });
  },

  async deleteConversation(convId: string | number, userId: number): Promise<{ success: boolean; message?: string }> {
    return await this.sendRequest('delete_conversation', { conversation_id: convId, user_id: userId });
  },

  // Groups
  async createGroup(title: string, creatorId: number, memberIds: number[]): Promise<{ success: boolean; conversation_id?: number }> {
    return await this.sendRequest('create_group', { title, creator_id: creatorId, member_ids: memberIds });
  },

  // Typing & Call
  sendTyping(convId: string | number, userId: number, fullName: string) {
    this.sendRequest('typing', { conversation_id: convId, user_id: userId, full_name: fullName }).catch(() => {});
  },

  async sendCallPacket(packet: CallPacket): Promise<{ success: boolean }> {
    return await this.sendRequest(packet.action, packet);
  },

  // Window Controls
  minimizeWindow() {
    window.api?.minimizeWindow();
  },
  maximizeWindow() {
    window.api?.maximizeWindow();
  },
  closeWindow() {
    window.api?.closeWindow();
  },
  async setAlwaysOnTop(enabled: boolean): Promise<boolean> {
    if (window.api) {
      return await window.api.setAlwaysOnTop(enabled);
    }
    return false;
  },
  async isAlwaysOnTop(): Promise<boolean> {
    if (window.api) {
      return await window.api.isAlwaysOnTop();
    }
    return false;
  },
  async selectLocalFile() {
    if (window.api) {
      return await window.api.selectLocalFile();
    }
    return { canceled: true };
  },
  async saveDownloadedFile(fileName: string, base64Data: string) {
    if (window.api) {
      return await window.api.saveDownloadedFile(fileName, base64Data);
    }
    return { success: false };
  },

  // Git Auto-Updater
  onUpdateAvailable(callback: (info: { remoteHash: string; localHash: string; message: string }) => void): () => void {
    if (window.api?.onUpdateAvailable) {
      return window.api.onUpdateAvailable(callback);
    }
    return () => {};
  },

  async applyUpdate(): Promise<{ success: boolean; error?: string }> {
    if (window.api?.applyUpdate) {
      return await window.api.applyUpdate();
    }
    return { success: false, error: 'Chức năng cập nhật chỉ hỗ trợ khi chạy ứng dụng Desktop!' };
  },

  async checkUpdateNow() {
    if (window.api?.checkUpdateNow) {
      return await window.api.checkUpdateNow();
    }
  },

  async openExternal(url: string): Promise<boolean> {
    if (window.api?.openExternal) {
      try {
        return await window.api.openExternal(url);
      } catch (err) {
        console.warn('[API] openExternal IPC error:', err);
      }
    }
    window.open(url, '_blank');
    return true;
  },
};

