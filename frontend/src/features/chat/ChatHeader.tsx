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
  Check,
  Clock,
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { apiService } from '../../services/api';
import { getInitials } from '../../lib/utils';
import { ChatInfoModal } from './ChatInfoModal';

export const ChatHeader: React.FC = () => {
  const {
    activeConv,
    messages,
    typingUser,
    startCall,
    friends,
    pendingFriends,
    sentFriendRequestIds,
    currentUser,
    refreshFriends,
    refreshConversations,
  } = useChat();
  const [showInfo, setShowInfo] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [showMenu, setShowMenu] = useState(false);
  const [isMuted, setIsMuted] = useState(false);

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
  const hasMessages = messages.length > 0;
  const canCall = isDirect && (isFriend || hasMessages);

  const handleAddFriend = async () => {
    if (!currentUser || !partnerId) return;
    const res = await apiService.sendFriendRequest(currentUser.id, partnerId);
    if (res && res.success) {
      await refreshFriends();
    }
  };

  const handleAcceptRequest = async () => {
    if (!currentUser || !partnerId) return;
    const res = await apiService.acceptFriendRequest(currentUser.id, partnerId);
    if (res && res.success) {
      await refreshFriends();
      await refreshConversations();
    }
  };

  const handleRejectRequest = async () => {
    if (!currentUser || !partnerId) return;
    const res = await apiService.rejectFriendRequest(currentUser.id, partnerId);
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
            className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white text-sm shadow-sm overflow-hidden"
            style={{ backgroundColor: activeConv.avatar_color || (isGroup ? '#06b6d4' : '#2481cc') }}
          >
            {activeConv.avatar_url && !isGroup ? (
              <img src={activeConv.avatar_url} alt="" className="w-full h-full object-cover" />
            ) : isGroup ? (
              <Users className="w-5 h-5" />
            ) : (
              getInitials(activeConv.title)
            )}
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

        {/* Right: Actions (Call or Friend/Block, Search, Menu) */}
        <div className="flex items-center space-x-1 relative">
          {isDirect && (
            <>
              {canCall ? (
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
              ) : (
                <div className="flex items-center space-x-1.5 mr-1">
                  {isSent ? (
                    <span className="px-2.5 py-1 text-xs rounded-lg bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/20 flex items-center space-x-1 font-medium select-none">
                      <Clock className="w-3.5 h-3.5" />
                      <span>Đã gửi lời mời</span>
                    </span>
                  ) : isIncoming ? (
                    <>
                      <button
                        onClick={handleAcceptRequest}
                        title="Đồng ý kết bạn"
                        className="px-2.5 py-1 text-xs rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors flex items-center space-x-1 font-medium cursor-pointer shadow-sm"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Đồng ý</span>
                      </button>
                      <button
                        onClick={handleRejectRequest}
                        title="Từ chối kết bạn"
                        className="px-2 py-1 text-xs rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors cursor-pointer"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={handleAddFriend}
                      title="Gửi lời mời kết bạn"
                      className="px-2.5 py-1 text-xs rounded-lg bg-[#2481cc] hover:bg-[#1b6ca8] text-white transition-colors flex items-center space-x-1 font-medium cursor-pointer shadow-sm"
                    >
                      <UserPlus className="w-3.5 h-3.5" />
                      <span>Kết bạn</span>
                    </button>
                  )}

                  <button
                    onClick={handleBlockUser}
                    title="Chặn người dùng này"
                    className="px-2.5 py-1 text-xs rounded-lg bg-rose-500/10 text-rose-600 dark:text-rose-400 hover:bg-rose-600 hover:text-white border border-rose-500/20 transition-colors flex items-center space-x-1 font-medium cursor-pointer"
                  >
                    <Ban className="w-3.5 h-3.5" />
                    <span>Chặn</span>
                  </button>
                </div>
              )}
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
    </>
  );
};
