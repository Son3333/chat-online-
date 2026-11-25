import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback, useRef } from 'react';
import { User, Conversation, Message, Friend, ServerEvent, MessageType, ActiveCallState, IncomingCallState } from '../types';
import { apiService } from '../services/api';

interface ChatContextType {
  currentUser: User | null;
  setCurrentUser: (user: User | null) => void;
  conversations: Conversation[];
  activeConv: Conversation | null;
  setActiveConv: (conv: Conversation | null) => void;
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  friends: Friend[];
  pendingFriends: User[];
  sentFriendRequestIds: number[];
  isLocked: boolean;
  setIsLocked: (locked: boolean) => void;
  theme: 'dark' | 'light';
  setTheme: (theme: 'dark' | 'light') => void;
  typingUser: string | null;
  repositioningImage: string | null;
  setRepositioningImage: (img: string | null) => void;
  isSidebarCollapsed: boolean;
  setIsSidebarCollapsed: React.Dispatch<React.SetStateAction<boolean>>;
  incomingCall: IncomingCallState | null;
  activeCall: ActiveCallState | null;
  loadingMessages: boolean;
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
  unpinMessage: () => Promise<void>;
  recallMessage: (msgId: number) => Promise<void>;
  startCall: (type: 'voice' | 'video', targetPartnerId?: number, targetPartnerName?: string) => Promise<void>;
  acceptCall: () => Promise<void>;
  rejectCall: () => Promise<void>;
  endCall: () => Promise<void>;
  logout: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

// Helper: Web Audio API sound for new message notification (Telegram/Messenger style pleasant double chime)
function playMessageNotificationSound() {
  if (localStorage.getItem('vibe_notification_sound') === 'false') return;
  try {
    const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    
    // First gentle chime (F#5: 739.99 Hz)
    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();
    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(740, ctx.currentTime);
    gain1.gain.setValueAtTime(0.12, ctx.currentTime);
    gain1.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.12);
    osc1.connect(gain1);
    gain1.connect(ctx.destination);
    osc1.start(ctx.currentTime);
    osc1.stop(ctx.currentTime + 0.12);

    // Second higher crisp chime (A5: 880 Hz)
    const osc2 = ctx.createOscillator();
    const gain2 = ctx.createGain();
    osc2.type = 'sine';
    osc2.frequency.setValueAtTime(880, ctx.currentTime + 0.08);
    gain2.gain.setValueAtTime(0.15, ctx.currentTime + 0.08);
    gain2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35);
    osc2.connect(gain2);
    gain2.connect(ctx.destination);
    osc2.start(ctx.currentTime + 0.08);
    osc2.stop(ctx.currentTime + 0.35);
  } catch {
    // Ignore audio context block if user has not interacted with DOM yet
  }
}

// Helper: Desktop notification popup for incoming messages
function triggerDesktopNotification(senderName: string, content: string) {
  try {
    if (!('Notification' in window)) return;
    if (Notification.permission === 'granted') {
      const notif = new Notification(senderName || 'Tin nhắn mới', {
        body: content || 'Đã gửi một tệp đính kèm',
        icon: '/app.ico',
        silent: true,
      });
      notif.onclick = () => {
        window.focus();
      };
    } else if (Notification.permission === 'default') {
      Notification.requestPermission().then((perm) => {
        if (perm === 'granted') {
          new Notification(senderName || 'Tin nhắn mới', {
            body: content || 'Đã gửi một tệp đính kèm',
            icon: '/app.ico',
            silent: true,
          });
        }
      });
    }
  } catch {
    // Notification not supported or blocked
  }
}

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('vibe_user') || localStorage.getItem('telegram_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConv, setActiveConv] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingMessages, setLoadingMessages] = useState<boolean>(false);
  const [friends, setFriends] = useState<Friend[]>([]);
  const [pendingFriends, setPendingFriends] = useState<User[]>([]);
  const [sentFriendRequestIds, setSentFriendRequestIds] = useState<number[]>([]);
  const [isLocked, setIsLocked] = useState<boolean>(false);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [typingUser, setTypingUser] = useState<string | null>(null);
  const [repositioningImage, setRepositioningImage] = useState<string | null>(null);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(() => {
    return typeof window !== 'undefined' ? window.innerWidth < 980 : false;
  });

  // Responsive layout: auto adapt when window is resized to compact width
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 980) {
        if (activeConvIdRef.current) {
          setIsSidebarCollapsed(true);
        } else {
          setIsSidebarCollapsed(false);
        }
      } else {
        setIsSidebarCollapsed(false);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  const [incomingCall, setIncomingCall] = useState<IncomingCallState | null>(null);
  const [activeCall, setActiveCall] = useState<ActiveCallState | null>(null);
  const [pinnedMessage, setPinnedMessage] = useState<Message | null>(null);
  const [replyTo, setReplyTo] = useState<Message | null>(null);
  const activeConvIdRef = useRef<string | number | null>(null);

  // Sync theme to HTML class
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  useEffect(() => {
    let cancelled = false;
    if (currentUser) {
      if (!currentUser.session_token) {
        localStorage.removeItem('vibe_user');
        setCurrentUser(null);
        return;
      }
      localStorage.setItem('vibe_user', JSON.stringify(currentUser));
      apiService
        .sendRequest('identify', {
          user_id: currentUser.id,
          session_token: currentUser.session_token,
        })
        .then((res) => {
          if (cancelled) return;
          if (!res || !res.success) {
            localStorage.removeItem('vibe_user');
            setCurrentUser(null);
            return;
          }
          apiService.getConversations(currentUser.id).then((cRes) => {
            if (!cancelled && cRes?.conversations) {
              setConversations(cRes.conversations.filter((c) => c.type !== 'saved'));
            }
          }).catch(() => {});
          apiService.getFriends(currentUser.id).then((fRes) => {
            if (!cancelled && fRes) {
              if (fRes.friends) setFriends(fRes.friends);
              if (fRes.pending_requests) setPendingFriends(fRes.pending_requests);
              if (fRes.sent_request_ids) setSentFriendRequestIds(fRes.sent_request_ids);
            }
          }).catch(() => {});
        })
        .catch(() => {});
    } else {
      localStorage.removeItem('vibe_user');
      localStorage.removeItem('telegram_user');
    }
    return () => {
      cancelled = true;
    };
  }, [currentUser]);

  // Request notification permission once if not determined
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission().catch(() => {});
    }
  }, []);

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
    activeConvIdRef.current = conv.id;
    setActiveConv(conv);
    if (typeof window !== 'undefined' && window.innerWidth < 980) {
      setIsSidebarCollapsed(true);
    }
    setLoadingMessages(true);
    setMessages([]);
    setReplyTo(null);
    setTypingUser(null);
    setPinnedMessage(null);

    const targetConvId = conv.id;

    // Fetch messages with safe fallback
    try {
      const res = await apiService.getMessages(targetConvId);
      // Chỉ gán messages nếu người dùng vẫn đang ở đúng hội thoại này
      if (String(activeConvIdRef.current) === String(targetConvId)) {
        if (res && res.messages && res.messages.length > 0) {
          const filtered = res.messages.filter(
            (m: any) => !m.conversation_id || String(m.conversation_id) === String(targetConvId)
          );
          setMessages(filtered.length > 0 ? filtered : res.messages);
        } else {
          setMessages([]);
        }
      }
    } catch (err) {
      console.warn('[ChatContext] Error loading messages:', err);
    } finally {
      if (String(activeConvIdRef.current) === String(targetConvId)) {
        setLoadingMessages(false);
      }
    }

    // Fetch pinned message with safe fallback
    try {
      const pRes = await apiService.getPinnedMessage(targetConvId);
      if (String(activeConvIdRef.current) === String(targetConvId)) {
        if (pRes && pRes.pinned) {
          setPinnedMessage(pRes.pinned);
        } else {
          setPinnedMessage(null);
        }
      }
    } catch {
      if (String(activeConvIdRef.current) === String(targetConvId)) {
        setPinnedMessage(null);
      }
    }
  };

  const openSavedMessages = async () => {
    if (!currentUser) return;
    if (typeof window !== 'undefined' && window.innerWidth < 980) {
      setIsSidebarCollapsed(true);
    }
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

  const normalizeMessage = (m: any): Message => ({
    ...m,
    msg_type: m.msg_type || m.message_type || 'text',
    original_name: m.original_name || m.file_name,
  });

  const sendMessage = async (content: string, type: MessageType = 'text', fileId?: string, origName?: string, fileSize?: number) => {
    if (!activeConv || !currentUser) return false;
    const targetConvId = activeConv.id;
    const res = await apiService.sendMessage({
      conversation_id: targetConvId,
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
      const norm = normalizeMessage(res.message);
      // Chỉ thêm tin nhắn nếu người dùng vẫn đang ở hội thoại đó
      if (String(norm.conversation_id) === String(activeConvIdRef.current)) {
        setMessages((prev) => {
          if (prev.some((m) => m.id === norm.id)) return prev;
          return [...prev, norm];
        });
      }
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
    if (pinnedMessage && pinnedMessage.id === msgId) {
      await apiService.unpinMessage(activeConv.id);
      setPinnedMessage(null);
      setMessages((prev) => prev.map((m) => (m.id === msgId ? { ...m, is_pinned: 0 } : m)));
      return;
    }
    await apiService.pinMessage(activeConv.id, msgId);
    const target = messages.find((m) => m.id === msgId);
    if (target) {
      const pinnedObj = { ...target, is_pinned: 1 };
      setPinnedMessage(pinnedObj);
      setMessages((prev) => prev.map((m) => (m.id === msgId ? { ...m, is_pinned: 1 } : { ...m, is_pinned: 0 })));
    }
  };

  const unpinMessage = async () => {
    if (!activeConv) return;
    await apiService.unpinMessage(activeConv.id);
    setPinnedMessage(null);
    setMessages((prev) => prev.map((m) => ({ ...m, is_pinned: 0 })));
  };

  const recallMessage = async (msgId: number) => {
    if (!currentUser) return;
    await apiService.recallMessage(msgId, currentUser.id);
    setMessages((prev) =>
      prev.map((m) => (m.id === msgId ? { ...m, is_deleted: 1, content: 'Tin nhắn đã được thu hồi' } : m))
    );
  };

  const startCall = async (callType: 'voice' | 'video', targetPartnerId?: number, targetPartnerName?: string) => {
    if (!currentUser) return;
    const rawPartnerId =
      targetPartnerId ||
      activeConv?.partner_id ||
      (typeof activeConv?.id === 'string' && activeConv.id.startsWith('direct_')
        ? Number(activeConv.id.replace('direct_', ''))
        : undefined);
    if (!rawPartnerId) {
      console.warn('[Call] No partner id found to start call');
      return;
    }
    const partnerId = Number(rawPartnerId);
    const partnerName = targetPartnerName || activeConv?.title || 'Đối phương';
    const convId = activeConv?.id || `direct_${partnerId}`;

    // Immediately show outgoing ringing screen
    setActiveCall({
      partnerId,
      partnerName,
      callType,
      isOutgoing: true,
      isConnected: false,
    });

    try {
      const res = await apiService.sendRequest('call_invite', {
        caller_id: Number(currentUser.id),
        receiver_id: partnerId,
        call_type: callType,
        conversation_id: convId,
      });

      if (res && res.channel_id) {
        setActiveCall((prev) => (prev ? { ...prev, channelId: res.channel_id } : null));
      } else {
        setActiveCall(null);
      }
    } catch (err: any) {
      console.warn('[Call] Error sending call_invite:', err);
      setActiveCall(null);
    }
  };

  const acceptCall = async () => {
    if (!incomingCall || !currentUser) return;
    const channelId = incomingCall.channelId;
    const callerId = incomingCall.callerId;
    const callerName = incomingCall.callerName;
    setActiveCall({
      partnerId: callerId,
      partnerName: callerName,
      callType: incomingCall.callType,
      channelId,
      isOutgoing: false,
      isConnected: true,
    });
    setIncomingCall(null);

    // Tu dong mo cuoc tro chuyen voi nguoi dang goi de ca 2 dong bo tin nhan
    if (!activeConv || activeConv.partner_id !== callerId) {
      const existing = conversations.find((c) => c.partner_id === callerId && c.type === 'direct');
      if (existing) {
        selectConversation(existing);
      } else {
        apiService.sendRequest('start_direct_chat', {
          user_id: currentUser.id,
          target_id: callerId,
        }).then((res) => {
          if (res && res.conversation_id) {
            selectConversation({
              id: res.conversation_id,
              title: callerName,
              type: 'direct',
              partner_id: callerId,
            });
          }
        }).catch(() => {});
      }
    }

    try {
      await apiService.sendRequest('call_accept', {
        channel_id: channelId,
      });
    } catch (err) {
      console.warn('[Call] Error sending call_accept:', err);
    }
  };

  const rejectCall = async () => {
    if (!incomingCall) return;
    try {
      await apiService.sendRequest('call_reject', {
        channel_id: incomingCall.channelId,
      });
    } catch (err) {
      console.warn('[Call] Error sending call_reject:', err);
    }
    setIncomingCall(null);
  };

  const endCall = async () => {
    if (!activeCall) return;
    const cid = activeCall.channelId;
    const pid = activeCall.partnerId;
    setActiveCall(null);
    setIncomingCall(null);
    refreshConversations();
    const targetCidEnd = activeConvIdRef.current || (activeConv ? activeConv.id : null);
    if (targetCidEnd) {
      setTimeout(() => {
        apiService.getMessages(targetCidEnd).then((res) => {
          if (res && res.messages && res.messages.length > 0) {
            setMessages(res.messages);
          }
        }).catch(() => {});
      }, 350);
    }
    try {
      await apiService.sendRequest('call_end', {
        channel_id: cid,
        user_id: currentUser?.id,
        partner_id: pid,
      });
    } catch (err) {
      console.warn('[Call] Error sending call_end:', err);
    }
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

  // Polling heartbeat while call is active
  // Connects caller when receiver accepts, and disconnects when partner hangs up
  useEffect(() => {
    if (!activeCall || !activeCall.channelId) return;

    const interval = setInterval(async () => {
      try {
        const res = await apiService.sendRequest('check_call_status', {
          channel_id: activeCall.channelId,
          caller_id: currentUser?.id,
          receiver_id: activeCall.partnerId,
        });

        if (res && res.success && res.status === 'connected') {
          if (!activeCall.isConnected) {
            setActiveCall((prev) =>
              prev ? { ...prev, isConnected: true, channelId: res.channel_id || prev.channelId } : null
            );
          }
        } else if (res && res.status === 'ended') {
          // Partner ended or rejected the call
          setActiveCall(null);
          setIncomingCall(null);
          refreshConversations();
          const targetCid = activeConvIdRef.current || (activeConv ? activeConv.id : null);
          if (targetCid) {
            setTimeout(() => {
              apiService.getMessages(targetCid).then((mRes) => {
                if (mRes && mRes.messages && mRes.messages.length > 0) {
                  setMessages(mRes.messages);
                }
              }).catch(() => {});
            }, 300);
          }
        }
      } catch (err) {
        // Silent catch on poll
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [activeCall?.channelId, activeCall?.isConnected, activeCall?.partnerId, currentUser?.id]);

  // Listen to real-time events from Python Server
  useEffect(() => {
    const unsubscribe = apiService.onServerEvent((event: ServerEvent) => {
      switch (event.type) {
        case 'new_message':
          if (event.message) {
            const newMsg = normalizeMessage(event.message);
            const currentCid = activeConvIdRef.current || (activeConv ? activeConv.id : null);
            const isCurrentChat = Boolean(currentCid && String(currentCid) === String(newMsg.conversation_id));

            if (isCurrentChat) {
              setMessages((prev) => {
                if (prev.some((m) => m.id === newMsg.id)) return prev;
                return [...prev, newMsg];
              });
            }

            // If message is from someone else, trigger notification sound and desktop alert
            if (currentUser && Number(newMsg.sender_id) !== Number(currentUser.id)) {
              playMessageNotificationSound();
              // Trigger Windows desktop notification if app is in background or looking at another chat
              if (document.hidden || !isCurrentChat) {
                triggerDesktopNotification(
                  newMsg.sender_name || 'Tin nhắn mới',
                  newMsg.content || 'Đã gửi một tệp đính kèm'
                );
              }
            }

            refreshConversations();
          }
          break;

        case 'message_recalled': {
          const recalledId = event.message_id || event.msg_id;
          if (recalledId) {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === recalledId ? { ...m, is_deleted: 1, content: 'Tin nhắn đã được thu hồi' } : m
              )
            );
          }
          break;
        }

        case 'reaction_updated': {
          const rxMsgId = event.message_id || event.msg_id;
          const rxList = event.reactions || event.data?.reactions;
          if (rxMsgId && rxList) {
            setMessages((prev) =>
              prev.map((m) => (m.id === rxMsgId ? { ...m, reactions: rxList } : m))
            );
          }
          break;
        }

        case 'pinned_updated': {
          const pinConvId = event.conversation_id || event.conv_id;
          if (activeConv && String(activeConv.id) === String(pinConvId)) {
            const pinnedObj = event.pinned !== undefined ? event.pinned : (event.data?.pinned || null);
            setPinnedMessage(pinnedObj);
            setMessages((prev) =>
              prev.map((m) => (pinnedObj && m.id === pinnedObj.id ? { ...m, is_pinned: 1 } : { ...m, is_pinned: 0 }))
            );
          }
          break;
        }

        case 'user_typing': {
          const typingConvId = event.conversation_id || event.conv_id;
          if (activeConv && String(activeConv.id) === String(typingConvId)) {
            const senderName = event.sender_name || event.data?.sender_name || 'Đối phương';
            setTypingUser(senderName);
            setTimeout(() => setTypingUser(null), 3000);
          }
          break;
        }

        case 'conversation_deleted': {
          const delConvId = event.conversation_id || event.conv_id;
          if (activeConv && String(activeConv.id) === String(delConvId)) {
            setActiveConv(null);
          }
          refreshConversations();
          break;
        }

        case 'block_status_changed':
          refreshConversations();
          break;

        case 'call_incoming':
          if (event.caller_id && event.channel_id) {
            setIncomingCall({
              channelId: event.channel_id,
              callerId: event.caller_id,
              callerName: event.caller_name || 'Người dùng',
              callType: event.call_type || 'voice',
            });
            triggerDesktopNotification(
              `Cuộc gọi ${event.call_type === 'video' ? 'Video' : 'thoại'} đến`,
              `${event.caller_name || 'Người dùng'} đang gọi cho bạn...`
            );
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
          refreshConversations();
          const targetCidEnded = activeConvIdRef.current || (activeConv ? activeConv.id : null);
          if (targetCidEnded) {
            setTimeout(() => {
              apiService.getMessages(targetCidEnded).then((res) => {
                if (res && res.messages && res.messages.length > 0) {
                  setMessages(res.messages);
                }
              }).catch(() => {});
            }, 350);
          }
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

        case 'kicked_from_group': {
          const kickConvId = event.conversation_id;
          if (activeConv && String(activeConv.id) === String(kickConvId)) {
            setActiveConv(null);
            setMessages([]);
            alert(event.message || 'Bạn đã bị quản trị viên kích khỏi nhóm trò chuyện!');
          }
          refreshConversations();
          break;
        }

        case 'member_kicked':
          refreshConversations();
          break;

        case 'member_role_updated': {
          const rConvId = event.conversation_id;
          if (activeConv && String(activeConv.id) === String(rConvId)) {
            if (currentUser && Number(event.target_id) === Number(currentUser.id)) {
              setActiveConv((prev) => (prev ? { ...prev, my_role: event.new_role } : null));
            }
          }
          refreshConversations();
          break;
        }

        case 'member_mute_updated': {
          const mConvId = event.conversation_id;
          if (activeConv && String(activeConv.id) === String(mConvId)) {
            if (currentUser && Number(event.target_id) === Number(currentUser.id)) {
              setActiveConv((prev) =>
                prev
                  ? {
                      ...prev,
                      my_is_muted: event.is_muted ? 1 : 0,
                      my_muted_by: event.muted_by_name,
                    }
                  : null
              );
            }
          }
          refreshConversations();
          break;
        }

        case 'group_mute_updated': {
          const gConvId = event.conversation_id;
          if (activeConv && String(activeConv.id) === String(gConvId)) {
            setActiveConv((prev) =>
              prev
                ? {
                    ...prev,
                    is_muted: event.is_muted ? 1 : 0,
                    custom_mute_text: event.custom_text,
                  }
                : null
            );
          }
          refreshConversations();
          break;
        }

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
                      title: prev.nicknames?.[u.id] || u.full_name || prev.title,
                      original_title: u.full_name || prev.original_title,
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

        case 'group_info_updated': {
          const updConv = event.conversation;
          const updId = event.conversation_id;
          if (String(activeConvIdRef.current) === String(updId)) {
            setActiveConv((prev) =>
              prev
                ? {
                    ...prev,
                    title: updConv?.name || prev.title,
                    avatar_url: updConv?.avatar_url !== undefined ? updConv.avatar_url : prev.avatar_url,
                  }
                : null
            );
          }
          refreshConversations();
          break;
        }

        case 'nickname_updated': {
          const nConvId = event.conversation_id;
          const targetUid = event.target_user_id;
          const newNick = event.nickname;
          const allNicks = event.all_nicknames;
          if (String(activeConvIdRef.current) === String(nConvId)) {
            setActiveConv((prev) => {
              if (!prev) return null;
              const updatedNicks = allNicks || { ...(prev.nicknames || {}), [targetUid]: newNick };
              let updatedTitle = prev.title;
              if (prev.type === 'direct' && prev.partner_id === targetUid) {
                updatedTitle = newNick || prev.original_title || prev.title;
              }
              return {
                ...prev,
                title: updatedTitle,
                nicknames: updatedNicks,
              };
            });
          }
          refreshConversations();
          break;
        }

        case 'conversation_theme_updated': {
          const tConvId = event.conversation_id;
          const newTheme = event.theme;
          if (String(activeConvIdRef.current) === String(tConvId)) {
            setActiveConv((prev) => (prev ? { ...prev, theme: newTheme } : null));
          }
          refreshConversations();
          break;
        }

        case 'connection_status':
          if (event.connected && currentUser?.session_token) {
            apiService
              .sendRequest('identify', {
                user_id: currentUser.id,
                session_token: currentUser.session_token,
              })
              .then((res) => {
                if (res?.success) {
                  refreshConversations();
                  refreshFriends();
                }
              })
              .catch(() => {});
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

  return (
    <ChatContext.Provider
      value={{
        currentUser,
        setCurrentUser,
        conversations,
        activeConv,
        setActiveConv,
        messages,
        setMessages,
        loadingMessages,
        friends,
        pendingFriends,
        sentFriendRequestIds,
        isLocked,
        setIsLocked,
        theme,
        setTheme,
        typingUser,
        repositioningImage,
        setRepositioningImage,
        isSidebarCollapsed,
        setIsSidebarCollapsed,
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
        unpinMessage,
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
