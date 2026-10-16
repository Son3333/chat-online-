import React, { useState, useEffect } from 'react';
import { Check, Pin, Reply, Trash2, Copy, FileText, Download, ExternalLink, Heart, Video, MapPin, Navigation, FolderArchive } from 'lucide-react';
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

  const fetchImage = () => {
    setLoading(true);
    apiService.getImageUrl(fileId).then((url) => {
      setDataUrl(url);
      setLoading(false);
    });
  };

  useEffect(() => {
    fetchImage();
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
          <span className="text-xs mb-2 font-medium text-slate-500 dark:text-slate-300">{originalName || 'Hình ảnh'}</span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              fetchImage();
            }}
            className="px-2.5 py-1 text-[11px] rounded-lg bg-[#2481cc]/20 text-[#2481cc] hover:bg-[#2481cc]/30 transition-colors font-medium"
          >
            Tải lại ảnh
          </button>
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

const VideoBubbleContent: React.FC<{
  fileId: string | number;
  originalName?: string;
  onDownload: () => void;
}> = ({ fileId, originalName, onDownload }) => {
  const [videoSrc, setVideoSrc] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const blobUrlRef = React.useRef<string | null>(null);

  useEffect(() => {
    let mounted = true;
    apiService.downloadFile(fileId).then((res) => {
      if (mounted) {
        if (res && res.file_data) {
          let mime = res.file_type || 'video/mp4';
          if (!mime.startsWith('video/')) {
            const fn = (res.filename || res.original_name || '').toLowerCase();
            if (fn.endsWith('.webm')) mime = 'video/webm';
            else if (fn.endsWith('.mov')) mime = 'video/quicktime';
            else if (fn.endsWith('.mkv')) mime = 'video/x-matroska';
            else mime = 'video/mp4';
          }

          try {
            const binaryString = atob(res.file_data);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
              bytes[i] = binaryString.charCodeAt(i);
            }
            const blob = new Blob([bytes], { type: mime });
            const url = URL.createObjectURL(blob);
            blobUrlRef.current = url;
            setVideoSrc(url);
          } catch {
            setVideoSrc(`data:${mime};base64,${res.file_data}`);
          }
        }
        setLoading(false);
      }
    });

    return () => {
      mounted = false;
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current);
      }
    };
  }, [fileId]);

  return (
    <div className="relative overflow-hidden rounded-xl bg-black/20 dark:bg-black/50 min-w-[260px] max-w-sm">
      {loading ? (
        <div className="flex flex-col items-center justify-center p-8 text-slate-400 animate-pulse">
          <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin mb-2" />
          <span className="text-[11px]">Đang tải video...</span>
        </div>
      ) : videoSrc && !hasError ? (
        <div className="flex flex-col">
          <video
            controls
            preload="metadata"
            src={videoSrc}
            onError={() => setHasError(true)}
            className="max-h-72 w-full rounded-t-xl object-contain bg-black"
          />
          <div className="p-2 bg-black/40 flex items-center justify-between text-xs text-white">
            <span className="truncate pr-2 font-medium">{originalName || 'Video'}</span>
            <button
              onClick={onDownload}
              title="Tải video về máy"
              className="p-1 rounded-lg bg-white/20 hover:bg-white/30 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      ) : (
        <div className="p-4 flex flex-col space-y-2">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
              <Video className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <span className="text-xs font-semibold block truncate text-slate-700 dark:text-slate-200">
                {originalName || 'Video clip'}
              </span>
              <span className="text-[10px] text-slate-400 block">
                {hasError ? 'Định dạng đặc biệt • Tải về để phát' : 'Video tệp đính kèm'}
              </span>
            </div>
          </div>
          <button
            onClick={onDownload}
            className="w-full py-1.5 px-3 rounded-lg bg-[#2481cc] hover:bg-[#1d6fa5] text-white text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Tải video về máy</span>
          </button>
        </div>
      )}
    </div>
  );
};

const LinkifiedText: React.FC<{ text: string }> = ({ text }) => {
  // Regex matching http/https URLs and www. links
  const urlRegex = /(https?:\/\/[^\s<]+[^<.,:;"')\]\s]|www\.[^\s<]+[^<.,:;"')\]\s])/gi;
  const parts = text.split(urlRegex);

  // Check for YouTube video link
  const ytMatch = text.match(/(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/i);
  const ytVideoId = ytMatch ? ytMatch[1] : null;

  return (
    <div>
      <p className="leading-relaxed whitespace-pre-wrap select-text">
        {parts.map((part, i) => {
          if (urlRegex.test(part)) {
            const href = part.startsWith('www.') ? `https://${part}` : part;
            return (
              <a
                key={i}
                href={href}
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  apiService.openExternal(href);
                }}
                title={`Mở liên kết: ${href}`}
                className="text-[#2481cc] hover:text-[#1d73b8] dark:text-[#52a6eb] hover:underline font-semibold break-all inline-flex items-center space-x-0.5 cursor-pointer"
              >
                <span>{part}</span>
                <ExternalLink className="w-3 h-3 inline-block ml-0.5 opacity-70 flex-shrink-0" />
              </a>
            );
          }
          return <span key={i}>{part}</span>;
        })}
      </p>

      {/* Embedded YouTube preview if message has a YouTube URL */}
      {ytVideoId && (
        <div className="mt-2 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700 aspect-video w-full max-w-sm shadow-md">
          <iframe
            src={`https://www.youtube.com/embed/${ytVideoId}`}
            title="YouTube video player"
            className="w-full h-full"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      )}
    </div>
  );
};

const LocationBubbleContent: React.FC<{
  content: string;
}> = ({ content }) => {
  // Extract coordinates if present (e.g., "21.0285, 105.8542")
  const coordMatch = content.match(/(-?\d+\.\d+),\s*(-?\d+\.\d+)/);
  const lat = coordMatch ? parseFloat(coordMatch[1]) : null;
  const lng = coordMatch ? parseFloat(coordMatch[2]) : null;

  // Clean human-readable address
  const cleanAddress = content.replace(/^📍\s*(Vị\s*trí(\s*thực\s*tế|\s*GPS)?:\s*)?/i, '').trim();

  // Directions (Chỉ đường trực tiếp trên Google Maps giống Messenger)
  const directionsUrl = lat && lng
    ? `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`
    : `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(cleanAddress)}`;

  // View location marker on Google Maps
  const mapUrl = lat && lng
    ? `https://www.google.com/maps?q=${lat},${lng}`
    : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(cleanAddress)}`;

  const handleOpenDirections = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    apiService.openExternal(directionsUrl);
  };

  const handleOpenMap = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    apiService.openExternal(mapUrl);
  };

  return (
    <div className="my-1.5 p-2 rounded-2xl bg-slate-50 dark:bg-[#192430] border border-slate-200 dark:border-slate-700/80 shadow-md min-w-[240px] max-w-sm select-none">
      {/* 1. Visual Map Preview */}
      {lat && lng ? (
        <div
          onClick={handleOpenDirections}
          title="Bấm để mở Google Maps chỉ đường"
          className="relative w-full h-36 rounded-xl overflow-hidden cursor-pointer group/map border border-slate-200 dark:border-slate-700 bg-slate-200 dark:bg-slate-800"
        >
          <iframe
            title="Location Map Preview"
            width="100%"
            height="100%"
            frameBorder="0"
            scrolling="no"
            src={`https://www.openstreetmap.org/export/embed.html?bbox=${lng - 0.007}%2C${lat - 0.004}%2C${lng + 0.007}%2C${lat + 0.004}&layer=mapnik&marker=${lat}%2C${lng}`}
            className="w-full h-full pointer-events-none select-none"
          />
          {/* Hover overlay hint */}
          <div className="absolute inset-0 bg-black/20 opacity-0 group-hover/map:opacity-100 transition-opacity flex items-center justify-center">
            <span className="px-3 py-1.5 rounded-full bg-emerald-600 text-white text-xs font-semibold shadow-lg flex items-center space-x-1.5 transform group-hover/map:scale-105 transition-transform">
              <Navigation className="w-3.5 h-3.5 fill-current" />
              <span>Chỉ đường trên Google Maps</span>
            </span>
          </div>
        </div>
      ) : (
        <div
          onClick={handleOpenDirections}
          className="relative w-full h-24 rounded-xl cursor-pointer bg-gradient-to-br from-emerald-500/20 via-teal-500/20 to-blue-500/20 flex flex-col items-center justify-center p-3 text-center border border-emerald-500/30"
        >
          <MapPin className="w-7 h-7 text-rose-500 animate-bounce mb-1" />
          <span className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-300">
            Bấm để mở bản đồ chỉ đường
          </span>
        </div>
      )}

      {/* 2. Location Info */}
      <div className="px-1 pt-2.5 pb-1">
        <div className="flex items-start space-x-2 mb-1">
          <MapPin className="w-4 h-4 text-rose-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <span className="text-xs font-bold text-slate-800 dark:text-slate-100 block truncate">
              {cleanAddress.split('(')[0] || 'Vị trí thời gian thực'}
            </span>
            {lat && lng ? (
              <span className="text-[10px] text-slate-400 block">
                Tọa độ GPS: {lat.toFixed(5)}, {lng.toFixed(5)}
              </span>
            ) : (
              <span className="text-[10px] text-slate-400 block truncate">{cleanAddress}</span>
            )}
          </div>
        </div>

        {/* 3. Action Buttons (Chỉ đường & Xem bản đồ) */}
        <div className="grid grid-cols-2 gap-2 mt-2.5">
          <button
            onClick={handleOpenDirections}
            className="py-2 px-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white text-xs font-bold flex items-center justify-center space-x-1.5 shadow-sm transition-all"
            title="Chỉ đường từ vị trí của bạn tới điểm này"
          >
            <Navigation className="w-3.5 h-3.5 fill-current flex-shrink-0" />
            <span className="truncate">Chỉ Đường</span>
          </button>

          <button
            onClick={handleOpenMap}
            className="py-2 px-2.5 rounded-xl bg-white dark:bg-[#233140] hover:bg-slate-100 dark:hover:bg-slate-700/60 active:scale-95 text-slate-700 dark:text-slate-200 text-xs font-semibold flex items-center justify-center space-x-1.5 border border-slate-200 dark:border-slate-700 transition-all shadow-xs"
            title="Xem vị trí ghim trên bản đồ"
          >
            <ExternalLink className="w-3.5 h-3.5 text-[#2481cc] flex-shrink-0" />
            <span className="truncate">Xem Bản Đồ</span>
          </button>
        </div>
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
  const isVideo = message.msg_type === 'video';
  const isLocation = message.msg_type === 'location';
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
          <div className="flex items-center space-x-1.5 mb-1">
            {message.avatar_url ? (
              <img src={message.avatar_url} alt="" className="w-4 h-4 rounded-full object-cover flex-shrink-0" />
            ) : null}
            <span className="block text-xs font-bold text-[#2481cc]">
              {message.sender_name}
            </span>
          </div>
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

        {/* 2. Video Message */}
        {isVideo && !isDeleted && (
          <div className="my-1 overflow-hidden rounded-xl border border-black/5 dark:border-white/5">
            {message.file_id ? (
              <VideoBubbleContent
                fileId={message.file_id}
                originalName={message.original_name}
                onDownload={handleDownloadFile}
              />
            ) : (
              <div className="p-4 bg-slate-100 dark:bg-slate-800 text-xs">🎬 Video</div>
            )}
          </div>
        )}

        {/* 3. Location Message */}
        {isLocation && !isDeleted && (
          <LocationBubbleContent content={message.content} />
        )}

        {/* 4. File / Document Message */}
        {isFile && !isDeleted && (() => {
          const isZip = /\.(zip|rar|7z|tar|gz|bz2)$/i.test(message.original_name || '');
          return (
            <div className="my-1 p-2.5 rounded-xl bg-black/5 dark:bg-black/25 flex items-center space-x-3">
              <div
                className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                  isZip
                    ? 'bg-amber-500/15 text-amber-500'
                    : 'bg-[#2481cc]/15 text-[#2481cc]'
                }`}
              >
                {isZip ? <FolderArchive className="w-5 h-5" /> : <FileText className="w-5 h-5" />}
              </div>
              <div className="flex-1 min-w-0">
                <span className="font-semibold text-xs truncate block">{message.original_name || 'Tài liệu'}</span>
                <span className="text-[10px] opacity-70 block">
                  {formatFileSize(message.file_size)} {isZip ? '• Tệp nén' : ''}
                </span>
              </div>
              <button
                onClick={handleDownloadFile}
                title="Tải về máy"
                className="p-1.5 rounded-lg bg-[#2481cc] hover:bg-[#1d73b8] text-white transition-colors"
              >
                <Download className="w-4 h-4" />
              </button>
            </div>
          );
        })()}

        {/* 5. Text Message Content */}
        {message.content && (!isImage && !isVideo && !isLocation || isDeleted) && (
          isDeleted ? (
            <p className="leading-relaxed whitespace-pre-wrap select-text">{message.content}</p>
          ) : (
            <LinkifiedText text={message.content} />
          )
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
