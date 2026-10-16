import React, { useState, useEffect } from 'react';
import { Minus, Square, X, Pin, Lock, Sun, Moon, RefreshCw, Sparkles } from 'lucide-react';
import { useChat } from '../context/ChatContext';
import { apiService } from '../services/api';
import APP_LOGO from '../assets/logo';

interface TitleBarProps {
  hasUpdateAvailable?: boolean;
  onOpenUpdateModal?: () => void;
}

export const TitleBar: React.FC<TitleBarProps> = ({ hasUpdateAvailable, onOpenUpdateModal }) => {
  const { currentUser, isLocked, setIsLocked, theme, setTheme, refreshConversations, refreshFriends } = useChat();
  const [isAlwaysOnTop, setIsAlwaysOnTop] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [logoError, setLogoError] = useState(false);

  useEffect(() => {
    apiService.isAlwaysOnTop().then(setIsAlwaysOnTop);
  }, []);

  const toggleAlwaysOnTop = async () => {
    const nextState = !isAlwaysOnTop;
    const res = await apiService.setAlwaysOnTop(nextState);
    setIsAlwaysOnTop(res);
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([refreshConversations(), refreshFriends()]);
    setTimeout(() => setIsRefreshing(false), 500);
  };

  return (
    <div className="h-9 w-full bg-slate-100 dark:bg-[#17212b] border-b border-slate-200 dark:border-slate-800/80 flex items-center justify-between select-none app-drag-region px-3 z-50">
      {/* Left: App Title and Pulsing Update Notification */}
      <div className="flex items-center space-x-2.5 app-no-drag">
        {logoError ? (
          <div className="w-5 h-5 rounded-full bg-[#2481cc] text-white font-bold text-[10px] flex items-center justify-center flex-shrink-0 shadow-sm">
            V
          </div>
        ) : (
          <img
            src={APP_LOGO}
            alt="Logo"
            onError={() => setLogoError(true)}
            className="w-5 h-5 rounded-full object-cover shadow-sm border border-amber-400/80 bg-amber-300 flex-shrink-0"
          />
        )}
        <span className="text-xs font-semibold text-slate-700 dark:text-slate-200 tracking-wide">
          Vibe Người Tốt
        </span>

        {hasUpdateAvailable && (
          <button
            onClick={onOpenUpdateModal}
            title="Có bản cập nhật mới - Nhấn để xem & nâng cấp"
            className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-gradient-to-r from-blue-500/20 to-sky-500/20 hover:from-blue-500/30 hover:to-sky-500/30 text-[#2481cc] dark:text-sky-400 text-[10px] font-bold border border-blue-500/30 shadow-xs transition-all app-no-drag cursor-pointer active:scale-95"
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-sky-500"></span>
            </span>
            <Sparkles className="w-2.5 h-2.5 text-[#2481cc] dark:text-sky-400" />
            <span className="animate-pulse">Có bản mới</span>
          </button>
        )}
      </div>

      {/* Right: Quick actions and window controls */}
      <div className="flex items-center space-x-1 app-no-drag">
        {currentUser && !isLocked && (
          <>
            {/* Refresh */}
            <button
              onClick={handleRefresh}
              title="Làm mới dữ liệu"
              className="p-1.5 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700/60 text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            </button>

            {/* App Lock */}
            <button
              onClick={() => setIsLocked(true)}
              title="Khóa ứng dụng (Ctrl+L)"
              className="p-1.5 rounded-md hover:bg-red-500/10 text-slate-500 dark:text-slate-400 hover:text-red-500 transition-colors"
            >
              <Lock className="w-3.5 h-3.5" />
            </button>

            {/* Always on top Pin */}
            <button
              onClick={toggleAlwaysOnTop}
              title={isAlwaysOnTop ? 'Bỏ ghim cửa sổ' : 'Ghim cửa sổ luôn nổi'}
              className={`p-1.5 rounded-md transition-colors ${
                isAlwaysOnTop
                  ? 'bg-[#2481cc]/15 text-[#2481cc]'
                  : 'hover:bg-slate-200 dark:hover:bg-slate-700/60 text-slate-500 dark:text-slate-400'
              }`}
            >
              <Pin className="w-3.5 h-3.5" />
            </button>
          </>
        )}

        {/* Theme Toggle */}
        <button
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          title={theme === 'dark' ? 'Chuyển sang Giao diện Sáng' : 'Chuyển sang Giao diện Tối'}
          className="p-1.5 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700/60 text-slate-500 dark:text-slate-400 hover:text-amber-500 transition-colors"
        >
          {theme === 'dark' ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
        </button>

        <div className="w-px h-3.5 bg-slate-300 dark:bg-slate-700/80 mx-1" />

        {/* Window controls */}
        <button
          onClick={() => apiService.minimizeWindow()}
          title="Thu nhỏ"
          className="w-7 h-7 flex items-center justify-center rounded-md hover:bg-slate-200 dark:hover:bg-slate-700/60 text-slate-500 dark:text-slate-400 transition-colors"
        >
          <Minus className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={() => apiService.maximizeWindow()}
          title="Phóng to"
          className="w-7 h-7 flex items-center justify-center rounded-md hover:bg-slate-200 dark:hover:bg-slate-700/60 text-slate-500 dark:text-slate-400 transition-colors"
        >
          <Square className="w-3 h-3" />
        </button>

        <button
          onClick={() => apiService.closeWindow()}
          title="Đóng ứng dụng"
          className="w-7 h-7 flex items-center justify-center rounded-md hover:bg-red-500 hover:text-white text-slate-500 dark:text-slate-400 transition-colors"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};

