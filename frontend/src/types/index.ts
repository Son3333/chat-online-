export interface User {
  id: number;
  username: string;
  full_name: string;
  avatar_color?: string;
  avatar_url?: string;
  phone_number?: string;
  is_phone_verified?: number | boolean;
  status?: string;
  pin_code?: string;
  is_online?: number | boolean;
  created_at?: string;
}

export type MessageType = 'text' | 'image' | 'video' | 'file' | 'location';

export interface LastMessage {
  id?: number;
  sender_name?: string;
  content: string;
  msg_type?: MessageType;
  created_at?: string;
}

export interface Conversation {
  id: string | number;
  title: string;
  type: 'direct' | 'group' | 'saved';
  avatar_color?: string;
  avatar_url?: string;
  partner_id?: number | null;
  partner_username?: string;
  phone_number?: string;
  is_phone_verified?: number | boolean;
  is_online?: number | boolean;
  member_count?: number;
  last_message?: LastMessage | null;
  unread_count?: number;
  is_pinned?: boolean;
}

export interface ReactionUser {
  id: number;
  name: string;
}

export interface MessageReaction {
  reaction: string;
  count: number;
  users: ReactionUser[];
}

export interface Message {
  id: number;
  conversation_id: string | number;
  sender_id: number;
  sender_name: string;
  avatar_color?: string;
  avatar_url?: string;
  content: string;
  msg_type: MessageType;
  file_id?: string | null;
  file_size?: number;
  original_name?: string;
  reply_to_id?: number | null;
  reply_preview?: string | null;
  is_deleted?: number | boolean;
  created_at: string;
  reactions?: MessageReaction[];
  is_pinned?: boolean;
}

export interface Friend {
  id: number;
  username: string;
  full_name: string;
  avatar_color?: string;
  avatar_url?: string;
  phone_number?: string;
  is_phone_verified?: number | boolean;
  is_online?: number | boolean;
}

export interface FriendRequest {
  request_id: number;
  sender_id: number;
  sender_username: string;
  sender_full_name: string;
  avatar_color?: string;
  avatar_url?: string;
  created_at: string;
}

export interface ActiveCallState {
  partnerId: number;
  partnerName: string;
  callType: 'voice' | 'video';
  channelId?: string;
  isOutgoing?: boolean;
  isConnected?: boolean;
}

export interface IncomingCallState {
  channelId: string;
  callerId: number;
  callerName: string;
  callType: 'voice' | 'video';
}

export interface CallPacket {
  action: 'call_invite' | 'call_accept' | 'call_reject' | 'call_end' | 'call_media' | 'call_request' | 'call_response';
  caller_id?: number;
  receiver_id?: number;
  target_id?: number;
  conversation_id?: string | number;
  channel_id?: string;
  call_type?: 'voice' | 'video';
  accepted?: boolean;
  reason?: string;
  media_type?: 'audio' | 'video';
  data?: string;
}

export interface ServerEvent {
  type: string;
  data?: any;
  message?: Message;
  message_id?: number;
  msg_id?: number;
  user_id?: number;
  sender_id?: number;
  sender_name?: string;
  is_online?: number;
  conv_id?: string | number;
  conversation_id?: string | number;
  reaction?: string;
  reactions?: MessageReaction[];
  pinned?: any;
  caller_id?: number;
  caller_name?: string;
  avatar_color?: string;
  call_type?: 'voice' | 'video';
  channel_id?: string;
  duration?: string;
  target_id?: number;
  user?: User;
  connected?: boolean;
  [key: string]: any;
}

