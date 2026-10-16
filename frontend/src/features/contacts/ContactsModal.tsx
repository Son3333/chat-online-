import React, { useState } from 'react';
import { X, Search, UserPlus, MessageCircle, Ban, Check, Users, UserMinus, UserCheck, Bell, Clock } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { apiService } from '../../services/api';
import { User, Friend } from '../../types';
import { getInitials } from '../../lib/utils';

interface ContactsModalProps {
  onClose: () => void;
}

export const ContactsModal: React.FC<ContactsModalProps> = ({ onClose }) => {
  const { friends, pendingFriends, sentFriendRequestIds, currentUser, refreshFriends, selectConversation, conversations, refreshConversations } = useChat();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [activeTab, setActiveTab] = useState<'friends' | 'requests' | 'search'>('friends');
  const [statusMsg, setStatusMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const handleSearch = async () => {
    if (!searchQuery.trim() || !currentUser) return;
    setIsSearching(true);
    setStatusMsg(null);
    try {
      const res = await apiService.searchUsers(searchQuery.trim(), currentUser.id);
      if (res && res.users) {
        setSearchResults(res.users.filter((u) => u.id !== currentUser.id));
      }
    } catch {
      setStatusMsg({ text: 'Lỗi tìm kiếm người dùng!', type: 'error' });
    } finally {
      setIsSearching(false);
    }
  };

  const handleSendFriendRequest = async (targetId: number) => {
    if (!currentUser) return;
    const res = await apiService.sendFriendRequest(currentUser.id, targetId);
    if (res && res.success) {
      setStatusMsg({ text: 'Đã gửi lời mời kết bạn thành công!', type: 'success' });
      await refreshFriends();
    } else {
      setStatusMsg({ text: res.error || res.message || 'Gửi lời mời thất bại!', type: 'error' });
    }
  };

  const handleAcceptRequest = async (requesterId: number) => {
    if (!currentUser) return;
    const res = await apiService.acceptFriendRequest(currentUser.id, requesterId);
    if (res && res.success) {
      setStatusMsg({ text: 'Đã chấp nhận lời mời kết bạn!', type: 'success' });
      await refreshFriends();
      await refreshConversations();
    } else {
      setStatusMsg({ text: res.error || 'Xử lý lời mời thất bại!', type: 'error' });
    }
  };

  const handleRejectRequest = async (requesterId: number) => {
    if (!currentUser) return;
    const res = await apiService.rejectFriendRequest(currentUser.id, requesterId);
    if (res && res.success) {
      setStatusMsg({ text: 'Đã từ chối lời mời kết bạn!', type: 'success' });
      await refreshFriends();
    } else {
      setStatusMsg({ text: res.error || 'Từ chối lời mời thất bại!', type: 'error' });
    }
  };

  const handleRemoveFriend = async (friendId: number) => {
    if (!currentUser) return;
    if (!confirm('Bạn có chắc chắn muốn hủy kết bạn với người này?')) return;
    const res = await apiService.removeFriend(currentUser.id, friendId);
    if (res && res.success) {
      setStatusMsg({ text: 'Đã hủy kết bạn thành công!', type: 'success' });
      await refreshFriends();
    }
  };

  const handleCancelFriendRequest = async (targetId: number) => {
    if (!currentUser) return;
    const res = await apiService.removeFriend(currentUser.id, targetId);
    if (res && res.success) {
      setStatusMsg({ text: 'Đã hủy lời mời kết bạn.', type: 'success' });
      await refreshFriends();
    } else {
      setStatusMsg({ text: (res as any)?.error || res?.message || 'Hủy lời mời thất bại!', type: 'error' });
    }
  };

  const handleBlockUser = async (targetId: number) => {
    if (!currentUser) return;
    if (!confirm('Bạn có chắc chắn muốn chặn người dùng này? Họ sẽ không thể nhắn tin cho bạn.')) return;
    const res = await apiService.blockUser(currentUser.id, targetId);
    if (res && res.success) {
      setStatusMsg({ text: 'Đã chặn người dùng thành công!', type: 'success' });
      await refreshFriends();
    }
  };

  const handleStartChat = async (friend: User | Friend) => {
    // Check if direct conversation already exists
    const existing = conversations.find((c) => c.partner_id === friend.id && c.type === 'direct');
    if (existing) {
      selectConversation(existing);
      onClose();
    } else {
      // Start or open direct chat
      if (currentUser) {
        const res = await apiService.sendRequest('start_direct_chat', {
          user_id: currentUser.id,
          target_id: friend.id,
        });
        if (res && res.success && res.conversation_id) {
          await refreshConversations();
          selectConversation({
            id: res.conversation_id,
            title: friend.full_name,
            type: 'direct',
            avatar_color: friend.avatar_color,
            partner_id: friend.id,
            is_online: friend.is_online,
          });
          onClose();
          return;
        }
      }

      // Fallback
      selectConversation({
        id: `direct_${friend.id}`,
        title: friend.full_name,
        type: 'direct',
        avatar_color: friend.avatar_color,
        partner_id: friend.id,
        is_online: friend.is_online,
      });
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 select-none">
      <div className="w-full max-w-lg bg-white dark:bg-[#17212b] border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl p-6 flex flex-col h-[540px] animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-[#2481cc]/15 text-[#2481cc] flex items-center justify-center">
              <Users className="w-4 h-4" />
            </div>
            <h2 className="font-bold text-sm text-slate-800 dark:text-slate-100">
              Danh Bạ & Kết Bạn Hai Chiều
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Status Alert */}
        {statusMsg && (
          <div
            className={`mt-3 p-2 rounded-xl text-xs text-center font-medium ${
              statusMsg.type === 'success'
                ? 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                : 'bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400'
            }`}
          >
            {statusMsg.text}
          </div>
        )}

        {/* 3 Tabs switch */}
        <div className="flex space-x-1.5 mt-3 p-1 bg-slate-100 dark:bg-[#242f3d] rounded-xl text-xs font-semibold">
          <button
            onClick={() => setActiveTab('friends')}
            className={`flex-1 py-1.5 rounded-lg transition-colors flex items-center justify-center space-x-1 ${
              activeTab === 'friends'
                ? 'bg-white dark:bg-[#17212b] text-[#2481cc] shadow-sm'
                : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            <span>Bạn Bè ({friends.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('requests')}
            className={`flex-1 py-1.5 rounded-lg transition-colors flex items-center justify-center space-x-1 relative ${
              activeTab === 'requests'
                ? 'bg-white dark:bg-[#17212b] text-[#2481cc] shadow-sm'
                : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            <Bell className="w-3.5 h-3.5" />
            <span>Lời Mời</span>
            {pendingFriends.length > 0 && (
              <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-red-500 text-white animate-pulse">
                {pendingFriends.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('search')}
            className={`flex-1 py-1.5 rounded-lg transition-colors flex items-center justify-center space-x-1 ${
              activeTab === 'search'
                ? 'bg-white dark:bg-[#17212b] text-[#2481cc] shadow-sm'
                : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            <Search className="w-3.5 h-3.5" />
            <span>Tìm Kiếm</span>
          </button>
        </div>

        {/* Tab 1: Friends List */}
        {activeTab === 'friends' && (
          <div className="flex-1 overflow-y-auto mt-3 space-y-1.5 pr-1">
            {friends.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-48 text-center text-slate-400 text-xs px-4">
                <Users className="w-8 h-8 mb-2 opacity-30" />
                <p>Bạn chưa có bạn bè nào trong danh bạ.</p>
                <p className="text-[11px] text-slate-500 mt-1">Chuyển sang tab "Tìm Kiếm" để kết nối với người dùng khác!</p>
              </div>
            ) : (
              friends.map((friend) => (
                <div
                  key={friend.id}
                  className="p-2.5 rounded-xl bg-slate-50 dark:bg-[#202b36] flex items-center justify-between text-xs hover:shadow-sm transition-all"
                >
                  <div className="flex items-center space-x-3">
                    <div className="relative">
                      <div
                        className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white text-xs shadow-sm overflow-hidden"
                        style={{ backgroundColor: friend.avatar_color || '#2563eb' }}
                      >
                        {friend.avatar_url ? (
                          <img src={friend.avatar_url} alt="" className="w-full h-full object-cover" />
                        ) : (
                          getInitials(friend.full_name)
                        )}
                      </div>
                      {Boolean(friend.is_online) && (
                        <span className="absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-white dark:border-[#202b36] bg-emerald-500" />
                      )}
                    </div>
                    <div>
                      <span className="font-semibold block text-slate-800 dark:text-slate-100">
                        {friend.full_name}
                      </span>
                      <div className="flex items-center space-x-1.5 text-slate-400 text-[11px]">
                        <span>@{friend.username} • #{friend.id}</span>
                        {friend.phone_number && (
                          <>
                            <span>•</span>
                            <span className="text-[#2481cc] font-medium font-mono">{friend.phone_number}</span>
                          </>
                        )}
                        <span>•</span>
                        <span className={friend.is_online ? 'text-emerald-500 font-medium' : 'text-slate-400'}>
                          {friend.is_online ? 'Trực tuyến' : 'Ngoại tuyến'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-1.5">
                    <button
                      onClick={() => handleStartChat(friend)}
                      title="Nhắn tin"
                      className="px-2.5 py-1.5 rounded-lg bg-[#2481cc] text-white hover:bg-[#1d73b8] transition-colors flex items-center space-x-1 font-medium"
                    >
                      <MessageCircle className="w-3.5 h-3.5" />
                      <span>Nhắn</span>
                    </button>
                    <button
                      onClick={() => handleRemoveFriend(friend.id)}
                      title="Hủy kết bạn"
                      className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700/60 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
                    >
                      <UserMinus className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleBlockUser(friend.id)}
                      title="Chặn người này"
                      className="p-2 rounded-lg hover:bg-red-500/10 text-slate-400 hover:text-red-500 transition-colors"
                    >
                      <Ban className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Tab 2: Pending Requests (Lời Mời Kết Bạn) */}
        {activeTab === 'requests' && (
          <div className="flex-1 overflow-y-auto mt-3 space-y-1.5 pr-1">
            {pendingFriends.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-48 text-center text-slate-400 text-xs px-4">
                <UserCheck className="w-8 h-8 mb-2 opacity-30" />
                <p>Không có lời mời kết bạn nào đang chờ phản hồi.</p>
              </div>
            ) : (
              pendingFriends.map((req) => (
                <div
                  key={req.id}
                  className="p-3 rounded-xl bg-slate-50 dark:bg-[#202b36] border border-slate-200/60 dark:border-slate-700/40 flex items-center justify-between text-xs"
                >
                  <div className="flex items-center space-x-3">
                    <div
                      className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white text-xs shadow-sm overflow-hidden"
                      style={{ backgroundColor: req.avatar_color || '#2563eb' }}
                    >
                      {req.avatar_url ? (
                        <img src={req.avatar_url} alt="" className="w-full h-full object-cover" />
                      ) : (
                        getInitials(req.full_name)
                      )}
                    </div>
                    <div>
                      <span className="font-semibold block text-slate-800 dark:text-slate-100">
                        {req.full_name}
                      </span>
                      <span className="text-slate-400 block text-[11px]">
                        @{req.username} • #{req.id}
                      </span>
                      <span className="text-indigo-500 text-[10px] font-medium block mt-0.5">
                        Đã gửi cho bạn lời mời kết bạn
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleAcceptRequest(req.id)}
                      className="px-3 py-1.5 rounded-lg bg-emerald-600 text-white font-semibold hover:bg-emerald-700 transition-colors flex items-center space-x-1 shadow-sm"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Đồng ý</span>
                    </button>
                    <button
                      onClick={() => handleRejectRequest(req.id)}
                      className="px-2.5 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-semibold hover:bg-red-50 dark:hover:bg-red-500/20 hover:text-red-600 transition-colors flex items-center space-x-1"
                    >
                      <X className="w-3.5 h-3.5" />
                      <span>Từ chối</span>
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Tab 3: Search Users */}
        {activeTab === 'search' && (
          <div className="flex-1 flex flex-col mt-3 overflow-hidden">
            <div className="flex items-center space-x-2 mb-3">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Nhập username, số điện thoại, ID hoặc họ tên..."
                className="flex-1 h-9 px-3 rounded-xl bg-slate-100 dark:bg-[#242f3d] text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-[#2481cc]"
              />
              <button
                onClick={handleSearch}
                disabled={isSearching}
                className="px-3 h-9 rounded-xl bg-[#2481cc] text-white text-xs font-semibold hover:bg-[#1d73b8] flex items-center space-x-1.5 disabled:opacity-50"
              >
                <Search className="w-3.5 h-3.5" />
                <span>{isSearching ? 'Đang tìm...' : 'Tìm'}</span>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
              {searchResults.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-10">
                  Nhập số điện thoại, tên tài khoản (@username), mã số (#ID) hoặc họ tên để tìm kiếm người dùng toàn hệ thống
                </p>
              ) : (
                searchResults.map((user) => {
                  const isFriend = friends.some((f) => f.id === user.id);
                  const isIncoming = pendingFriends.some((p) => p.id === user.id);
                  const isSent = sentFriendRequestIds.includes(user.id);

                  return (
                    <div
                      key={user.id}
                      className="p-2.5 rounded-xl bg-slate-50 dark:bg-[#202b36] flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="relative">
                          <div
                            className="w-9 h-9 rounded-full flex items-center justify-center font-bold text-white text-xs overflow-hidden"
                            style={{ backgroundColor: user.avatar_color || '#2563eb' }}
                          >
                            {user.avatar_url ? (
                              <img src={user.avatar_url} alt="" className="w-full h-full object-cover" />
                            ) : (
                              getInitials(user.full_name)
                            )}
                          </div>
                          {Boolean(user.is_online) && (
                            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-white dark:border-[#202b36] bg-emerald-500" />
                          )}
                        </div>
                        <div>
                          <span className="font-semibold block text-slate-800 dark:text-slate-100">
                            {user.full_name}
                          </span>
                          <div className="text-slate-400 flex items-center space-x-1.5 text-[11px]">
                            <span>@{user.username} • #{user.id}</span>
                            {user.phone_number && (
                              <>
                                <span>•</span>
                                <span className="text-[#2481cc] font-medium font-mono">{user.phone_number}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-1.5">
                        {isFriend ? (
                          <div className="flex items-center space-x-1">
                            <span className="px-2 py-1 rounded-lg bg-emerald-500/10 text-emerald-500 font-semibold flex items-center space-x-1">
                              <Check className="w-3 h-3" />
                              <span>Bạn bè</span>
                            </span>
                            <button
                              onClick={() => handleStartChat(user)}
                              className="px-2.5 py-1 rounded-lg bg-[#2481cc] text-white font-medium hover:bg-[#1d73b8]"
                            >
                              Nhắn tin
                            </button>
                            <button
                              onClick={() => handleRemoveFriend(user.id)}
                              title="Hủy kết bạn"
                              className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10"
                            >
                              <UserMinus className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ) : isIncoming ? (
                          <div className="flex items-center space-x-1">
                            <button
                              onClick={() => handleAcceptRequest(user.id)}
                              className="px-2.5 py-1 rounded-lg bg-emerald-600 text-white font-semibold hover:bg-emerald-700 flex items-center space-x-1"
                            >
                              <Check className="w-3.5 h-3.5" />
                              <span>Đồng ý</span>
                            </button>
                            <button
                              onClick={() => handleRejectRequest(user.id)}
                              className="px-2 py-1 rounded-lg bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-semibold hover:text-red-600 flex items-center space-x-1"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </div>
                        ) : isSent ? (
                          <button
                            onClick={() => handleCancelFriendRequest(user.id)}
                            title="Bấm để hủy lời mời kết bạn"
                            className="px-2.5 py-1 rounded-lg bg-amber-500/15 hover:bg-rose-500/15 text-amber-600 dark:text-amber-400 hover:text-rose-600 dark:hover:text-rose-400 border border-amber-500/25 hover:border-rose-500/30 font-semibold flex items-center space-x-1 cursor-pointer transition-all active:scale-95 group/btn"
                          >
                            <Clock className="w-3.5 h-3.5 group-hover/btn:hidden" />
                            <X className="w-3.5 h-3.5 hidden group-hover/btn:inline-block text-rose-500" />
                            <span className="group-hover/btn:hidden">Chờ duyệt</span>
                            <span className="hidden group-hover/btn:inline-block font-semibold">Hủy lời mời</span>
                          </button>
                        ) : (
                          <button
                            onClick={() => handleSendFriendRequest(user.id)}
                            className="px-3 py-1.5 rounded-lg bg-[#2481cc] text-white font-semibold hover:bg-[#1d73b8] flex items-center space-x-1"
                          >
                            <UserPlus className="w-3.5 h-3.5" />
                            <span>Kết bạn</span>
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
