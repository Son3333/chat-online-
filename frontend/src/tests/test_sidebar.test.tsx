import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Sidebar } from '../features/chat/Sidebar';
import { ChatProvider } from '../context/ChatContext';

describe('Sidebar Component', () => {
  it('renders search input and action buttons', () => {
    const onOpenGroup = vi.fn();
    const onOpenContacts = vi.fn();

    render(
      <ChatProvider>
        <Sidebar onOpenCreateGroup={onOpenGroup} onOpenContacts={onOpenContacts} />
      </ChatProvider>
    );

    expect(screen.getByPlaceholderText('Tìm kiếm @user hoặc #ID...')).toBeInTheDocument();
    expect(screen.getByText('Tạo Nhóm')).toBeInTheDocument();
    expect(screen.getByText('Cloud Cá Nhân')).toBeInTheDocument();
    expect(screen.getByText('Tất cả')).toBeInTheDocument();
    expect(screen.getByText('Cá nhân')).toBeInTheDocument();
    expect(screen.getByText('Nhóm')).toBeInTheDocument();
  });

  it('triggers onOpenCreateGroup when clicking Tạo Nhóm', () => {
    const onOpenGroup = vi.fn();
    const onOpenContacts = vi.fn();

    render(
      <ChatProvider>
        <Sidebar onOpenCreateGroup={onOpenGroup} onOpenContacts={onOpenContacts} />
      </ChatProvider>
    );

    const btn = screen.getByText('Tạo Nhóm');
    fireEvent.click(btn);
    expect(onOpenGroup).toHaveBeenCalledTimes(1);
  });
});

