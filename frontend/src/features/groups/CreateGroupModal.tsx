import React, { useState } from 'react';
import { X, Users, Check } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { apiService } from '../../services/api';
import { getInitials } from '../../lib/utils';

interface CreateGroupModalProps {
  onClose: () => void;
}

export const CreateGroupModal: React.FC<CreateGroupModalProps> = ({ onClose }) => {
  const { currentUser, friends, refreshConversations } = useChat();
  const [title, setTitle] = useState('');
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const toggleMember = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((mId) => mId !== id) : [...prev, id]
    );
  };

  const handleCreate = async () => {
    if (!title.trim()) {
      setErrorMsg('Vui lòng nhập tên nhóm!');
      return;
    }
    if (!currentUser) return;

    setLoading(true);
    try {
      const res = await apiService.createGroup(title.trim(), currentUser.id, selectedIds);
      if (res && res.success) {
        await refreshConversations();
        onClose();
      } else {
        setErrorMsg('Tạo nhóm thất bại!');
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Lỗi tạo nhóm!');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 select-none">
      <div className="w-full max-w-md bg-white dark:bg-[#17212b] border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl p-6 flex flex-col animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-[#2481cc]/15 text-[#2481cc] flex items-center justify-center">
              <Users className="w-4 h-4" />
            </div>
            <h2 className="font-bold text-sm text-slate-800 dark:text-slate-100">
              Tạo Nhóm Chat Mới
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {errorMsg && (
          <div className="mt-3 p-2 rounded-xl bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-600 dark:text-red-400 text-xs text-center font-medium">
            {errorMsg}
          </div>
        )}

        {/* Group Title input */}
        <div className="mt-4">
          <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
            Tên nhóm trò chuyện
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="vd: Nhóm Đồ Án Chuyên Ngành..."
            className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#242f3d] text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-[#2481cc]"
          />
        </div>

        {/* Member selector */}
        <div className="mt-4 flex-1 flex flex-col">
          <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-2">
            Chọn thành viên từ danh bạ ({selectedIds.length} đã chọn)
          </label>
          <div className="max-h-48 overflow-y-auto space-y-1 pr-1">
            {friends.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-4">
                Chưa có bạn bè nào trong danh bạ. Bạn vẫn có thể tạo nhóm và thêm thành viên sau.
              </p>
            ) : (
              friends.map((friend) => {
                const isSelected = selectedIds.includes(friend.id);
                return (
                  <div
                    key={friend.id}
                    onClick={() => toggleMember(friend.id)}
                    className={`p-2 rounded-xl flex items-center justify-between cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-[#2481cc]/15 text-[#2481cc]'
                        : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200'
                    }`}
                  >
                    <div className="flex items-center space-x-2.5">
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs text-white"
                        style={{ backgroundColor: friend.avatar_color || '#2563eb' }}
                      >
                        {getInitials(friend.full_name)}
                      </div>
                      <div className="flex flex-col text-xs">
                        <span className="font-semibold">{friend.full_name}</span>
                        <span className="text-[10px] opacity-70">@{friend.username}</span>
                      </div>
                    </div>
                    <div
                      className={`w-5 h-5 rounded-md border flex items-center justify-center transition-colors ${
                        isSelected
                          ? 'bg-[#2481cc] border-[#2481cc] text-white'
                          : 'border-slate-300 dark:border-slate-700'
                      }`}
                    >
                      {isSelected && <Check className="w-3.5 h-3.5" />}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Submit */}
        <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800 flex justify-end space-x-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            Hủy
          </button>
          <button
            onClick={handleCreate}
            disabled={loading}
            className="px-4 py-2 rounded-xl bg-[#2481cc] hover:bg-[#1d73b8] text-white text-xs font-semibold shadow-md shadow-[#2481cc]/25 disabled:opacity-50"
          >
            {loading ? 'Đang tạo...' : 'Tạo Nhóm'}
          </button>
        </div>
      </div>
    </div>
  );
};

