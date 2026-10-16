import React, { useState, useRef, useEffect } from 'react';
import { Paperclip, Smile, Send, X, MapPin } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { EmojiPicker } from '../../components/EmojiPicker';
import { apiService } from '../../services/api';

export const ChatComposer: React.FC = () => {
  const { replyTo, setReplyTo, sendMessage, activeConv, currentUser } = useChat();
  const [text, setText] = useState('');
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const lastTypingRef = useRef<number>(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, [activeConv, replyTo]);

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

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const lat = pos.coords.latitude.toFixed(6);
          const lng = pos.coords.longitude.toFixed(6);
          await sendMessage(`📍 Vị trí hiện tại: ${lat}, ${lng}`, 'location');
        },
        async () => {
          const custom = prompt('Nhập tên địa điểm hoặc tọa độ bạn muốn chia sẻ:', 'Hà Nội, Việt Nam');
          if (custom && custom.trim()) {
            await sendMessage(`📍 Vị trí: ${custom.trim()}`, 'location');
          }
        },
        { timeout: 7000, enableHighAccuracy: true }
      );
    } else {
      const custom = prompt('Nhập tên địa điểm bạn muốn chia sẻ:', 'Hà Nội, Việt Nam');
      if (custom && custom.trim()) {
        sendMessage(`📍 Vị trí: ${custom.trim()}`, 'location');
      }
    }
  };

  const processFileAttachment = async (fileName: string, base64Data: string, fileSize: number) => {
    if (!activeConv || !currentUser) return;
    setIsSending(true);

    try {
      const isImg = /\.(png|jpe?g|gif|webp)$/i.test(fileName);
      const isVid = /\.(mp4|webm|mov|mkv|avi)$/i.test(fileName);
      const fileType = isImg ? 'image' : isVid ? 'video' : 'file';

      const uploadRes = await apiService.uploadFile(
        fileName,
        base64Data,
        fileSize,
        fileType,
        activeConv.id,
        currentUser.id
      );

      if (uploadRes && uploadRes.file_id) {
        const defaultCaption = isImg
          ? 'Đã gửi một hình ảnh'
          : isVid
          ? `Đã gửi video: ${fileName}`
          : `Đã gửi tài liệu: ${fileName}`;

        await sendMessage(
          defaultCaption,
          fileType,
          uploadRes.file_id,
          fileName,
          fileSize
        );
      }
    } catch (err) {
      console.error('Error uploading file:', err);
    } finally {
      setIsSending(false);
    }
  };

  const handlePickFile = async () => {
    // Try native Electron file picker first if available
    try {
      const fileRes = await apiService.selectLocalFile();
      if (!fileRes.canceled && fileRes.fileData && fileRes.fileName) {
        await processFileAttachment(fileRes.fileName, fileRes.fileData, fileRes.fileSize || 0);
        return;
      }
    } catch {
      // Fallback to browser input
    }

    // Fallback: trigger HTML5 input
    fileInputRef.current?.click();
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async () => {
      const result = reader.result as string;
      const b64 = result.includes(',') ? result.split(',')[1] : result;
      await processFileAttachment(file.name, b64, file.size);
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

      {/* Main Composer Row */}
      <div className="flex items-center space-x-1.5">
        {/* Attach File Button */}
        <button
          onClick={handlePickFile}
          title="Đính kèm tệp tin, hình ảnh hoặc video"
          className="p-2 rounded-xl text-slate-400 hover:text-[#2481cc] hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
        >
          <Paperclip className="w-5 h-5" />
        </button>

        {/* Share Location Button */}
        <button
          onClick={handleShareLocation}
          title="Chia sẻ vị trí thời gian thực"
          className="p-2 rounded-xl text-slate-400 hover:text-emerald-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
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
              ? 'bg-[#2481cc] text-white hover:bg-[#1d73b8] hover:scale-105 active:scale-95 shadow-md shadow-[#2481cc]/20'
              : 'bg-slate-100 dark:bg-slate-800 text-slate-400 cursor-not-allowed'
          }`}
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
