import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock window.api for Vitest jsdom environment
Object.defineProperty(window, 'api', {
  value: {
    sendRequest: vi.fn().mockResolvedValue({ success: true }),
    onServerEvent: vi.fn().mockReturnValue(() => {}),
    minimizeWindow: vi.fn(),
    maximizeWindow: vi.fn(),
    closeWindow: vi.fn(),
    setAlwaysOnTop: vi.fn().mockResolvedValue(true),
    isAlwaysOnTop: vi.fn().mockResolvedValue(false),
    selectLocalFile: vi.fn().mockResolvedValue({ canceled: true }),
    saveDownloadedFile: vi.fn().mockResolvedValue({ success: true }),
  },
  writable: true,
});

// Mock scrollIntoView
window.HTMLElement.prototype.scrollIntoView = vi.fn();

