import React, { useState, useEffect, useRef } from 'react';
import { Minus, Square, X, Pin, Lock, Sun, Moon, RefreshCw, Sparkles, Globe, Server, Check, ChevronDown } from 'lucide-react';
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
  const [serverConfig, setServerConfig] = useState<{ host: string; port: number; isWan: boolean }>({
    host: 'bore.pub',
    port: 38888,
    isWan: true,
  });
  const [showServerMenu, setShowServerMenu] = useState(false);
  const [customHost, setCustomHost] = useState('');
  const [customPort, setCustomPort] = useState('');
  const [isSwitchingServer, setIsSwitchingServer] = useState(false);
  const serverMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiService.isAlwaysOnTop().then(setIsAlwaysOnTop);
    apiService.getServerConfig().then((cfg) => {
      if (cfg) {
        setServerConfig(cfg);
        setCustomHost(cfg.host);
        setCustomPort(String(cfg.port));
      }
    });

    const handleClickOutside = (e: MouseEvent) => {
      if (serverMenuRef.current && !serverMenuRef.current.contains(e.target as Node)) {
        setShowServerMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleAlwaysOnTop = async () => {
    const nextState = !isAlwaysOnTop;
    const res = await apiService.setAlwaysOnTop(nextState);
    setIsAlwaysOnTop(res);
  };

  const [logoError, setLogoError] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([refreshConversations(), refreshFriends()]);
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const handleSelectServer = async (host: string, port: number) => {
    setIsSwitchingServer(true);
    try {
      const res = await apiService.setServerConfig(host, port);
      setServerConfig({ host: res.host, port: res.port, isWan: res.isWan });
      setShowServerMenu(false);
      setTimeout(async () => {
        await Promise.all([refreshConversations(), refreshFriends()]);
        setIsSwitchingServer(false);
      }, 800);
    } catch (e) {
      console.error('Error switching server:', e);
      setIsSwitchingServer(false);
    }
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

        {/* Server Status Pill & Dropdown */}
        <div className="relative app-no-drag" ref={serverMenuRef}>
          <button
            onClick={() => setShowServerMenu(!showServerMenu)}
            title={`Máy chủ hiện tại: ${serverConfig.host}:${serverConfig.port}. Nhấn để đổi máy chủ.`}
            className={`flex items-center space-x-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium border transition-all cursor-pointer ${
              serverConfig.isWan
                ? 'bg-blue-500/10 hover:bg-blue-500/20 text-blue-600 dark:text-blue-400 border-blue-500/30'
                : 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border-emerald-500/30'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${serverConfig.isWan ? 'bg-blue-500 animate-pulse' : 'bg-emerald-500'}`} />
            {serverConfig.isWan ? <Globe className="w-3 h-3" /> : <Server className="w-3 h-3" />}
            <span className="font-semibold">{serverConfig.isWan ? `WAN: ${serverConfig.host}` : `Local: ${serverConfig.host}`}</span>
            <ChevronDown className="w-2.5 h-2.5 opacity-60" />
          </button>

          {/* Server Switcher Dropdown */}
          {showServerMenu && (
            <div className="absolute left-0 top-7 w-72 bg-white dark:bg-[#1e2c3a] border border-slate-200 dark:border-slate-700/80 rounded-xl shadow-2xl py-2 z-50 text-xs text-slate-700 dark:text-slate-200 animate-in fade-in zoom-in-95">
              <div className="px-3 py-1 font-semibold text-[10px] uppercase tracking-wider text-slate-400 border-b border-slate-100 dark:border-slate-700/50 pb-1.5 mb-1">
                Chọn Máy Chủ Kết Nối
              </div>

              {/* WAN Option */}
              <button
                onClick={() => handleSelectServer('bore.pub', 38888)}
                disabled={isSwitchingServer}
                className="w-full px-3 py-2 text-left hover:bg-blue-50 dark:hover:bg-blue-900/30 flex items-center justify-between transition-colors disabled:opacity-50"
              >
                <div className="flex items-center space-x-2.5">
                  <Globe className="w-4 h-4 text-blue-500 flex-shrink-0" />
                  <div>
                    <div className="font-semibold text-slate-800 dark:text-slate-100 flex items-center space-x-1">
                      <span>Máy chủ WAN (Internet)</span>
                      <span className="text-[9px] bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-300 px-1 py-0.2 rounded font-bold">Khuyên dùng</span>
                    </div>
                    <div className="text-[10px] text-slate-400">bore.pub:38888 (Dành cho 2 máy gọi & chat)</div>
                  </div>
                </div>
                {serverConfig.host === 'bore.pub' && <Check className="w-3.5 h-3.5 text-blue-500 flex-shrink-0" />}
              </button>

              {/* Local Option */}
              <button
                onClick={() => handleSelectServer('127.0.0.1', 8888)}
                disabled={isSwitchingServer}
                className="w-full px-3 py-2 text-left hover:bg-emerald-50 dark:hover:bg-emerald-900/30 flex items-center justify-between transition-colors disabled:opacity-50"
              >
                <div className="flex items-center space-x-2.5">
                  <Server className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                  <div>
                    <div className="font-semibold text-slate-800 dark:text-slate-100">Máy chủ Cục bộ (Local)</div>
                    <div className="text-[10px] text-slate-400">127.0.0.1:8888 (Chỉ máy mở server)</div>
                  </div>
                </div>
                {serverConfig.host === '127.0.0.1' && <Check className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />}
              </button>

              {/* Custom Endpoint Input */}
              <div className="p-2.5 mt-1 border-t border-slate-100 dark:border-slate-700/50">
                <div className="text-[10px] text-slate-400 mb-1.5 font-medium">Hoặc nhập máy chủ tùy chỉnh:</div>
                <div className="flex space-x-1.5">
                  <input
                    type="text"
                    placeholder="bore.pub / IP"
                    value={customHost}
                    onChange={(e) => setCustomHost(e.target.value)}
                    className="flex-1 px-2 py-1 text-[11px] rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 outline-none focus:border-blue-500"
                  />
                  <input
                    type="number"
                    placeholder="Port"
                    value={customPort}
                    onChange={(e) => setCustomPort(e.target.value)}
                    className="w-16 px-2 py-1 text-[11px] rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 outline-none focus:border-blue-500"
                  />
                  <button
                    onClick={() => {
                      if (customHost.trim() && customPort) {
                        handleSelectServer(customHost.trim(), parseInt(customPort, 10));
                      }
                    }}
                    disabled={isSwitchingServer}
                    className="px-2.5 py-1 bg-[#2481cc] hover:bg-[#1d6fa5] text-white rounded text-[11px] font-semibold transition-colors disabled:opacity-50"
                  >
                    {isSwitchingServer ? '...' : 'Lưu'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

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

