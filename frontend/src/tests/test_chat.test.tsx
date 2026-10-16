import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatBubble } from '../features/chat/ChatBubble';
import { ChatProvider } from '../context/ChatContext';
import { Message } from '../types';

describe('ChatBubble Component', () => {
  const sampleMessage: Message = {
    id: 101,
    conversation_id: 'conv_1',
    sender_id: 1,
    sender_name: 'Vũ Duy Thái Sơn',
    content: 'Xin chào từ Telegram Desktop!',
    msg_type: 'text',
    created_at: '2026-10-16T10:00:00Z',
    reactions: [{ reaction: '❤️', count: 2, users: [{ id: 1, name: 'Sơn' }] }],
  };

  it('renders message text content and timestamp', () => {
    render(
      <ChatProvider>
        <ChatBubble message={sampleMessage} isSelf={true} />
      </ChatProvider>
    );

    expect(screen.getByText('Xin chào từ Telegram Desktop!')).toBeInTheDocument();
    expect(screen.getByText('❤️')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('renders file attachments with formatted file size', () => {
    const fileMessage: Message = {
      ...sampleMessage,
      id: 102,
      msg_type: 'file',
      file_id: 'file_abc_123',
      original_name: 'Bao_cao_tot_nghiep.pdf',
      file_size: 2048576, // ~1.95 MB
    };

    render(
      <ChatProvider>
        <ChatBubble message={fileMessage} isSelf={false} />
      </ChatProvider>
    );

    expect(screen.getByText('Bao_cao_tot_nghiep.pdf')).toBeInTheDocument();
    expect(screen.getByText('2.0 MB')).toBeInTheDocument();
  });

  it('renders reply preview block when message is a reply', () => {
    const replyMessage: Message = {
      ...sampleMessage,
      id: 103,
      reply_to_id: 100,
      reply_preview: 'Người dùng: Tin nhắn trước đó',
    };

    render(
      <ChatProvider>
        <ChatBubble message={replyMessage} isSelf={true} />
      </ChatProvider>
    );

    expect(screen.getByText('Trả lời:')).toBeInTheDocument();
    expect(screen.getByText('Người dùng: Tin nhắn trước đó')).toBeInTheDocument();
  });
});

