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
    };
  }
}

// Fallback in-memory mock for web testing when running directly in browser without Electron
const isElectron = typeof window !== 'undefined' && Boolean(window.api);

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

  // Auth
  async login(username: string, password: string): Promise<{ success: boolean; user?: User; error?: string }> {
    return await this.sendRequest('login', { username, password });
  },

  async register(username: string, password: string, full_name: string): Promise<{ success: boolean; user?: User; error?: string }> {
    return await this.sendRequest('register', { username, password, full_name });
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
    msg_type?: 'text' | 'image' | 'file';
    file_id?: string | null;
    original_name?: string;
    file_size?: number;
    reply_to_id?: number | null;
    reply_preview?: string | null;
  }): Promise<{ success: boolean; message?: Message; error?: string }> {
    return await this.sendRequest('send_message', params);
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

  async getPinnedMessage(convId: string | number): Promise<{ success: boolean; pinned?: Message | null }> {
    return await this.sendRequest('get_pinned_message', { conversation_id: convId });
  },

  // Files
  async uploadFile(originalName: string, fileData: string, fileSize: number, fileType: string): Promise<{ success: boolean; file_id?: string }> {
    return await this.sendRequest('upload_file', {
      original_name: originalName,
      file_data: fileData,
      file_size: fileSize,
      file_type: fileType,
    });
  },

  async downloadFile(fileId: string): Promise<{ success: boolean; file_data?: string; original_name?: string }> {
    return await this.sendRequest('download_file', { file_id: fileId });
  },

  // Contacts
  async searchUsers(query: string, currentUserId?: number): Promise<{ success: boolean; users: User[] }> {
    const res = await this.sendRequest('search_users', { keyword: query, query, user_id: currentUserId });
    return {
      success: res?.success !== false,
      users: res?.users || [],
    };
  },

  async getFriends(userId: number): Promise<{ success: boolean; friends: Friend[] }> {
    return await this.sendRequest('get_friends', { user_id: userId });
  },

  async sendFriendRequest(senderId: number, targetId: number): Promise<{ success: boolean; error?: string }> {
    return await this.sendRequest('send_friend_request', { sender_id: senderId, target_id: targetId });
  },

  async blockUser(userId: number, targetId: number): Promise<{ success: boolean }> {
    return await this.sendRequest('block_user', { user_id: userId, target_id: targetId });
  },

  async unblockUser(userId: number, targetId: number): Promise<{ success: boolean }> {
    return await this.sendRequest('unblock_user', { user_id: userId, target_id: targetId });
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
};

