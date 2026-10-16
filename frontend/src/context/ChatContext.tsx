import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { User, Conversation, Message, Friend, ServerEvent, MessageType, ActiveCallState, IncomingCallState } from '../types';
import { apiService } from '../services/api';

interface ChatContextType {
  currentUser: User | null;
  setCurrentUser: (user: User | null) => void;
  conversations: Conversation[];
  activeConv: Conversation | null;
  messages: Message[];
  friends: Friend[];
  pendingFriends: User[];
  sentFriendRequestIds: number[];
  isLocked: boolean;
  setIsLocked: (locked: boolean) => void;
  theme: 'dark' | 'light';
  setTheme: (theme: 'dark' | 'light') => void;
  typingUser: string | null;
  incomingCall: IncomingCallState | null;
  activeCall: ActiveCallState | null;
  pinnedMessage: Message | null;
  replyTo: Message | null;
  setReplyTo: (msg: Message | null) => void;
  selectConversation: (conv: Conversation) => Promise<void>;
  sendMessage: (content: string, type?: MessageType, fileId?: string, origName?: string, fileSize?: number) => Promise<boolean>;
  openSavedMessages: () => Promise<void>;
  refreshConversations: () => Promise<void>;
  refreshFriends: () => Promise<void>;
  toggleReaction: (msgId: number, reaction: string) => Promise<void>;
  pinMessage: (msgId: number) => Promise<void>;
  recallMessage: (msgId: number) => Promise<void>;
  startCall: (type: 'voice' | 'video') => Promise<void>;
  acceptCall: () => Promise<void>;
  rejectCall: () => Promise<void>;
  endCall: () => Promise<void>;
  logout: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('vibe_user') || localStorage.getItem('telegram_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConv, setActiveConv] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [friends, setFriends] = useState<Friend[]>([]);
  const [pendingFriends, setPendingFriends] = useState<User[]>([]);
  const [sentFriendRequestIds, setSentFriendRequestIds] = useState<number[]>([]);
  const [isLocked, setIsLocked] = useState<boolean>(false);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [typingUser, setTypingUser] = useState<string | null>(null);
  const [incomingCall, setIncomingCall] = useState<IncomingCallState | null>(null);
  const [activeCall, setActiveCall] = useState<ActiveCallState | null>(null);
  const [pinnedMessage, setPinnedMessage] = useState<Message | null>(null);
  const [replyTo, setReplyTo] = useState<Message | null>(null);

  // Sync theme to HTML class
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  // Persist session & Auto-identify on socket connection
  useEffect(() => {
    if (currentUser) {
      localStorage.setItem('vibe_user', JSON.stringify(currentUser));
      apiService.sendRequest('identify', { user_id: currentUser.id }).catch(() => {});
    } else {
      localStorage.removeItem('vibe_user');
      localStorage.removeItem('telegram_user');
    }
  }, [currentUser]);

  const refreshConversations = useCallback(async () => {
    if (!currentUser) return;
    const res = await apiService.getConversations(currentUser.id);
    if (res && res.conversations) {
      // Filter out saved messages from regular list (accessed via top button)
      const filtered = res.conversations.filter((c) => c.type !== 'saved');
      setConversations(filtered);
    }
  }, [currentUser]);

  const refreshFriends = useCallback(async () => {
    if (!currentUser) return;
    const res = await apiService.getFriends(currentUser.id);
    if (res) {
      if (res.friends) setFriends(res.friends);
      if (res.pending_requests) setPendingFriends(res.pending_requests);
      if (res.sent_request_ids) setSentFriendRequestIds(res.sent_request_ids);
    }
  }, [currentUser]);

  const selectConversation = async (conv: Conversation) => {
    setActiveConv(conv);
    setReplyTo(null);
    setTypingUser(null);

    // Fetch messages
    const res = await apiService.getMessages(conv.id);
    if (res && res.messages) {
      setMessages(res.messages);
    } else {
      setMessages([]);
    }

    // Fetch pinned message
    const pRes = await apiService.getPinnedMessage(conv.id);
    if (pRes && pRes.pinned) {
      setPinnedMessage(pRes.pinned);
    } else {
      setPinnedMessage(null);
    }
  };

  const openSavedMessages = async () => {
    if (!currentUser) return;
    const res = await apiService.getSavedConversation(currentUser.id);
    if (res && res.conversation_id) {
      const savedConv: Conversation = {
        id: res.conversation_id,
        title: 'Cloud của tôi (Saved Messages)',
        type: 'saved',
        avatar_color: '#4F46E5',
      };
      await selectConversation(savedConv);
    }
  };

  const sendMessage = async (content: string, type: MessageType = 'text', fileId?: string, origName?: string, fileSize?: number) => {
    if (!activeConv || !currentUser) return false;
    const res = await apiService.sendMessage({
      conversation_id: activeConv.id,
      sender_id: currentUser.id,
      content,
      msg_type: type,
      file_id: fileId,
      original_name: origName,
      file_size: fileSize,
      reply_to_id: replyTo ? replyTo.id : null,
      reply_preview: replyTo ? `${replyTo.sender_name}: ${replyTo.content.slice(0, 40)}` : null,
    });

    if (res && res.success && res.message) {
      setMessages((prev) => [...prev, res.message!]);
      setReplyTo(null);
      refreshConversations();
      return true;
    }
    return false;
  };

  const toggleReaction = async (msgId: number, reaction: string) => {
    if (!currentUser) return;
    await apiService.toggleReaction(msgId, currentUser.id, reaction);
  };

  const pinMessage = async (msgId: number) => {
    if (!activeConv) return;
    await apiService.pinMessage(activeConv.id, msgId);
    const target = messages.find((m) => m.id === msgId);
    if (target) setPinnedMessage(target);
  };

  const recallMessage = async (msgId: number) => {
    if (!currentUser) return;
    await apiService.recallMessage(msgId, currentUser.id);
    setMessages((prev) =>
      prev.map((m) => (m.id === msgId ? { ...m, is_deleted: 1, content: 'Tin nhắn đã được thu hồi' } : m))
    );
  };

  const startCall = async (callType: 'voice' | 'video') => {
    if (!activeConv || !currentUser) return;
    const rawPartnerId =
      activeConv.partner_id ||
      (typeof activeConv.id === 'string' && activeConv.id.startsWith('direct_')
        ? Number(activeConv.id.replace('direct_', ''))
        : undefined);
    if (!rawPartnerId) return;
    const partnerId = Number(rawPartnerId);

    // Immediately show outgoing ringing screen
    setActiveCall({
      partnerId,
      partnerName: activeConv.title,
      callType,
      isOutgoing: true,
      isConnected: false,
    });

    const res = await apiService.sendRequest('call_invite', {
      caller_id: Number(currentUser.id),
      receiver_id: partnerId,
      call_type: callType,
      conversation_id: activeConv.id,
    });

    if (res && res.channel_id) {
      setActiveCall((prev) => (prev ? { ...prev, channelId: res.channel_id } : null));
    } else if (res && res.success === false) {
      alert(res.message || 'Không thể thực hiện cuộc gọi vào lúc này.');
      setActiveCall(null);
    }
  };

  const acceptCall = async () => {
    if (!incomingCall || !currentUser) return;
    const channelId = incomingCall.channelId;
    setActiveCall({
      partnerId: incomingCall.callerId,
      partnerName: incomingCall.callerName,
      callType: incomingCall.callType,
      channelId,
      isOutgoing: false,
      isConnected: true,
    });
    setIncomingCall(null);
    await apiService.sendRequest('call_accept', {
      channel_id: channelId,
    });
  };

  const rejectCall = async () => {
    if (!incomingCall) return;
    await apiService.sendRequest('call_reject', {
      channel_id: incomingCall.channelId,
    });
    setIncomingCall(null);
  };

  const endCall = async () => {
    if (!activeCall) return;
    if (activeCall.channelId) {
      await apiService.sendRequest('call_end', {
        channel_id: activeCall.channelId,
      });
    }
    setActiveCall(null);
  };

  const logout = () => {
    setCurrentUser(null);
    setActiveConv(null);
    setMessages([]);
    setConversations([]);
    setFriends([]);
    localStorage.removeItem('vibe_user');
    localStorage.removeItem('telegram_user');
  };

  // Listen to real-time events from Python Server
  useEffect(() => {
    const unsubscribe = apiService.onServerEvent((event: ServerEvent) => {
      switch (event.type) {
        case 'new_message':
          if (event.message) {
            const newMsg = event.message;
            if (activeConv && String(activeConv.id) === String(newMsg.conversation_id)) {
              setMessages((prev) => {
                if (prev.some((m) => m.id === newMsg.id)) return prev;
                return [...prev, newMsg];
              });
            }
            refreshConversations();
          }
          break;

        case 'message_recalled':
          if (event.msg_id) {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === event.msg_id ? { ...m, is_deleted: 1, content: 'Tin nhắn đã được thu hồi' } : m
              )
            );
          }
          break;

        case 'reaction_updated':
          if (event.msg_id && event.data?.reactions) {
            setMessages((prev) =>
              prev.map((m) => (m.id === event.msg_id ? { ...m, reactions: event.data.reactions } : m))
            );
          }
          break;

        case 'pinned_updated':
          if (activeConv && String(activeConv.id) === String(event.conv_id)) {
            setPinnedMessage(event.data?.pinned || null);
          }
          break;

        case 'user_typing':
          if (activeConv && String(activeConv.id) === String(event.conv_id)) {
            const senderName = event.data?.sender_name || 'Đối phương';
            setTypingUser(senderName);
            setTimeout(() => setTypingUser(null), 3000);
          }
          break;

        case 'call_incoming':
          if (event.caller_id && event.channel_id) {
            setIncomingCall({
              channelId: event.channel_id,
              callerId: event.caller_id,
              callerName: event.caller_name || 'Người dùng',
              callType: event.call_type || 'voice',
            });
          }
          break;

        case 'call_connected':
          setActiveCall((prev) => (prev ? { ...prev, isConnected: true, channelId: event.channel_id || prev.channelId } : null));
          break;

        case 'call_rejected':
          setActiveCall(null);
          setIncomingCall(null);
          break;

        case 'call_ended':
          setActiveCall(null);
          setIncomingCall(null);
          break;

        case 'user_status_changed':
          if (event.user_id && activeConv && activeConv.type === 'direct' && activeConv.partner_id === event.user_id) {
            setActiveConv((prev) => prev ? { ...prev, is_online: Boolean(event.is_online) } : null);
          }
          refreshConversations();
          refreshFriends();
          break;

        case 'new_friend_request':
        case 'refresh_friends':
          refreshFriends();
          break;

        case 'profile_updated':
          if (event.user) {
            const u = event.user;
            if (currentUser && currentUser.id === u.id) {
              setCurrentUser((prev) => (prev ? { ...prev, ...u } : u));
              localStorage.setItem('vibe_user', JSON.stringify({ ...currentUser, ...u }));
            }
            if (activeConv && activeConv.type === 'direct' && activeConv.partner_id === u.id) {
              setActiveConv((prev) =>
                prev
                  ? {
                      ...prev,
                      title: u.full_name || prev.title,
                      avatar_color: u.avatar_color || prev.avatar_color,
                      avatar_url: u.avatar_url,
                      partner_username: u.username || prev.partner_username,
                      phone_number: u.phone_number,
                      is_phone_verified: u.is_phone_verified,
                    }
                  : null
              );
            }
            refreshConversations();
            refreshFriends();
          }
          break;

        case 'refresh_conversations':
          refreshConversations();
          break;
      }
    });

    return () => {
      unsubscribe();
    };
  }, [activeConv, refreshConversations, refreshFriends]);

  // Initial load
  useEffect(() => {
    if (currentUser) {
      refreshConversations();
      refreshFriends();
    }
  }, [currentUser, refreshConversations, refreshFriends]);

  return (
    <ChatContext.Provider
      value={{
        currentUser,
        setCurrentUser,
        conversations,
        activeConv,
        messages,
        friends,
        pendingFriends,
        sentFriendRequestIds,
        isLocked,
        setIsLocked,
        theme,
        setTheme,
        typingUser,
        incomingCall,
        activeCall,
        pinnedMessage,
        replyTo,
        setReplyTo,
        selectConversation,
        sendMessage,
        openSavedMessages,
        refreshConversations,
        refreshFriends,
        toggleReaction,
        pinMessage,
        recallMessage,
        startCall,
        acceptCall,
        rejectCall,
        endCall,
        logout,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};
