import React, { useState, useEffect } from 'react';
import { Check, Pin, Reply, Trash2, Copy, FileText, Download, ExternalLink, Heart } from 'lucide-react';
import { Message } from '../../types';
import { formatTime, formatFileSize } from '../../lib/utils';
import { useChat } from '../../context/ChatContext';
import { apiService } from '../../services/api';

interface ChatBubbleProps {
  message: Message;
  isSelf: boolean;
  onOpenImage?: (fileId: string, name: string, dataUrl?: string) => void;
}

const ImageBubbleContent: React.FC<{
  fileId: string | number;
  originalName?: string;
  onOpenImage?: (fileId: string, name: string, dataUrl?: string) => void;
  onDownload: () => void;
}> = ({ fileId, originalName, onOpenImage, onDownload }) => {
  const [dataUrl, setDataUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    apiService.getImageUrl(fileId).then((url) => {
      if (mounted) {
        setDataUrl(url);
        setLoading(false);
      }
    });
    return () => {
      mounted = false;
    };
  }, [fileId]);

  return (
    <div
      onClick={() => onOpenImage && onOpenImage(String(fileId), originalName || 'image.png', dataUrl || undefined)}
      className="cursor-pointer group/img relative overflow-hidden bg-slate-200 dark:bg-slate-800 min-w-[200px] min-h-[140px] flex items-center justify-center rounded-xl"
    >
      {loading ? (
        <div className="flex flex-col items-center justify-center p-6 text-slate-400 animate-pulse">
          <div className="w-7 h-7 rounded-full border-2 border-blue-500 border-t-transparent animate-spin mb-2" />
          <span className="text-[11px]">Đang tải ảnh...</span>
        </div>
      ) : dataUrl ? (
        <img
          src={dataUrl}
          alt={originalName || 'Image'}
          className="max-h-72 max-w-full rounded-xl object-contain group-hover/img:scale-[1.02] transition-transform duration-200"
        />
      ) : (
        <div className="flex flex-col items-center justify-center p-6 text-slate-400">
          <span className="text-2xl mb-1">🖼️</span>
          <span className="text-xs">{originalName || 'Hình ảnh'}</span>
        </div>
      )}

      {/* Overlay action bar on hover */}
      <div className="absolute inset-0 bg-black/35 opacity-0 group-hover/img:opacity-100 flex items-center justify-center space-x-3 transition-opacity">
        <span className="p-2 rounded-full bg-black/60 text-white hover:bg-black/80 transition-colors shadow-md" title="Xem toàn màn hình">
          <ExternalLink className="w-4 h-4" />
        </span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDownload();
          }}
          className="p-2 rounded-full bg-black/60 text-white hover:bg-black/80 transition-colors shadow-md"
          title="Tải ảnh về máy"
        >
          <Download className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

const QUICK_REACTIONS = ['❤️', '👍', '😂', '😮', '😢', '🔥'];

export const ChatBubble: React.FC<ChatBubbleProps> = ({ message, isSelf, onOpenImage }) => {
  const { setReplyTo, pinMessage, recallMessage, toggleReaction, currentUser } = useChat();
  const [showMenu, setShowMenu] = useState(false);
  const [menuPos, setMenuPos] = useState({ x: 0, y: 0 });
  const [showReactionPicker, setShowReactionPicker] = useState(false);

  const [copied, setCopied] = useState(false);

  const isDeleted = Boolean(message.is_deleted);
  const isImage = message.msg_type === 'image';
  const isFile = message.msg_type === 'file';

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    setMenuPos({ x: e.clientX, y: e.clientY });
    setShowMenu(true);
  };

  const handleDownloadFile = async () => {
    if (!message.file_id) return;
    const res = await apiService.downloadFile(message.file_id);
    if (res && res.file_data) {
      await apiService.saveDownloadedFile(message.original_name || 'downloaded_file', res.file_data);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
    setShowMenu(false);
  };

  return (
    <div
      onContextMenu={handleContextMenu}
      className={`group relative flex flex-col my-1 max-w-[75%] ${
        isSelf ? 'self-end items-end' : 'self-start items-start'
      }`}
    >
      {/* Bubble Card */}
      <div
        className={`relative px-3.5 py-2 rounded-2xl shadow-sm text-sm break-words transition-all ${
          isSelf
            ? 'bg-[#effdde] dark:bg-[#2b5278] text-slate-800 dark:text-slate-100 rounded-tr-none'
            : 'bg-white dark:bg-[#182533] text-slate-800 dark:text-slate-100 rounded-tl-none border border-slate-100 dark:border-transparent'
        } ${isDeleted ? 'opacity-60 italic' : ''}`}
      >
        {/* Sender Name in Group Chat */}
        {!isSelf && (
          <span className="block text-xs font-bold text-[#2481cc] mb-1">
            {message.sender_name}
          </span>
        )}

        {/* Quoted / Reply Preview */}
        {message.reply_preview && (
          <div className="mb-1.5 p-1.5 px-2 rounded-lg bg-black/5 dark:bg-black/20 border-l-2 border-[#2481cc] text-xs">
            <span className="font-semibold text-[#2481cc] block">Trả lời:</span>
            <span className="truncate block opacity-80">{message.reply_preview}</span>
          </div>
        )}

        {/* 1. Image Thumbnail Message */}
        {isImage && !isDeleted && (
          <div className="my-1 overflow-hidden rounded-xl border border-black/5 dark:border-white/5">
            {message.file_id ? (
              <ImageBubbleContent
                fileId={message.file_id}
                originalName={message.original_name}
                onOpenImage={onOpenImage}
                onDownload={handleDownloadFile}
              />
            ) : (
              <div className="p-4 bg-slate-100 dark:bg-slate-800 text-xs">🖼️ Hình ảnh</div>
            )}
          </div>
        )}

        {/* 2. File / Document Message */}
        {isFile && !isDeleted && (
          <div className="my-1 p-2.5 rounded-xl bg-black/5 dark:bg-black/25 flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-[#2481cc]/15 text-[#2481cc] flex items-center justify-center">
              <FileText className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <span className="font-semibold text-xs truncate block">{message.original_name || 'Tài liệu'}</span>
              <span className="text-[10px] opacity-70 block">{formatFileSize(message.file_size)}</span>
            </div>
            <button
              onClick={handleDownloadFile}
              title="Tải về máy"
              className="p-1.5 rounded-lg bg-[#2481cc] hover:bg-[#1d73b8] text-white transition-colors"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* 3. Text Message Content */}
        {message.content && (!isImage || isDeleted) && (
          <p className="leading-relaxed whitespace-pre-wrap select-text">{message.content}</p>
        )}

        {/* Metadata: Time & Tick */}
        <div className="flex items-center justify-end space-x-1 mt-1 select-none">
          {message.is_pinned && <Pin className="w-2.5 h-2.5 text-[#2481cc] rotate-45" />}
          <span className="text-[10px] opacity-60 font-medium">
            {formatTime(message.created_at)}
          </span>
          {isSelf && !isDeleted && <Check className="w-3 h-3 text-[#2481cc]" />}
        </div>
      </div>

      {/* Reaction Badges */}
      {message.reactions && message.reactions.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1 px-1">
          {message.reactions.map((rx, idx) => {
            const hasMyReaction = rx.users.some((u) => u.id === currentUser?.id);
            return (
              <button
                key={idx}
                onClick={() => toggleReaction(message.id, rx.reaction)}
                className={`px-1.5 py-0.5 rounded-full text-xs flex items-center space-x-1 border transition-all ${
                  hasMyReaction
                    ? 'bg-[#2481cc]/20 border-[#2481cc] text-[#2481cc]'
                    : 'bg-white dark:bg-[#182533] border-slate-200 dark:border-slate-700/60 text-slate-600 dark:text-slate-300'
                }`}
              >
                <span>{rx.reaction}</span>
                <span className="text-[10px] font-bold">{rx.count}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Hover Quick Action Toolbar (Thả cảm xúc, Trả lời, Sao chép, Ghim, Thu hồi) */}
      <div
        className={`absolute -top-3.5 ${
          isSelf ? 'right-2' : 'left-2'
        } hidden group-hover:flex items-center space-x-0.5 bg-white dark:bg-[#1e2c3a] border border-slate-200 dark:border-slate-700/80 rounded-full shadow-lg px-1.5 py-0.5 z-20 animate-in fade-in zoom-in-95 duration-100`}
      >
        {/* 1. Thả cảm xúc */}
        <button
          onClick={() => setShowReactionPicker(!showReactionPicker)}
          title="Thả biểu cảm"
          className="p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400 hover:text-amber-500 transition-colors"
        >
          <Heart className="w-3.5 h-3.5" />
        </button>

        {/* 2. Trả lời */}
        <button
          onClick={() => setReplyTo(message)}
          title="Trả lời tin nhắn"
          className="p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400 hover:text-[#2481cc] transition-colors"
        >
          <Reply className="w-3.5 h-3.5" />
        </button>

        {/* 3. Sao chép nội dung */}
        <button
          onClick={handleCopy}
          title={copied ? 'Đã sao chép!' : 'Sao chép tin nhắn'}
          className={`p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors ${
            copied ? 'text-emerald-500' : 'text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
          }`}
        >
          {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
        </button>

        {/* 4. Ghim tin nhắn */}
        <button
          onClick={() => pinMessage(message.id)}
          title={message.is_pinned ? 'Bỏ ghim' : 'Ghim tin nhắn'}
          className={`p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors ${
            message.is_pinned ? 'text-[#2481cc]' : 'text-slate-400 hover:text-[#2481cc]'
          }`}
        >
          <Pin className="w-3.5 h-3.5" />
        </button>

        {/* 5. Thu hồi tin nhắn (chỉ với tin của mình và chưa thu hồi) */}
        {isSelf && !isDeleted && (
          <button
            onClick={() => recallMessage(message.id)}
            title="Thu hồi tin nhắn"
            className="p-1 rounded-full hover:bg-red-50 dark:hover:bg-red-500/10 text-slate-400 hover:text-red-500 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Quick Reaction Popup */}
      {showReactionPicker && (
        <div
          className={`absolute -top-11 ${
            isSelf ? 'right-0' : 'left-0'
          } bg-white dark:bg-[#1e2c3a] border border-slate-200 dark:border-slate-700 rounded-full shadow-lg p-1 flex space-x-1 z-30 animate-in fade-in zoom-in-95 duration-100`}
        >
          {QUICK_REACTIONS.map((emoji) => (
            <button
              key={emoji}
              onClick={() => {
                toggleReaction(message.id, emoji);
                setShowReactionPicker(false);
              }}
              className="w-7 h-7 flex items-center justify-center text-sm rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 hover:scale-125 transition-transform"
            >
              {emoji}
            </button>
          ))}
        </div>
      )}

      {/* Context Menu Modal / Backdrop */}
      {showMenu && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setShowMenu(false)} />
          <div
            style={{ top: `${menuPos.y}px`, left: `${menuPos.x}px` }}
            className="fixed w-44 bg-white dark:bg-[#1e2c3a] border border-slate-200 dark:border-slate-700/80 rounded-xl shadow-2xl py-1 z-50 text-xs text-slate-700 dark:text-slate-200 animate-in fade-in zoom-in-95 duration-100"
          >
            <button
              onClick={() => {
                setReplyTo(message);
                setShowMenu(false);
              }}
              className="w-full px-3 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center space-x-2"
            >
              <Reply className="w-3.5 h-3.5 text-[#2481cc]" />
              <span>Trả lời tin nhắn</span>
            </button>

            <button
              onClick={() => {
                pinMessage(message.id);
                setShowMenu(false);
              }}
              className="w-full px-3 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center space-x-2"
            >
              <Pin className="w-3.5 h-3.5 text-amber-500" />
              <span>Ghim tin nhắn</span>
            </button>

            {message.content && (
              <button
                onClick={handleCopy}
                className="w-full px-3 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-700/60 flex items-center space-x-2"
              >
                <Copy className="w-3.5 h-3.5" />
                <span>Sao chép</span>
              </button>
            )}

            {isSelf && !isDeleted && (
              <>
                <div className="w-full h-px bg-slate-200 dark:bg-slate-700/60 my-1" />
                <button
                  onClick={() => {
                    recallMessage(message.id);
                    setShowMenu(false);
                  }}
                  className="w-full px-3 py-2 text-left text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 flex items-center space-x-2"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Thu hồi tin nhắn</span>
                </button>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
};

