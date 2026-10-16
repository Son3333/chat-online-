import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuthModal } from '../features/auth/AuthModal';
import { ChatProvider } from '../context/ChatContext';
import { apiService } from '../services/api';

describe('AuthModal Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders login form by default with Telegram brand title', () => {
    render(
      <ChatProvider>
        <AuthModal />
      </ChatProvider>
    );

    expect(screen.getByText('Đăng Nhập Telegram')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('vd: thaison99')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Đăng Nhập' })).toBeInTheDocument();
  });

  it('switches to register mode when clicking register link', () => {
    render(
      <ChatProvider>
        <AuthModal />
      </ChatProvider>
    );

    const switchBtn = screen.getByText('Đăng ký tài khoản mới');
    fireEvent.click(switchBtn);

    expect(screen.getByText('Tạo Tài Khoản Mới')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Ví dụ: Vũ Duy Thái Sơn')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Đăng Ký Tài Khoản' })).toBeInTheDocument();
  });

  it('shows validation error when fields are empty on submit', async () => {
    render(
      <ChatProvider>
        <AuthModal />
      </ChatProvider>
    );

    const submitBtn = screen.getByRole('button', { name: 'Đăng Nhập' });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!')).toBeInTheDocument();
    });
  });

  it('calls apiService.login on valid credentials', async () => {
    const loginSpy = vi.spyOn(apiService, 'login').mockResolvedValueOnce({
      success: true,
      user: { id: 1, username: 'thaison', full_name: 'Vũ Duy Thái Sơn' },
    });

    render(
      <ChatProvider>
        <AuthModal />
      </ChatProvider>
    );

    const userInput = screen.getByPlaceholderText('vd: thaison99');
    const passInput = screen.getByPlaceholderText('••••••••');
    const submitBtn = screen.getByRole('button', { name: 'Đăng Nhập' });

    fireEvent.change(userInput, { target: { value: 'thaison' } });
    fireEvent.change(passInput, { target: { value: 'Password123@' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(loginSpy).toHaveBeenCalledWith('thaison', 'Password123@');
    });
  });
});

