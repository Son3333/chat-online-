import React, { useRef, useEffect, useState } from 'react';
import { Pin, X, Download, MessageCircle } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { apiService } from '../../services/api';
import APP_LOGO from '../../assets/logo';
import { ChatHeader } from './ChatHeader';
import { ChatBubble } from './ChatBubble';
import { ChatComposer } from './ChatComposer';

export const ChatArea: React.FC = () => {
  const { activeConv, messages, currentUser, pinnedMessage } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [previewImage, setPreviewImage] = useState<{ fileId: string; name: string; url?: string } | null>(null);
  const [logoError, setLogoError] = useState(false);

  // Auto scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // When no conversation is selected
  if (!activeConv) {
    return (
      <div className="flex-1 h-full flex flex-col items-center justify-center bg-slate-50 dark:bg-[#0e1621] p-6 text-center select-none">
        {logoError ? (
          <div className="w-24 h-24 rounded-2xl bg-gradient-to-tr from-[#2481cc] to-indigo-600 flex items-center justify-center text-white shadow-xl mb-4 border-2 border-blue-400">
            <MessageCircle className="w-12 h-12" />
          </div>
        ) : (
          <img
            src={APP_LOGO}
            alt="Vibe Người Tốt Logo"
            onError={() => setLogoError(true)}
            className="w-24 h-24 rounded-2xl object-cover mb-4 shadow-xl border-2 border-amber-300 dark:border-amber-400 bg-amber-300 animate-in zoom-in-95 duration-200"
          />
        )}
        <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-1">
          Chào mừng đến với Vibe Người Tốt!
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm">
          Chọn một cuộc trò chuyện ở danh sách bên trái hoặc nhấn vào "Tạo Nhóm" để bắt đầu nhắn tin an toàn, tốc độ cao.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 h-full flex flex-col bg-slate-50 dark:bg-[#0e1621] relative overflow-hidden">
      {/* 1. Header */}
      <ChatHeader />

      {/* 2. Pinned Message Banner */}
      {pinnedMessage && (
        <div className="h-10 px-4 bg-slate-100 dark:bg-[#1a2530] border-b border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs animate-in slide-in-from-top-1 duration-150 select-none">
          <div className="flex items-center space-x-2 truncate">
            <Pin className="w-3.5 h-3.5 text-[#2481cc] rotate-45 flex-shrink-0" />
            <span className="font-semibold text-[#2481cc]">Tin nhắn đã ghim:</span>
            <span className="truncate text-slate-600 dark:text-slate-300">
              {pinnedMessage.content || pinnedMessage.original_name}
            </span>
          </div>
        </div>
      )}

      {/* 3. Messages List */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col space-y-1">
        {messages.map((msg) => {
          const isSelf = msg.sender_id === currentUser?.id;
          return (
            <ChatBubble
              key={msg.id}
              message={msg}
              isSelf={isSelf}
              onOpenImage={(fileId, name, dataUrl) => setPreviewImage({ fileId, name, url: dataUrl })}
            />
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* 4. Bottom Composer */}
      <ChatComposer />

      {/* 5. Fullscreen Image Preview Modal */}
      {previewImage && (
        <FullscreenPreviewModal
          fileId={previewImage.fileId}
          name={previewImage.name}
          initialUrl={previewImage.url}
          onClose={() => setPreviewImage(null)}
        />
      )}
    </div>
  );
};

const FullscreenPreviewModal: React.FC<{
  fileId: string;
  name: string;
  initialUrl?: string;
  onClose: () => void;
}> = ({ fileId, name, initialUrl, onClose }) => {
  const [url, setUrl] = useState<string | null>(initialUrl || null);
  const [loading, setLoading] = useState(!initialUrl);

  useEffect(() => {
    if (!url) {
      apiService.getImageUrl(fileId).then((loaded) => {
        setUrl(loaded);
        setLoading(false);
      });
    }
  }, [fileId, url]);

  const handleDownload = async () => {
    const res = await apiService.downloadFile(fileId);
    if (res && res.file_data) {
      await apiService.saveDownloadedFile(name || 'image.png', res.file_data);
    }
  };

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-150 select-none"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative max-w-5xl max-h-[92vh] flex flex-col items-center"
      >
        <div className="absolute -top-11 right-0 flex items-center space-x-2">
          <button
            onClick={handleDownload}
            className="p-2 text-white/80 hover:text-white rounded-full bg-white/10 hover:bg-white/20 transition-colors"
            title="Tải ảnh về máy"
          >
            <Download className="w-5 h-5" />
          </button>
          <button
            onClick={onClose}
            className="p-2 text-white/80 hover:text-white rounded-full bg-white/10 hover:bg-white/20 transition-colors"
            title="Đóng"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {loading ? (
          <div className="p-12 flex flex-col items-center justify-center text-white/70">
            <div className="w-10 h-10 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin mb-3" />
            <span className="text-xs">Đang tải hình ảnh...</span>
          </div>
        ) : url ? (
          <img
            src={url}
            alt={name}
            className="max-h-[82vh] w-auto max-w-full rounded-2xl shadow-2xl object-contain border border-white/10"
          />
        ) : (
          <div className="p-12 text-center text-white/70 text-xs">
            Không thể tải được hình ảnh này.
          </div>
        )}

        <div className="mt-3 px-4 py-1.5 rounded-full bg-black/60 border border-white/10 text-xs text-white/90 font-medium">
          {name}
        </div>
      </div>
    </div>
  );
};

