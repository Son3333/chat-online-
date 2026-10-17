import React, { useState, useRef, useEffect } from 'react';
import { Paperclip, Smile, Send, X, MapPin, Image as ImageIcon, Video, FileText, Loader2 } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { EmojiPicker } from '../../components/EmojiPicker';
import { apiService } from '../../services/api';
import { LocationModal } from './LocationModal';

export const ChatComposer: React.FC = () => {
  const { replyTo, setReplyTo, sendMessage, activeConv, currentUser } = useChat();
  const [text, setText] = useState('');
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [showAttachMenu, setShowAttachMenu] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  const lastTypingRef = useRef<number>(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const attachMenuRef = useRef<HTMLDivElement>(null);
  const [activeCategory, setActiveCategory] = useState<'image' | 'video' | 'file'>('file');

  useEffect(() => {
    inputRef.current?.focus();
  }, [activeConv, replyTo]);

  // Click outside to close attachment menu
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (attachMenuRef.current && !attachMenuRef.current.contains(e.target as Node)) {
        setShowAttachMenu(false);
      }
    };
    if (showAttachMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showAttachMenu]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    } else {
      handleTypingNotification();
    }
  };

  const handleTypingNotification = () => {
    const now = Date.now();
    if (now - lastTypingRef.current > 2500 && activeConv && currentUser) {
      lastTypingRef.current = now;
      apiService.sendTyping(activeConv.id, currentUser.id, currentUser.full_name);
    }
  };

  const handleSend = async () => {
    if (!text.trim() || isSending) return;
    setIsSending(true);
    const sent = await sendMessage(text.trim(), 'text');
    if (sent) {
      setText('');
      setShowEmojiPicker(false);
    }
    setIsSending(false);
  };

  const handleShareLocation = () => {
    if (!activeConv || !currentUser) return;
    setShowLocationModal(true);
  };

  const processFileAttachment = async (
    fileName: string,
    base64Data: string,
    fileSize: number,
    enforcedType?: 'image' | 'video' | 'file'
  ) => {
    if (!activeConv || !currentUser) return;

    if (fileSize > 40 * 1024 * 1024) {
      alert('Tệp tin vượt quá giới hạn 40MB. Vui lòng chọn tệp nhỏ hơn.');
      return;
    }

    setIsSending(true);
    setUploadStatus('Đang chuẩn bị tệp...');

    try {
      const isImg =
        enforcedType === 'image' ||
        (enforcedType !== 'file' &&
          enforcedType !== 'video' &&
          /\.(png|jpe?g|gif|webp|bmp|svg)$/i.test(fileName));
      const isVid =
        enforcedType === 'video' ||
        (enforcedType !== 'file' &&
          enforcedType !== 'image' &&
          /\.(mp4|webm|mov|mkv|avi)$/i.test(fileName));
      const fileType: 'image' | 'video' | 'file' = isImg ? 'image' : isVid ? 'video' : 'file';

      let finalB64 = base64Data;
      let finalSize = fileSize;

      if (isImg) {
        setUploadStatus('Đang tối ưu hình ảnh...');
        try {
          const mime = fileName.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg';
          const src = `data:${mime};base64,${base64Data}`;
          const img = new Image();
          await new Promise((res, rej) => {
            img.onload = () => res(null);
            img.onerror = () => rej();
            img.src = src;
          });
          const maxDim = 1400;
          let w = img.width;
          let h = img.height;
          if (w > maxDim || h > maxDim) {
            if (w > h) {
              h = Math.round((h * maxDim) / w);
              w = maxDim;
            } else {
              w = Math.round((w * maxDim) / h);
              h = maxDim;
            }
          }
          const canvas = document.createElement('canvas');
          canvas.width = w;
          canvas.height = h;
          const ctx = canvas.getContext('2d');
          if (ctx) {
            ctx.drawImage(img, 0, 0, w, h);
            const compDataUrl = canvas.toDataURL('image/jpeg', 0.85);
            finalB64 = compDataUrl.split(',')[1] || base64Data;
            finalSize = Math.round((finalB64.length * 3) / 4);
          }
        } catch {
          // Fallback to original
        }
      }

      setUploadStatus('Đang tải lên máy chủ...');
      const uploadRes = await apiService.uploadFile(
        fileName,
        finalB64,
        finalSize,
        fileType
      );

      if (uploadRes && uploadRes.file_id) {
        if (isImg) {
          apiService.cacheImage(uploadRes.file_id, `data:image/jpeg;base64,${finalB64}`);
        }

        const defaultCaption = isImg
          ? 'Đã gửi một hình ảnh'
          : isVid
          ? `Đã gửi video: ${fileName}`
          : `Đã gửi tài liệu: ${fileName}`;

        setUploadStatus('Đang hoàn tất...');
        await sendMessage(
          defaultCaption,
          fileType,
          uploadRes.file_id,
          fileName,
          finalSize
        );
      } else {
        alert(uploadRes?.error || 'Không thể tải tệp tin lên máy chủ. Vui lòng kiểm tra lại kết nối!');
      }
    } catch (err: any) {
      console.error('Error uploading file:', err);
      alert('Lỗi tải tệp: ' + (err?.message || 'Không thể kết nối đến máy chủ.'));
    } finally {
      setIsSending(false);
      setUploadStatus(null);
    }
  };

  const handlePickCategory = async (category: 'image' | 'video' | 'file') => {
    setShowAttachMenu(false);
    setActiveCategory(category);

    try {
      const fileRes = await apiService.selectLocalFile(category);
      if (!fileRes.canceled && fileRes.fileData && fileRes.fileName) {
        await processFileAttachment(fileRes.fileName, fileRes.fileData, fileRes.fileSize || 0, category);
        return;
      }
      if (fileRes.canceled) return;
    } catch {
      // Fallback to HTML5 file input
    }

    if (fileInputRef.current) {
      if (category === 'image') fileInputRef.current.accept = 'image/*';
      else if (category === 'video') fileInputRef.current.accept = 'video/*';
      else fileInputRef.current.accept = '*/*';
      fileInputRef.current.click();
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async () => {
      const result = reader.result as string;
      const b64 = result.includes(',') ? result.split(',')[1] : result;
      await processFileAttachment(file.name, b64, file.size, activeCategory);
      if (fileInputRef.current) fileInputRef.current.value = '';
    };
    reader.readAsDataURL(file);
  };

  const handleEmojiSelect = (emoji: string) => {
    setText((prev) => prev + emoji);
    inputRef.current?.focus();
  };

  return (
    <div className="bg-white dark:bg-[#17212b] border-t border-slate-200 dark:border-slate-800/80 p-3 relative select-none">
      {/* Hidden File Input Fallback for all environments */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileInputChange}
        className="hidden"
        accept="*/*"
      />

      {/* Uploading progress notification bar */}
      {uploadStatus && (
        <div className="mb-2 px-3 py-1.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-[#2481cc] flex items-center space-x-2 text-xs animate-in fade-in duration-150">
          <Loader2 className="w-3.5 h-3.5 animate-spin flex-shrink-0" />
          <span className="font-medium">{uploadStatus}</span>
        </div>
      )}

      {/* Quoted Message / Reply Banner */}
      {replyTo && (
        <div className="mb-2 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-[#202b36] border-l-4 border-[#2481cc] flex items-center justify-between animate-in fade-in slide-in-from-bottom-2 duration-150">
          <div className="flex flex-col text-xs min-w-0 pr-2">
            <span className="font-semibold text-[#2481cc]">Trả lời {replyTo.sender_name}</span>
            <span className="truncate opacity-75">{replyTo.content}</span>
          </div>
          <button
            onClick={() => setReplyTo(null)}
            className="p-1 rounded-full text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Attachment Menu Popup (Separated into Image, Video, Document/File) */}
      {showAttachMenu && (
        <div
          ref={attachMenuRef}
          className="absolute bottom-16 left-3 bg-white dark:bg-[#1e2a38] border border-slate-200 dark:border-slate-700/80 rounded-2xl shadow-2xl p-2 min-w-[230px] z-50 animate-in fade-in zoom-in-95 duration-150 select-none"
        >
          <div className="px-3 py-1.5 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            Tùy chọn đính kèm
          </div>

          {/* 1. Gửi Hình ảnh */}
          <button
            onClick={() => handlePickCategory('image')}
            className="w-full px-3 py-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center space-x-3 transition-colors text-left group cursor-pointer"
          >
            <div className="w-8 h-8 rounded-lg bg-sky-500/15 text-[#2481cc] dark:text-sky-400 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
              <ImageIcon className="w-4 h-4" />
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-semibold text-slate-700 dark:text-slate-200">Gửi Hình ảnh</span>
              <span className="text-[10px] text-slate-400">PNG, JPG, JPEG, GIF, WebP</span>
            </div>
          </button>

          {/* 2. Gửi Video */}
          <button
            onClick={() => handlePickCategory('video')}
            className="w-full px-3 py-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center space-x-3 transition-colors text-left group cursor-pointer"
          >
            <div className="w-8 h-8 rounded-lg bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
              <Video className="w-4 h-4" />
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-semibold text-slate-700 dark:text-slate-200">Gửi Video</span>
              <span className="text-[10px] text-slate-400">MP4, WebM, MOV, MKV</span>
            </div>
          </button>

          {/* 3. Gửi Tệp tin / Tài liệu */}
          <button
            onClick={() => handlePickCategory('file')}
            className="w-full px-3 py-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center space-x-3 transition-colors text-left group cursor-pointer"
          >
            <div className="w-8 h-8 rounded-lg bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
              <FileText className="w-4 h-4" />
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-semibold text-slate-700 dark:text-slate-200">Gửi Tệp tin / Tài liệu</span>
              <span className="text-[10px] text-slate-400">PDF, Word, Excel, ZIP, RAR...</span>
            </div>
          </button>
        </div>
      )}

      {/* Main Composer Row */}
      <div className="flex items-center space-x-1.5">
        {/* Attach File Button - Toggles Menu */}
        <button
          onClick={() => setShowAttachMenu(!showAttachMenu)}
          title="Đính kèm Hình ảnh, Video hoặc Tệp tin"
          className={`p-2 rounded-xl transition-all cursor-pointer ${
            showAttachMenu
              ? 'bg-[#2481cc]/15 text-[#2481cc] dark:bg-[#2481cc]/25'
              : 'text-slate-400 hover:text-[#2481cc] hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <Paperclip className="w-5 h-5" />
        </button>

        {/* Share Location Button */}
        <button
          onClick={handleShareLocation}
          title="Chia sẻ vị trí thời gian thực"
          className="p-2 rounded-xl text-slate-400 hover:text-emerald-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
        >
          <MapPin className="w-5 h-5" />
        </button>

        {/* Text Input */}
        <div className="flex-1 relative flex items-center">
          <input
            ref={inputRef}
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Viết tin nhắn... (Nhấn Enter để gửi)"
            className="w-full h-10 px-4 pr-10 rounded-xl bg-slate-100 dark:bg-[#242f3d] text-sm text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-[#2481cc] transition-all"
          />

          {/* Inline Emoji Trigger */}
          <button
            onClick={() => setShowEmojiPicker(!showEmojiPicker)}
            title="Biểu tượng cảm xúc"
            className="absolute right-2 p-1.5 rounded-lg text-slate-400 hover:text-amber-500 hover:bg-slate-200 dark:hover:bg-slate-700/50 transition-colors"
          >
            <Smile className="w-4 h-4" />
          </button>

          {/* Emoji Picker Popup */}
          {showEmojiPicker && (
            <div className="absolute bottom-12 right-0 z-50">
              <EmojiPicker onSelect={handleEmojiSelect} onClose={() => setShowEmojiPicker(false)} />
            </div>
          )}
        </div>

        {/* Send Button */}
        <button
          onClick={handleSend}
          disabled={!text.trim() || isSending}
          title="Gửi tin nhắn"
          className={`p-2.5 rounded-xl transition-all ${
            text.trim() && !isSending
              ? 'bg-[#2481cc] text-white hover:bg-[#1d73b8] hover:scale-105 active:scale-95 shadow-md shadow-[#2481cc]/20 cursor-pointer'
              : 'bg-slate-100 dark:bg-slate-800 text-slate-400 cursor-not-allowed'
          }`}
        >
          <Send className="w-4 h-4" />
        </button>
      </div>

      {/* Location Sharing Interactive Modal */}
      <LocationModal
        isOpen={showLocationModal}
        onClose={() => setShowLocationModal(false)}
        onSendLocation={(loc) => sendMessage(loc, 'location')}
      />
    </div>
  );
};
