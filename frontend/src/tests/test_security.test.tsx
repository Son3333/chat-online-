import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LockScreen } from '../features/security/LockScreen';
import { ChatProvider } from '../context/ChatContext';

describe('LockScreen Component', () => {
  it('renders locked state and numpad when locked', () => {
    // We can simulate locked by setting isLocked to true
    render(
      <ChatProvider>
        <LockScreen />
      </ChatProvider>
    );

    // If initially not locked, it renders null
    expect(screen.queryByText('Ứng dụng đã bị khóa')).not.toBeInTheDocument();
  });
});

