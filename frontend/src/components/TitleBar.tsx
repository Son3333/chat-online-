import React, { useState, useEffect } from 'react';
import { Minus, Square, X, Pin, Lock, Sun, Moon, RefreshCw, Radio } from 'lucide-react';
import { useChat } from '../context/ChatContext';
import { apiService } from '../services/api';

export const TitleBar: React.FC = () => {
  const { currentUser, isLocked, setIsLocked, theme, setTheme, refreshConversations } = useChat();
  const [isAlwaysOnTop, setIsAlwaysOnTop] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

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
    await refreshConversations();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  return (
    <div className="h-9 w-full bg-slate-100 dark:bg-[#17212b] border-b border-slate-200 dark:border-slate-800/80 flex items-center justify-between select-none app-drag-region px-3 z-50">
      {/* Left: App Title and Connection info */}
      <div className="flex items-center space-x-2.5">
        <div className="w-5 h-5 rounded-full bg-[#2481cc] flex items-center justify-center text-white text-xs font-bold shadow-sm">
          T
        </div>
        <span className="text-xs font-semibold text-slate-700 dark:text-slate-200 tracking-wide">
          Telegram Messenger
        </span>
        <div className="hidden sm:flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[10px] font-medium">
          <Radio className="w-2.5 h-2.5 animate-pulse" />
          <span>127.0.0.1:8888</span>
        </div>
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

