import React, { useState } from 'react';
import { X, Check, Sparkles, Upload } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { apiService } from '../../services/api';

interface ChatThemeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PRESET_THEMES = [
  { id: 'default', name: 'Mặc định', bgClass: 'bg-slate-50 dark:bg-[#0e1621]', preview: 'linear-gradient(to bottom right, #f8fafc, #0e1621)' },
  { id: 'ocean', name: 'Đại dương xanh', bgClass: 'bg-gradient-to-br from-cyan-950/40 via-blue-900/30 to-slate-900', preview: 'linear-gradient(135deg, #083344, #1e3a8a, #0f172a)' },
  { id: 'sunset', name: 'Hoàng hôn tím', bgClass: 'bg-gradient-to-br from-purple-950/40 via-pink-900/25 to-slate-900', preview: 'linear-gradient(135deg, #3b0764, #831843, #0f172a)' },
  { id: 'emerald', name: 'Rừng nhiệt đới', bgClass: 'bg-gradient-to-br from-emerald-950/40 via-teal-900/25 to-slate-900', preview: 'linear-gradient(135deg, #022c22, #134e4a, #0f172a)' },
  { id: 'amber', name: 'Cà phê ấm áp', bgClass: 'bg-gradient-to-br from-amber-950/40 via-orange-950/30 to-slate-900', preview: 'linear-gradient(135deg, #451a03, #431407, #0f172a)' },
  { id: 'neon_night', name: 'Đêm Neon Cyber', bgClass: 'bg-gradient-to-br from-indigo-950/50 via-slate-900 to-black', preview: 'linear-gradient(135deg, #1e1b4b, #0f172a, #000000)' },
  { id: 'rose', name: 'Hồng ngọt ngào', bgClass: 'bg-gradient-to-br from-rose-950/40 via-pink-950/30 to-slate-900', preview: 'linear-gradient(135deg, #4c0519, #500724, #0f172a)' },
];

export const ChatThemeModal: React.FC<ChatThemeModalProps> = ({ isOpen, onClose }) => {
  const { activeConv, currentUser, refreshConversations } = useChat();
  const [selectedTheme, setSelectedTheme] = useState<string>(activeConv?.theme || 'default');
  const [customBgUrl, setCustomBgUrl] = useState<string>('');
  const [isSaving, setIsSaving] = useState(false);
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);

  if (!isOpen || !activeConv || !currentUser) return null;

  const handleSelectTheme = (themeId: string) => {
    setSelectedTheme(themeId);
    setCustomBgUrl('');
  };

  const handleCustomImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      alert('Vui lòng chọn tệp hình ảnh hợp lệ (PNG, JPG, WEBP)!');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = reader.result as string;
      setCustomBgUrl(base64);
      setSelectedTheme('custom');
    };
    reader.readAsDataURL(file);
  };

  const handleSaveTheme = async () => {
    setIsSaving(true);
    try {
      const themeValue = selectedTheme === 'custom' ? customBgUrl : selectedTheme;
      const res = await apiService.updateConversationTheme(activeConv.id, currentUser.id, themeValue);
      if (res && res.success) {
        await refreshConversations();
        onClose();
      } else {
        alert(res?.error || 'Không thể đổi chủ đề cuộc trò chuyện!');
      }
    } catch (e: any) {
      alert(e.message || 'Lỗi kết nối máy chủ!');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 select-none animate-in fade-in duration-150"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-sm bg-white dark:bg-[#17212b] border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl flex flex-col overflow-hidden max-h-[85vh] animate-in zoom-in-95 duration-150"
      >
        {/* Header */}
        <div className="h-14 px-5 border-b border-slate-200 dark:border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-[#2481cc]" />
            <h3 className="font-bold text-base text-slate-800 dark:text-slate-100">
              Đổi giao diện đoạn chat
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 flex-1 overflow-y-auto space-y-4 text-xs">
          <p className="text-slate-500 dark:text-slate-400 text-xs">
            Chọn chủ đề màu sắc hoặc hình nền riêng cho cuộc trò chuyện này (áp dụng cho cả hai bên giống Messenger / Zalo):
          </p>

          {/* Grid preset themes */}
          <div className="grid grid-cols-2 gap-3">
            {PRESET_THEMES.map((th) => {
              const isSelected = selectedTheme === th.id;
              return (
                <div
                  key={th.id}
                  onClick={() => handleSelectTheme(th.id)}
                  className={`p-3 rounded-2xl border cursor-pointer transition-all flex flex-col space-y-2.5 relative group ${
                    isSelected
                      ? 'border-[#2481cc] ring-2 ring-blue-500/20 bg-blue-500/5'
                      : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                  }`}
                >
                  <div
                    className="w-full h-14 rounded-xl shadow-inner flex items-center justify-center relative overflow-hidden"
                    style={{ background: th.preview }}
                  >
                    {isSelected && (
                      <div className="w-6 h-6 rounded-full bg-[#2481cc] text-white flex items-center justify-center shadow-md">
                        <Check className="w-3.5 h-3.5 stroke-[3]" />
                      </div>
                    )}
                  </div>
                  <span className="font-semibold text-slate-800 dark:text-slate-200 text-center truncate">
                    {th.name}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Custom Background Image Upload */}
          <div className="pt-2 border-t border-slate-200/60 dark:border-slate-800/80">
            <input
              type="file"
              ref={fileInputRef}
              accept="image/*"
              onChange={handleCustomImageUpload}
              className="hidden"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-full py-2.5 px-3 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 hover:border-[#2481cc] dark:hover:border-[#2481cc] text-slate-600 dark:text-slate-300 flex items-center justify-center space-x-2 transition-colors cursor-pointer"
            >
              <Upload className="w-4 h-4 text-[#2481cc]" />
              <span>{customBgUrl ? 'Đã chọn ảnh tùy chỉnh (Bấm để đổi)' : 'Tải ảnh nền riêng từ máy tính'}</span>
            </button>
            {customBgUrl && (
              <div className="mt-2.5 h-16 rounded-xl overflow-hidden border border-[#2481cc] relative">
                <img src={customBgUrl} alt="Custom Theme" className="w-full h-full object-cover" />
                <span className="absolute bottom-1 right-2 px-1.5 py-0.5 rounded text-[9px] bg-black/60 text-white font-semibold">
                  Hình nền riêng
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800/80 bg-slate-50 dark:bg-[#1a232e] flex items-center space-x-2.5">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 font-semibold text-xs transition-colors cursor-pointer"
          >
            Hủy bỏ
          </button>
          <button
            type="button"
            disabled={isSaving}
            onClick={handleSaveTheme}
            className="flex-1 py-2.5 rounded-xl bg-[#2481cc] hover:bg-[#1b6ca8] text-white font-bold text-xs transition-all active:scale-95 disabled:opacity-50 shadow-md shadow-blue-500/20 cursor-pointer"
          >
            {isSaving ? 'Đang lưu...' : 'Áp Dụng Giao Diện'}
          </button>
        </div>
      </div>
    </div>
  );
};
