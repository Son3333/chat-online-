import React, { useState, useMemo } from 'react';
import { Search, Plus, Cloud, Users, User as UserIcon, LogOut, Shield } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { getInitials, formatDate } from '../../lib/utils';

interface SidebarProps {
  onOpenCreateGroup: () => void;
  onOpenContacts: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onOpenCreateGroup, onOpenContacts }) => {
  const { currentUser, conversations, activeConv, selectConversation, openSavedMessages, logout, setIsLocked } = useChat();
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'all' | 'direct' | 'group'>('all');
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Filter conversations
  const filteredConversations = useMemo(() => {
    return conversations.filter((c) => {
      // Tab filter
      if (activeTab === 'direct' && c.type !== 'direct') return false;
      if (activeTab === 'group' && c.type !== 'group') return false;

      // Search filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchTitle = c.title.toLowerCase().includes(q);
        const matchLastMsg = c.last_message?.content?.toLowerCase().includes(q);
        return matchTitle || matchLastMsg;
      }
      return true;
    });
  }, [conversations, activeTab, searchQuery]);

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
                className="w-full px-3 py-2 text-left text-xs text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center space-x-2"
              >
                <Users className="w-4 h-4 text-[#2481cc]" />
                <span>Danh bạ & Bạn bè</span>
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

      {/* Action shortcuts: New Group & Saved Cloud */}
      <div className="px-3 py-1 flex space-x-1.5">
        <button
          onClick={onOpenCreateGroup}
          className="flex-1 py-1.5 px-2 rounded-lg bg-[#2481cc]/10 dark:bg-[#2481cc]/15 text-[#2481cc] hover:bg-[#2481cc]/20 text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Tạo Nhóm</span>
        </button>

        <button
          onClick={openSavedMessages}
          className="flex-1 py-1.5 px-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors"
        >
          <Cloud className="w-3.5 h-3.5" />
          <span>Cloud Cá Nhân</span>
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
      </div>

      {/* Conversations Scroll List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {filteredConversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-center text-slate-400 text-xs px-4">
            <UserIcon className="w-8 h-8 mb-2 opacity-40" />
            <span>Không tìm thấy cuộc trò chuyện nào</span>
          </div>
        ) : (
          filteredConversations.map((conv) => {
            const isSelected = activeConv?.id === conv.id;
            const isOnline = Boolean(conv.is_online);
            const isGroup = conv.type === 'group';

            return (
              <div
                key={conv.id}
                onClick={() => selectConversation(conv)}
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
                    <span className="font-semibold text-xs truncate leading-tight">
                      {conv.title}
                    </span>
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
      </div>
    </aside>
  );
};
