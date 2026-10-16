import React, { useState } from 'react';
import { Phone, Video, Users, MoreVertical, Search, Info, X, Bell, BellOff, Trash2 } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { getInitials } from '../../lib/utils';
import { ChatInfoModal } from './ChatInfoModal';

export const ChatHeader: React.FC = () => {
  const { activeConv, messages, typingUser, startCall } = useChat();
  const [showInfo, setShowInfo] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [showMenu, setShowMenu] = useState(false);
  const [isMuted, setIsMuted] = useState(false);

  if (!activeConv) return null;

  const isGroup = activeConv.type === 'group';
  const isSaved = activeConv.type === 'saved';
  const isDirect = activeConv.type === 'direct';

  const matchCount = searchKeyword.trim()
    ? messages.filter((m) => m.content?.toLowerCase().includes(searchKeyword.toLowerCase().trim())).length
    : 0;

  return (
    <>
      <div className="h-14 px-4 bg-white dark:bg-[#17212b] border-b border-slate-200 dark:border-slate-800/80 flex items-center justify-between select-none relative z-30">
        {/* Left: Avatar & Title & Status (Clickable to view info) */}
        <div
          onClick={() => setShowInfo(true)}
          className="flex items-center space-x-3 cursor-pointer hover:opacity-90 transition-opacity p-1 -ml-1 rounded-lg"
          title="Xem thông tin hội thoại"
        >
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white text-sm shadow-sm"
            style={{ backgroundColor: activeConv.avatar_color || (isGroup ? '#06b6d4' : '#2481cc') }}
          >
            {isGroup ? <Users className="w-5 h-5" /> : getInitials(activeConv.title)}
          </div>

          <div className="flex flex-col">
            <span className="font-semibold text-sm text-slate-800 dark:text-slate-100">
              {activeConv.title}
            </span>
            <span className="text-xs">
              {typingUser ? (
                <span className="text-[#2481cc] font-medium animate-pulse">
                  {typingUser} đang soạn tin nhắn...
                </span>
              ) : isGroup ? (
                <span className="text-slate-400">
                  {activeConv.member_count || 3} thành viên
                </span>
              ) : isSaved ? (
                <span className="text-indigo-400 font-medium">
                  Không gian lưu trữ cá nhân
                </span>
              ) : activeConv.is_online ? (
                <span className="text-emerald-500 font-medium flex items-center space-x-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
                  <span>Trực tuyến</span>
                </span>
              ) : (
                <span className="text-slate-400">Ngoại tuyến</span>
              )}
            </span>
          </div>
        </div>

        {/* Right: Actions (Call, Search, Menu) */}
        <div className="flex items-center space-x-1 relative">
          {isDirect && (
            <>
              <button
                onClick={() => startCall('voice')}
                title="Gọi Thoại (Voice Call)"
                className="p-2 rounded-lg text-slate-500 hover:text-[#2481cc] hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-slate-300 transition-colors cursor-pointer"
              >
                <Phone className="w-4 h-4" />
              </button>

              <button
                onClick={() => startCall('video')}
                title="Gọi Video HD (Camera)"
                className="p-2 rounded-lg text-slate-500 hover:text-emerald-500 hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-slate-300 transition-colors cursor-pointer"
              >
                <Video className="w-4 h-4" />
              </button>
            </>
          )}

          <button
            onClick={() => setShowSearch(!showSearch)}
            title="Tìm kiếm trong cuộc trò chuyện"
            className={`p-2 rounded-lg transition-colors cursor-pointer ${
              showSearch
                ? 'bg-[#2481cc]/15 text-[#2481cc]'
                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-slate-300'
            }`}
          >
            <Search className="w-4 h-4" />
          </button>

          <button
            onClick={() => setShowInfo(true)}
            title="Xem thông tin hội thoại"
            className="p-2 rounded-lg text-slate-500 hover:text-[#2481cc] hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-slate-300 transition-colors cursor-pointer"
          >
            <Info className="w-4 h-4" />
          </button>

          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              title="Tùy chọn khác"
              className="p-2 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-slate-300 transition-colors cursor-pointer"
            >
              <MoreVertical className="w-4 h-4" />
            </button>

            {/* Dropdown Menu */}
            {showMenu && (
              <div
                onClick={(e) => e.stopPropagation()}
                className="absolute right-0 top-10 w-52 bg-white dark:bg-[#1e2c3a] border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl py-1 z-50 animate-in fade-in zoom-in-95 duration-100 text-xs"
              >
                <button
                  onClick={() => {
                    setShowMenu(false);
                    setShowInfo(true);
                  }}
                  className="w-full px-3 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center space-x-2 text-slate-700 dark:text-slate-200"
                >
                  <Info className="w-4 h-4 text-[#2481cc]" />
                  <span>Xem thông tin hội thoại</span>
                </button>

                <button
                  onClick={() => {
                    setShowMenu(false);
                    setShowSearch(true);
                  }}
                  className="w-full px-3 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center space-x-2 text-slate-700 dark:text-slate-200"
                >
                  <Search className="w-4 h-4 text-emerald-500" />
                  <span>Tìm kiếm tin nhắn</span>
                </button>

                <button
                  onClick={() => {
                    setIsMuted(!isMuted);
                    setShowMenu(false);
                  }}
                  className="w-full px-3 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center space-x-2 text-slate-700 dark:text-slate-200"
                >
                  {isMuted ? <Bell className="w-4 h-4 text-amber-500" /> : <BellOff className="w-4 h-4 text-slate-400" />}
                  <span>{isMuted ? 'Bật thông báo' : 'Tắt thông báo'}</span>
                </button>

                <div className="h-px bg-slate-100 dark:bg-slate-700/60 my-1" />

                <button
                  onClick={() => setShowMenu(false)}
                  className="w-full px-3 py-2 text-left hover:bg-red-50 dark:hover:bg-red-500/10 flex items-center space-x-2 text-red-600 dark:text-red-400"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Xóa lịch sử trò chuyện</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* In-Chat Message Search Bar */}
      {showSearch && (
        <div className="h-10 px-4 bg-slate-100 dark:bg-[#1a2530] border-b border-slate-200 dark:border-slate-800 flex items-center justify-between animate-in slide-in-from-top-2 duration-150 text-xs">
          <div className="flex items-center space-x-2 flex-1 mr-3">
            <Search className="w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              autoFocus
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              placeholder="Tìm kiếm nội dung tin nhắn trong cuộc trò chuyện..."
              className="w-full bg-transparent focus:outline-none text-slate-800 dark:text-slate-100 placeholder-slate-400"
            />
            {searchKeyword.trim() && (
              <span className="text-[11px] text-slate-400 whitespace-nowrap font-medium">
                {matchCount} kết quả
              </span>
            )}
          </div>
          <button
            onClick={() => {
              setShowSearch(false);
              setSearchKeyword('');
            }}
            className="p-1 rounded-md text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Popout Info Modal */}
      <ChatInfoModal isOpen={showInfo} onClose={() => setShowInfo(false)} />
    </>
  );
};
