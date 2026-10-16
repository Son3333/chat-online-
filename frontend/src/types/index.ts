export interface User {
  id: number;
  username: string;
  full_name: string;
  avatar_color?: string;
  status?: string;
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
  partner_id?: number | null;
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
  is_online?: number | boolean;
}

export interface FriendRequest {
  request_id: number;
  sender_id: number;
  sender_username: string;
  sender_full_name: string;
  created_at: string;
}

export interface CallPacket {
  action: 'call_request' | 'call_response' | 'call_end' | 'call_media';
  caller_id?: number;
  target_id?: number;
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
  user_id?: number;
  is_online?: number;
  conv_id?: string | number;
  reaction?: string;
  msg_id?: number;
  caller_id?: number;
  caller_name?: string;
  call_type?: 'voice' | 'video';
  target_id?: number;
}

