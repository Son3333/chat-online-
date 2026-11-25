import React, { useState } from 'react';
import {
  Phone,
  Video,
  Users,
  MoreVertical,
  Search,
  Info,
  X,
  Bell,
  BellOff,
  Trash2,
  UserPlus,
  Ban,
  ChevronLeft,
  PanelLeftClose,
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { apiService } from '../../services/api';
import { getInitials } from '../../lib/utils';
import { ChatInfoModal } from './ChatInfoModal';
import { ChatThemeModal } from './ChatThemeModal';
import { Edit3, Sparkles } from 'lucide-react';

export const ChatHeader: React.FC = () => {
  const {
    activeConv,
    setActiveConv,
    messages,
    typingUser,
    startCall,
    friends,
    pendingFriends,
    sentFriendRequestIds,
    currentUser,
    refreshFriends,
    refreshConversations,
    isSidebarCollapsed,
    setIsSidebarCollapsed,
  } = useChat();
  const [showInfo, setShowInfo] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [showMenu, setShowMenu] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [showThemeModal, setShowThemeModal] = useState(false);
  const [showNicknamePrompt, setShowNicknamePrompt] = useState(false);
  const [nicknameInput, setNicknameInput] = useState('');

  if (!activeConv) return null;

  const isGroup = activeConv.type === 'group';
  const isSaved = activeConv.type === 'saved';
  const isDirect = activeConv.type === 'direct';

  const partnerId =
    activeConv.partner_id ||
    (typeof activeConv.id === 'string' && activeConv.id.startsWith('direct_')
      ? Number(activeConv.id.replace('direct_', ''))
      : undefined);

  const isFriend = Boolean(partnerId && friends.some((f) => f.id === partnerId));
  const isSent = Boolean(partnerId && sentFriendRequestIds.includes(partnerId));
  const isIncoming = Boolean(partnerId && pendingFriends.some((p) => p.id === partnerId));

  const handleAddFriend = async () => {
    if (!currentUser || !partnerId) return;
    const res = await apiService.sendFriendRequest(currentUser.id, partnerId);
    if (res && res.success) {
      await refreshFriends();
    }
  };

  const handleBlockUser = async () => {
    if (!currentUser || !partnerId) return;
    if (!confirm(`Bạn có chắc chắn muốn chặn ${activeConv.title}? Họ sẽ không thể gửi tin nhắn cho bạn.`)) return;
    const res = await apiService.blockUser(currentUser.id, partnerId);
    if (res && res.success) {
      await refreshFriends();
      await refreshConversations();
    }
  };

  const handleDeleteHistory = async () => {
    if (!currentUser) return;
    if (!confirm('Bạn có chắc chắn muốn xóa toàn bộ lịch sử trò chuyện này?')) return;
    setShowMenu(false);
    await apiService.deleteConversation(activeConv.id, currentUser.id);
    await refreshConversations();
  };

  const handleSaveNickname = async () => {
    if (!currentUser || !partnerId) return;
    const nick = nicknameInput.trim();
    const res = await apiService.setConversationNickname(activeConv.id, currentUser.id, partnerId, nick);
    if (res && res.success) {
      setShowNicknamePrompt(false);
      const newTitle = nick || activeConv.original_title || activeConv.title;
      setActiveConv({
        ...activeConv,
        title: newTitle,
        nicknames: { ...(activeConv.nicknames || {}), [partnerId]: nick }
      });
      await refreshConversations();
    } else {
      alert(res?.message || 'Không thể đặt biệt danh!');
    }
  };

  const matchCount = searchKeyword.trim()
    ? messages.filter((m) => m.content?.toLowerCase().includes(searchKeyword.toLowerCase().trim())).length
    : 0;

  return (
    <>
      <div className="h-14 px-4 bg-white dark:bg-[#17212b] border-b border-slate-200 dark:border-slate-800/80 flex items-center justify-between select-none relative z-30">
        {/* Left: Back button (on compact) + Avatar & Title */}
        <div className="flex items-center space-x-1.5 overflow-hidden mr-2">
          {isSidebarCollapsed ? (
            <button
              type="button"
              onClick={() => setIsSidebarCollapsed(false)}
              className="p-1.5 -ml-1 rounded-lg text-slate-500 hover:text-[#2481cc] hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-slate-300 transition-colors cursor-pointer flex-shrink-0 flex items-center justify-center"
              title="Quay lại danh sách hội thoại"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setIsSidebarCollapsed(true)}
              className="hidden lg:flex p-1.5 -ml-1 rounded-lg text-slate-500 hover:text-[#2481cc] hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-slate-300 transition-colors cursor-pointer flex-shrink-0 items-center justify-center"
              title="Thu gọn danh sách hội thoại"
            >
              <PanelLeftClose className="w-5 h-5" />
            </button>
          )}

          <div
            onClick={() => setShowInfo(true)}
            className="flex items-center space-x-2.5 cursor-pointer hover:opacity-90 transition-opacity p-1 rounded-lg truncate"
            title="Xem thông tin hội thoại"
          >
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white text-sm shadow-sm overflow-hidden flex-shrink-0"
              style={{ backgroundColor: activeConv.avatar_color || (isGroup ? '#06b6d4' : '#2481cc') }}
            >
              {activeConv.avatar_url ? (
                <img src={activeConv.avatar_url} alt="" className="w-full h-full object-cover" />
              ) : isGroup ? (
                <Users className="w-5 h-5" />
              ) : (
                getInitials(activeConv.title)
              )}
            </div>

            <div className="flex flex-col truncate">
              <span className="font-semibold text-sm text-slate-800 dark:text-slate-100 truncate">
                {activeConv.title}
              </span>
              <span className="text-xs truncate">
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
        </div>

        {/* Right: Actions (Clean & Compact like Zalo: Voice, Video, Search, Info, More) */}
        <div className="flex items-center space-x-1 relative flex-shrink-0">
          {isDirect && (
            <>
              {/* Always accessible voice call button */}
              <button
                onClick={() => startCall('voice')}
                title="Gọi Thoại (Voice Call)"
                className="p-2 rounded-lg text-slate-500 hover:text-[#2481cc] hover:bg-slate-100 dark:hover:bg-slate-800 dark:text-slate-300 transition-colors cursor-pointer"
              >
                <Phone className="w-4 h-4" />
              </button>

              {/* Always accessible video call button */}
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
                    setShowMenu(false);
                    setShowThemeModal(true);
                  }}
                  className="w-full px-3 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center space-x-2 text-slate-700 dark:text-slate-200"
                >
                  <Sparkles className="w-4 h-4 text-purple-500" />
                  <span>Đổi giao diện / hình nền</span>
                </button>

                {isDirect && partnerId && (
                  <button
                    onClick={() => {
                      setShowMenu(false);
                      setNicknameInput(activeConv.nicknames?.[partnerId] || '');
                      setShowNicknamePrompt(true);
                    }}
                    className="w-full px-3 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center space-x-2 text-slate-700 dark:text-slate-200"
                  >
                    <Edit3 className="w-4 h-4 text-blue-500" />
                    <span>Đặt biệt danh cho bạn chat</span>
                  </button>
                )}

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

                {isDirect && partnerId && !isFriend && !isSent && !isIncoming && (
                  <button
                    onClick={() => {
                      setShowMenu(false);
                      handleAddFriend();
                    }}
                    className="w-full px-3 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center space-x-2 text-slate-700 dark:text-slate-200"
                  >
                    <UserPlus className="w-4 h-4 text-[#2481cc]" />
                    <span>Thêm bạn bè</span>
                  </button>
                )}

                {isDirect && partnerId && (
                  <button
                    onClick={() => {
                      setShowMenu(false);
                      handleBlockUser();
                    }}
                    className="w-full px-3 py-2 text-left hover:bg-rose-50 dark:hover:bg-rose-500/10 flex items-center space-x-2 text-rose-600 dark:text-rose-400"
                  >
                    <Ban className="w-4 h-4 text-rose-500" />
                    <span>Chặn người dùng này</span>
                  </button>
                )}

                <div className="h-px bg-slate-100 dark:bg-slate-700/60 my-1" />

                <button
                  onClick={handleDeleteHistory}
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

      {/* Popout Chat Theme Modal */}
      <ChatThemeModal isOpen={showThemeModal} onClose={() => setShowThemeModal(false)} />

      {/* Prompt Set Nickname Modal */}
      {showNicknamePrompt && (
        <div
          onClick={() => setShowNicknamePrompt(false)}
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 select-none animate-in fade-in duration-150"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-sm bg-white dark:bg-[#17212b] border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl p-5 space-y-4 animate-in zoom-in-95 duration-150 text-xs"
          >
            <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center space-x-2 font-bold text-sm text-slate-800 dark:text-slate-100">
                <Edit3 className="w-4 h-4 text-[#2481cc]" />
                <span>Đặt biệt danh cho bạn chat</span>
              </div>
              <button
                onClick={() => setShowNicknamePrompt(false)}
                className="p-1 rounded-full text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-slate-500 dark:text-slate-400 text-xs leading-relaxed">
              Biệt danh sẽ hiển thị thay thế tên gốc của đối phương trong đoạn chat này:
            </p>

            <div>
              <label className="block font-semibold text-slate-700 dark:text-slate-200 mb-1.5">
                Biệt danh mới:
              </label>
              <input
                type="text"
                autoFocus
                value={nicknameInput}
                onChange={(e) => setNicknameInput(e.target.value)}
                placeholder="Nhập biệt danh (để trống nếu muốn xóa biệt danh)..."
                className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#202b36] text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-[#2481cc] border border-transparent dark:border-slate-700/60"
              />
            </div>

            <div className="flex items-center space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setShowNicknamePrompt(false)}
                className="flex-1 py-2.5 rounded-xl bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 font-semibold cursor-pointer"
              >
                Hủy bỏ
              </button>
              <button
                type="button"
                onClick={handleSaveNickname}
                className="flex-1 py-2.5 rounded-xl bg-[#2481cc] hover:bg-[#1b6ca8] text-white font-bold cursor-pointer transition-all active:scale-95 shadow-md shadow-blue-500/20"
              >
                Lưu Biệt Danh
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
