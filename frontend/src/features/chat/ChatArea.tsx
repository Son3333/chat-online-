import React, { useRef, useEffect, useState } from 'react';
import { MessageSquare, Pin, X } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { ChatHeader } from './ChatHeader';
import { ChatBubble } from './ChatBubble';
import { ChatComposer } from './ChatComposer';

export const ChatArea: React.FC = () => {
  const { activeConv, messages, currentUser, pinnedMessage } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [previewImage, setPreviewImage] = useState<{ fileId: string; name: string } | null>(null);

  // Auto scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // When no conversation is selected
  if (!activeConv) {
    return (
      <div className="flex-1 h-full flex flex-col items-center justify-center bg-slate-50 dark:bg-[#0e1621] p-6 text-center select-none">
        <div className="w-20 h-20 rounded-full bg-[#2481cc]/10 dark:bg-[#2481cc]/15 flex items-center justify-center text-[#2481cc] mb-4 shadow-inner">
          <MessageSquare className="w-10 h-10" />
        </div>
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
              onOpenImage={(fileId, name) => setPreviewImage({ fileId, name })}
            />
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* 4. Bottom Composer */}
      <ChatComposer />

      {/* 5. Fullscreen Image Preview Modal */}
      {previewImage && (
        <div
          onClick={() => setPreviewImage(null)}
          className="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-150"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="relative max-w-4xl max-h-[90vh] flex flex-col items-center"
          >
            <button
              onClick={() => setPreviewImage(null)}
              className="absolute -top-10 right-0 p-1.5 text-white/80 hover:text-white rounded-full bg-black/40 hover:bg-black/60"
            >
              <X className="w-5 h-5" />
            </button>
            <img
              src={`http://127.0.0.1:8888/uploads/${previewImage.fileId}`}
              alt={previewImage.name}
              className="max-h-[80vh] w-auto rounded-lg shadow-2xl object-contain"
            />
            <span className="mt-2 text-xs text-white/80 font-medium">{previewImage.name}</span>
          </div>
        </div>
      )}
    </div>
  );
};

