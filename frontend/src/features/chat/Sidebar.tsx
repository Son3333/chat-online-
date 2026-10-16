import React, { useState, useMemo, useEffect } from 'react';
import { Search, Plus, Cloud, Users, User as UserIcon, LogOut, Shield, MessageCircle, Pin, Archive, Ban, Trash2 } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { getInitials, formatDate } from '../../lib/utils';
import { apiService } from '../../services/api';
import { User, Conversation } from '../../types';

interface SidebarProps {
  onOpenCreateGroup: () => void;
  onOpenContacts: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onOpenCreateGroup, onOpenContacts }) => {
  const {
    currentUser,
    conversations,
    activeConv,
    selectConversation,
    openSavedMessages,
    logout,
    setIsLocked,
    refreshConversations,
    pendingFriends,
    refreshFriends,
  } = useChat();

  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'all' | 'direct' | 'group' | 'archived'>('all');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [globalUsers, setGlobalUsers] = useState<User[]>([]);
  const [isSearchingUsers, setIsSearchingUsers] = useState(false);

  // Pinned & Archived conversations from localStorage
  const [pinnedConvIds, setPinnedConvIds] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem('vibe_pinned_conversations');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [archivedConvIds, setArchivedConvIds] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem('vibe_archived_conversations');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Context Menu state
  const [convContextMenu, setConvContextMenu] = useState<{ x: number; y: number; conv: Conversation } | null>(null);

  const savePinned = (ids: string[]) => {
    setPinnedConvIds(ids);
    localStorage.setItem('vibe_pinned_conversations', JSON.stringify(ids));
  };

  const saveArchived = (ids: string[]) => {
    setArchivedConvIds(ids);
    localStorage.setItem('vibe_archived_conversations', JSON.stringify(ids));
  };

  const handleTogglePin = (convId: string | number) => {
    const sId = String(convId);
    if (pinnedConvIds.includes(sId)) {
      savePinned(pinnedConvIds.filter((id) => id !== sId));
    } else {
      savePinned([...pinnedConvIds, sId]);
    }
    setConvContextMenu(null);
  };

  const handleToggleArchive = (convId: string | number) => {
    const sId = String(convId);
    if (archivedConvIds.includes(sId)) {
      saveArchived(archivedConvIds.filter((id) => id !== sId));
    } else {
      saveArchived([...archivedConvIds, sId]);
    }
    setConvContextMenu(null);
  };

  const handleBlockUser = async (partnerId?: number | null) => {
    if (!currentUser || !partnerId) return;
    if (confirm('Bạn có chắc chắn muốn chặn người dùng này?')) {
      await apiService.blockUser(currentUser.id, partnerId);
      await refreshFriends();
      await refreshConversations();
    }
    setConvContextMenu(null);
  };

  const handleDeleteConversation = async (convId: string | number) => {
    if (!currentUser) return;
    if (confirm('Bạn có chắc chắn muốn xóa cuộc trò chuyện này? Toàn bộ tin nhắn sẽ bị xóa.')) {
      await apiService.deleteConversation(convId, currentUser.id);
      await refreshConversations();
    }
    setConvContextMenu(null);
  };

  // Debounced global user search
  useEffect(() => {
    const trimmed = searchQuery.trim();
    if (!trimmed) {
      setGlobalUsers([]);
      return;
    }
    const timer = setTimeout(async () => {
      setIsSearchingUsers(true);
      try {
        const res = await apiService.searchUsers(trimmed, currentUser?.id);
        if (res && res.success && res.users) {
          setGlobalUsers(res.users.filter((u) => u.id !== currentUser?.id));
        } else {
          setGlobalUsers([]);
        }
      } catch {
        setGlobalUsers([]);
      } finally {
        setIsSearchingUsers(false);
      }
    }, 200);
    return () => clearTimeout(timer);
  }, [searchQuery, currentUser?.id]);

  const handleStartChatWithUser = async (u: User) => {
    if (!currentUser) return;
    const res = await apiService.sendRequest('start_direct_chat', {
      user_id: currentUser.id,
      target_id: u.id,
    });
    if (res && res.success && res.conversation_id) {
      await refreshConversations();
      selectConversation({
        id: res.conversation_id,
        title: u.full_name,
        type: 'direct',
        avatar_color: u.avatar_color,
        partner_id: u.id,
        is_online: u.is_online,
      });
      setSearchQuery('');
    }
  };

  // Filter conversations
  const filteredConversations = useMemo(() => {
    let list = conversations.filter((c) => {
      const isArchived = archivedConvIds.includes(String(c.id));

      if (activeTab === 'archived') {
        if (!isArchived) return false;
      } else {
        if (isArchived) return false;
        if (activeTab === 'direct' && c.type !== 'direct') return false;
        if (activeTab === 'group' && c.type !== 'group') return false;
      }

      // Search filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchTitle = c.title.toLowerCase().includes(q);
        const matchLastMsg = c.last_message?.content?.toLowerCase().includes(q);
        return matchTitle || matchLastMsg;
      }
      return true;
    });

    // Sort pinned conversations to the top
    if (activeTab !== 'archived') {
      list = [...list].sort((a, b) => {
        const aPinned = pinnedConvIds.includes(String(a.id));
        const bPinned = pinnedConvIds.includes(String(b.id));
        if (aPinned && !bPinned) return -1;
        if (!aPinned && bPinned) return 1;
        return 0;
      });
    }

    return list;
  }, [conversations, activeTab, searchQuery, pinnedConvIds, archivedConvIds]);

  return (
    <aside className="w-[320px] h-full flex flex-col bg-white dark:bg-[#17212b] border-r border-slate-200 dark:border-slate-800/80 flex-shrink-0 select-none">
      {/* Top Header / Profile */}
      <div className="p-3 border-b border-slate-100 dark:border-slate-800/60 flex items-center justify-between relative">
        <div className="flex items-center space-x-2.5">
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-sm"
            style={{ backgroundColor: currentUser?.avatar_color || '#2481cc' }}
          >
            {getInitials(currentUser?.full_name)}
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-sm text-slate-800 dark:text-slate-100 leading-tight">
              {currentUser?.full_name || 'Người dùng'}
            </span>
            <span className="text-xs text-emerald-500 font-medium">
              @{currentUser?.username || 'user'} • #{currentUser?.id}
            </span>
          </div>
        </div>

        {/* User Menu Trigger */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
          >
            <div className="flex flex-col space-y-1">
              <span className="w-4 h-0.5 bg-current rounded-full" />
              <span className="w-4 h-0.5 bg-current rounded-full" />
              <span className="w-4 h-0.5 bg-current rounded-full" />
            </div>
          </button>

          {/* Dropdown Menu */}
          {showUserMenu && (
            <div className="absolute right-0 top-10 w-48 bg-white dark:bg-[#1e2c3a] border border-slate-200 dark:border-slate-700/80 rounded-xl shadow-xl py-1 z-50 animate-in fade-in zoom-in-95 duration-100">
              <button
                onClick={() => {
                  setShowUserMenu(false);
                  onOpenContacts();
                }}
                className="w-full px-3 py-2 text-left text-xs text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center justify-between"
              >
                <div className="flex items-center space-x-2">
                  <Users className="w-4 h-4 text-[#2481cc]" />
                  <span>Danh bạ & Bạn bè</span>
                </div>
                {pendingFriends.length > 0 && (
                  <span className="px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-red-500 text-white">
                    {pendingFriends.length}
                  </span>
                )}
              </button>

              <button
                onClick={() => {
                  setShowUserMenu(false);
                  openSavedMessages();
                }}
                className="w-full px-3 py-2 text-left text-xs text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center space-x-2"
              >
                <Cloud className="w-4 h-4 text-indigo-500" />
                <span>Cloud của tôi</span>
              </button>

              <button
                onClick={() => {
                  setShowUserMenu(false);
                  setIsLocked(true);
                }}
                className="w-full px-3 py-2 text-left text-xs text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center space-x-2"
              >
                <Shield className="w-4 h-4 text-amber-500" />
                <span>Khóa màn hình</span>
              </button>

              <div className="w-full h-px bg-slate-200 dark:bg-slate-700/60 my-1" />

              <button
                onClick={() => {
                  setShowUserMenu(false);
                  logout();
                }}
                className="w-full px-3 py-2 text-left text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 flex items-center space-x-2"
              >
                <LogOut className="w-4 h-4" />
                <span>Đăng xuất</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Search Input */}
      <div className="p-3 pb-2">
        <div className="relative flex items-center">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm kiếm @user hoặc #ID..."
            className="w-full h-9 pl-9 pr-3 rounded-lg bg-slate-100 dark:bg-[#242f3d] text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-[#2481cc] transition-all"
          />
        </div>
      </div>

      {/* Action shortcuts: New Group, Contacts & Saved Cloud */}
      <div className="px-3 py-1 flex space-x-1.5">
        <button
          onClick={onOpenCreateGroup}
          title="Tạo nhóm trò chuyện mới"
          className="flex-1 py-1.5 px-1.5 rounded-lg bg-[#2481cc]/10 dark:bg-[#2481cc]/15 text-[#2481cc] hover:bg-[#2481cc]/20 text-[11px] font-semibold flex items-center justify-center space-x-1 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Tạo Nhóm</span>
        </button>

        <button
          onClick={onOpenContacts}
          title="Danh bạ & Lời mời kết bạn"
          className="flex-1 py-1.5 px-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-900/50 text-[11px] font-semibold flex items-center justify-center space-x-1 transition-colors relative"
        >
          <Users className="w-3.5 h-3.5" />
          <span>Danh Bạ</span>
          {pendingFriends.length > 0 && (
            <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-500 text-white text-[9px] font-bold flex items-center justify-center animate-pulse">
              {pendingFriends.length}
            </span>
          )}
        </button>

        <button
          onClick={openSavedMessages}
          title="Cloud lưu trữ tin nhắn cá nhân"
          className="flex-1 py-1.5 px-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 text-[11px] font-semibold flex items-center justify-center space-x-1 transition-colors"
        >
          <Cloud className="w-3.5 h-3.5" />
          <span>Cloud</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex px-3 pt-2 pb-1 space-x-1 border-b border-slate-100 dark:border-slate-800/60 text-xs font-medium">
        <button
          onClick={() => setActiveTab('all')}
          className={`flex-1 pb-1.5 border-b-2 text-center transition-colors ${
            activeTab === 'all'
              ? 'border-[#2481cc] text-[#2481cc] font-semibold'
              : 'border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
          }`}
        >
          Tất cả
        </button>
        <button
          onClick={() => setActiveTab('direct')}
          className={`flex-1 pb-1.5 border-b-2 text-center transition-colors ${
            activeTab === 'direct'
              ? 'border-[#2481cc] text-[#2481cc] font-semibold'
              : 'border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
          }`}
        >
          Cá nhân
        </button>
        <button
          onClick={() => setActiveTab('group')}
          className={`flex-1 pb-1.5 border-b-2 text-center transition-colors ${
            activeTab === 'group'
              ? 'border-[#2481cc] text-[#2481cc] font-semibold'
              : 'border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
          }`}
        >
          Nhóm
        </button>
        {archivedConvIds.length > 0 && (
          <button
            onClick={() => setActiveTab('archived')}
            className={`pb-1.5 px-1 border-b-2 text-center transition-colors flex items-center space-x-1 ${
              activeTab === 'archived'
                ? 'border-amber-500 text-amber-500 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
            }`}
          >
            <Archive className="w-3 h-3" />
            <span>({archivedConvIds.length})</span>
          </button>
        )}
      </div>

      {/* Conversations Scroll List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {filteredConversations.length === 0 && globalUsers.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-center text-slate-400 text-xs px-4">
            <UserIcon className="w-8 h-8 mb-2 opacity-40" />
            <span>
              {activeTab === 'archived'
                ? 'Không có cuộc trò chuyện nào trong kho lưu trữ'
                : 'Không tìm thấy cuộc trò chuyện nào'}
            </span>
          </div>
        ) : (
          filteredConversations.map((conv) => {
            const isSelected = activeConv?.id === conv.id;
            const isOnline = Boolean(conv.is_online);
            const isGroup = conv.type === 'group';
            const isPinned = pinnedConvIds.includes(String(conv.id));

            return (
              <div
                key={conv.id}
                onClick={() => selectConversation(conv)}
                onContextMenu={(e) => {
                  e.preventDefault();
                  setConvContextMenu({ x: e.clientX, y: e.clientY, conv });
                }}
                className={`p-2.5 rounded-xl flex items-center space-x-3 cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-[#2481cc] text-white'
                    : 'hover:bg-slate-100 dark:hover:bg-[#202b36] text-slate-800 dark:text-slate-200'
                }`}
              >
                {/* Avatar */}
                <div className="relative flex-shrink-0">
                  <div
                    className="w-11 h-11 rounded-full flex items-center justify-center font-bold text-sm text-white shadow-sm"
                    style={{ backgroundColor: conv.avatar_color || (isGroup ? '#06b6d4' : '#2563eb') }}
                  >
                    {isGroup ? <Users className="w-5 h-5" /> : getInitials(conv.title)}
                  </div>
                  {!isGroup && isOnline && (
                    <span
                      className={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 ${
                        isSelected ? 'border-[#2481cc]' : 'border-white dark:border-[#17212b]'
                      } bg-emerald-500`}
                    />
                  )}
                </div>

                {/* Info Text */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-1.5 truncate">
                      <span className="font-semibold text-xs truncate leading-tight">
                        {conv.title}
                      </span>
                      {isPinned && (
                        <Pin className={`w-3 h-3 flex-shrink-0 ${isSelected ? 'text-white' : 'text-amber-500'}`} />
                      )}
                    </div>
                    {conv.last_message?.created_at && (
                      <span
                        className={`text-[10px] ${
                          isSelected ? 'text-white/80' : 'text-slate-400 dark:text-slate-500'
                        }`}
                      >
                        {formatDate(conv.last_message.created_at)}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center justify-between mt-1">
                    <p
                      className={`text-xs truncate ${
                        isSelected ? 'text-white/90' : 'text-slate-500 dark:text-slate-400'
                      }`}
                    >
                      {conv.last_message?.sender_name ? `${conv.last_message.sender_name}: ` : ''}
                      {conv.last_message?.content || 'Chưa có tin nhắn'}
                    </p>
                    {Boolean(conv.unread_count && conv.unread_count > 0) && (
                      <span className="ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-[#2481cc] text-white">
                        {conv.unread_count}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}

        {/* Global User Search Results */}
        {searchQuery.trim() && globalUsers.length > 0 && (
          <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800/80">
            <div className="px-2 pb-1.5 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider flex items-center justify-between">
              <span>Người dùng tìm thấy ({globalUsers.length})</span>
              {isSearchingUsers && <span className="text-[#2481cc] normal-case animate-pulse">Đang tìm...</span>}
            </div>
            {globalUsers.map((u) => (
              <div
                key={u.id}
                onClick={() => handleStartChatWithUser(u)}
                className="p-2.5 rounded-xl flex items-center justify-between hover:bg-slate-100 dark:hover:bg-[#202b36] cursor-pointer transition-colors group mb-1"
              >
                <div className="flex items-center space-x-2.5 overflow-hidden">
                  <div
                    className="w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs text-white shadow-sm flex-shrink-0"
                    style={{ backgroundColor: u.avatar_color || '#2563eb' }}
                  >
                    {getInitials(u.full_name)}
                  </div>
                  <div className="flex flex-col truncate">
                    <span className="font-semibold text-xs text-slate-800 dark:text-slate-100 truncate">
                      {u.full_name}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      @{u.username} • #{u.id}
                    </span>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleStartChatWithUser(u);
                  }}
                  className="px-2 py-1 rounded-lg bg-[#2481cc]/15 text-[#2481cc] hover:bg-[#2481cc] hover:text-white text-xs font-semibold transition-colors flex items-center space-x-1 flex-shrink-0"
                >
                  <MessageCircle className="w-3.5 h-3.5" />
                  <span>Nhắn tin</span>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Right-click Conversation Context Menu */}
      {convContextMenu && (
        <>
          <div className="fixed inset-0 z-50" onClick={() => setConvContextMenu(null)} />
          <div
            style={{
              top: `${Math.min(convContextMenu.y, window.innerHeight - 220)}px`,
              left: `${Math.min(convContextMenu.x, window.innerWidth - 200)}px`,
            }}
            className="fixed w-48 bg-white dark:bg-[#1e2c3a] border border-slate-200 dark:border-slate-700/80 rounded-xl shadow-2xl py-1 z-50 text-xs text-slate-700 dark:text-slate-200 animate-in fade-in zoom-in-95 duration-100"
          >
            {/* Ghim / Bỏ ghim */}
            <button
              onClick={() => handleTogglePin(convContextMenu.conv.id)}
              className="w-full px-3 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center space-x-2"
            >
              <Pin className="w-3.5 h-3.5 text-amber-500" />
              <span>
                {pinnedConvIds.includes(String(convContextMenu.conv.id)) ? 'Bỏ ghim hội thoại' : 'Ghim lên đầu'}
              </span>
            </button>

            {/* Lưu trữ / Bỏ lưu trữ */}
            <button
              onClick={() => handleToggleArchive(convContextMenu.conv.id)}
              className="w-full px-3 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center space-x-2"
            >
              <Archive className="w-3.5 h-3.5 text-blue-500" />
              <span>
                {archivedConvIds.includes(String(convContextMenu.conv.id))
                  ? 'Bỏ khỏi kho lưu trữ'
                  : 'Ẩn vào kho lưu trữ'}
              </span>
            </button>

            {/* Chặn người dùng nếu là chat cá nhân 1-1 */}
            {convContextMenu.conv.type === 'direct' && convContextMenu.conv.partner_id && (
              <button
                onClick={() => handleBlockUser(convContextMenu.conv.partner_id)}
                className="w-full px-3 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center space-x-2 text-amber-600 dark:text-amber-400"
              >
                <Ban className="w-3.5 h-3.5" />
                <span>Chặn người dùng này</span>
              </button>
            )}

            <div className="w-full h-px bg-slate-200 dark:bg-slate-700/60 my-1" />

            {/* Xóa cuộc trò chuyện */}
            <button
              onClick={() => handleDeleteConversation(convContextMenu.conv.id)}
              className="w-full px-3 py-2 text-left text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 flex items-center space-x-2"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Xóa cuộc trò chuyện</span>
            </button>
          </div>
        </>
      )}
    </aside>
  );
};
