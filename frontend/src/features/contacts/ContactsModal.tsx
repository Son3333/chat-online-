import React, { useState } from 'react';
import { X, Search, UserPlus, MessageCircle, Ban, Check, Users } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { apiService } from '../../services/api';
import { User } from '../../types';
import { getInitials } from '../../lib/utils';

interface ContactsModalProps {
  onClose: () => void;
}

export const ContactsModal: React.FC<ContactsModalProps> = ({ onClose }) => {
  const { friends, currentUser, refreshFriends, selectConversation, conversations } = useChat();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [activeTab, setActiveTab] = useState<'friends' | 'search'>('friends');
  const [statusMsg, setStatusMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    setStatusMsg(null);
    try {
      const res = await apiService.searchUsers(searchQuery.trim());
      if (res && res.users) {
        setSearchResults(res.users.filter((u) => u.id !== currentUser?.id));
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
      setStatusMsg({ text: res.error || 'Gửi lời mời thất bại!', type: 'error' });
    }
  };

  const handleBlockUser = async (targetId: number) => {
    if (!currentUser) return;
    const res = await apiService.blockUser(currentUser.id, targetId);
    if (res && res.success) {
      setStatusMsg({ text: 'Đã chặn người dùng thành công!', type: 'success' });
      await refreshFriends();
    }
  };

  const handleStartChat = async (friend: User) => {
    // Check if direct conversation already exists
    const existing = conversations.find((c) => c.partner_id === friend.id && c.type === 'direct');
    if (existing) {
      selectConversation(existing);
      onClose();
    } else {
      // Create a temporary conversation object to display
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
      <div className="w-full max-w-lg bg-white dark:bg-[#17212b] border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl p-6 flex flex-col h-[520px] animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-[#2481cc]/15 text-[#2481cc] flex items-center justify-center">
              <Users className="w-4 h-4" />
            </div>
            <h2 className="font-bold text-sm text-slate-800 dark:text-slate-100">
              Danh Bạ & Kết Bạn
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

        {/* Tab switch */}
        <div className="flex space-x-2 mt-3 p-1 bg-slate-100 dark:bg-[#242f3d] rounded-xl text-xs font-semibold">
          <button
            onClick={() => setActiveTab('friends')}
            className={`flex-1 py-1.5 rounded-lg transition-colors ${
              activeTab === 'friends'
                ? 'bg-white dark:bg-[#17212b] text-[#2481cc] shadow-sm'
                : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            Bạn Bè ({friends.length})
          </button>
          <button
            onClick={() => setActiveTab('search')}
            className={`flex-1 py-1.5 rounded-lg transition-colors ${
              activeTab === 'search'
                ? 'bg-white dark:bg-[#17212b] text-[#2481cc] shadow-sm'
                : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            Tìm Người Dùng Mới
          </button>
        </div>

        {/* Tab 1: Friends List */}
        {activeTab === 'friends' && (
          <div className="flex-1 overflow-y-auto mt-3 space-y-1.5 pr-1">
            {friends.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-10">
                Bạn chưa có người bạn nào trong danh bạ. Hãy chuyển sang tab "Tìm Người Dùng Mới" để kết bạn!
              </p>
            ) : (
              friends.map((friend) => (
                <div
                  key={friend.id}
                  className="p-2.5 rounded-xl bg-slate-50 dark:bg-[#202b36] flex items-center justify-between text-xs"
                >
                  <div className="flex items-center space-x-3">
                    <div
                      className="w-9 h-9 rounded-full flex items-center justify-center font-bold text-white text-xs"
                      style={{ backgroundColor: friend.avatar_color || '#2563eb' }}
                    >
                      {getInitials(friend.full_name)}
                    </div>
                    <div>
                      <span className="font-semibold block text-slate-800 dark:text-slate-100">
                        {friend.full_name}
                      </span>
                      <span className="text-slate-400 block text-[11px]">
                        @{friend.username} • #{friend.id}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-1.5">
                    <button
                      onClick={() => handleStartChat(friend)}
                      title="Nhắn tin"
                      className="p-2 rounded-lg bg-[#2481cc] text-white hover:bg-[#1d73b8] transition-colors"
                    >
                      <MessageCircle className="w-3.5 h-3.5" />
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

        {/* Tab 2: Search Users */}
        {activeTab === 'search' && (
          <div className="flex-1 flex flex-col mt-3 overflow-hidden">
            <div className="flex items-center space-x-2 mb-3">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Nhập @username hoặc ID..."
                className="flex-1 h-9 px-3 rounded-xl bg-slate-100 dark:bg-[#242f3d] text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-[#2481cc]"
              />
              <button
                onClick={handleSearch}
                disabled={isSearching}
                className="px-3 h-9 rounded-xl bg-[#2481cc] text-white text-xs font-semibold hover:bg-[#1d73b8] flex items-center space-x-1.5"
              >
                <Search className="w-3.5 h-3.5" />
                <span>Tìm</span>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
              {searchResults.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-10">
                  Nhập tên tài khoản hoặc mã ID người dùng để tìm kiếm
                </p>
              ) : (
                searchResults.map((user) => {
                  const isFriend = friends.some((f) => f.id === user.id);
                  return (
                    <div
                      key={user.id}
                      className="p-2.5 rounded-xl bg-slate-50 dark:bg-[#202b36] flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center space-x-3">
                        <div
                          className="w-9 h-9 rounded-full flex items-center justify-center font-bold text-white text-xs"
                          style={{ backgroundColor: user.avatar_color || '#2563eb' }}
                        >
                          {getInitials(user.full_name)}
                        </div>
                        <div>
                          <span className="font-semibold block text-slate-800 dark:text-slate-100">
                            {user.full_name}
                          </span>
                          <span className="text-slate-400 block text-[11px]">
                            @{user.username} • #{user.id}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-1.5">
                        {isFriend ? (
                          <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-500 font-semibold flex items-center space-x-1">
                            <Check className="w-3 h-3" />
                            <span>Bạn bè</span>
                          </span>
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
