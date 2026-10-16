import React, { useState } from 'react';
import { Phone, Video, Users, MoreVertical, Search, Info } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { getInitials } from '../../lib/utils';
import { ChatInfoModal } from './ChatInfoModal';

export const ChatHeader: React.FC = () => {
  const { activeConv, typingUser, startCall } = useChat();
  const [showInfo, setShowInfo] = useState(false);

  if (!activeConv) return null;

  const isGroup = activeConv.type === 'group';
  const isSaved = activeConv.type === 'saved';
  const isDirect = activeConv.type === 'direct';

  return (
    <>
      <div className="h-14 px-4 bg-white dark:bg-[#17212b] border-b border-slate-200 dark:border-slate-800/80 flex items-center justify-between select-none">
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
      <div className="flex items-center space-x-1">
        {isDirect && (
          <>
            <button
              onClick={() => startCall('voice')}
              title="Gọi Thoại"
              className="p-2 rounded-lg text-slate-500 hover:text-[#2481cc] hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-slate-300 transition-colors"
            >
              <Phone className="w-4 h-4" />
            </button>

            <button
              onClick={() => startCall('video')}
              title="Gọi Video"
              className="p-2 rounded-lg text-slate-500 hover:text-emerald-500 hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-slate-300 transition-colors"
            >
              <Video className="w-4 h-4" />
            </button>
          </>
        )}

        <button
          title="Tìm kiếm trong cuộc trò chuyện"
          className="p-2 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-slate-300 transition-colors"
        >
          <Search className="w-4 h-4" />
        </button>

          <button
            onClick={() => setShowInfo(true)}
            title="Xem thông tin hội thoại"
            className="p-2 rounded-lg text-slate-500 hover:text-[#2481cc] hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-slate-300 transition-colors"
          >
            <Info className="w-4 h-4" />
          </button>

          <button
            title="Tùy chọn khác"
            className="p-2 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-slate-300 transition-colors"
          >
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Popout Info Modal */}
      <ChatInfoModal isOpen={showInfo} onClose={() => setShowInfo(false)} />
    </>
  );
};

