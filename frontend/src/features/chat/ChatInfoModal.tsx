import React, { useState, useEffect } from 'react';
import { X, Image as ImageIcon, FileText, Pin, Download, User, Phone, Video } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { getInitials, formatTime } from '../../lib/utils';
import { apiService } from '../../services/api';

interface ChatInfoModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const MediaThumbnailItem: React.FC<{
  fileId: string;
  name: string;
  onPreview: (url?: string) => void;
  onDownload: () => void;
}> = ({ fileId, name, onPreview, onDownload }) => {
  const [url, setUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    apiService.getImageUrl(fileId).then((imgUrl) => {
      if (mounted) {
        setUrl(imgUrl);
        setLoading(false);
      }
    });
    return () => {
      mounted = false;
    };
  }, [fileId]);

  return (
    <div
      className="group relative aspect-square rounded-xl overflow-hidden bg-slate-800 cursor-pointer border border-slate-700/60 shadow-sm"
      onClick={() => onPreview(url || undefined)}
    >
      {loading ? (
        <div className="w-full h-full flex flex-col items-center justify-center bg-slate-800 text-slate-400 p-2 animate-pulse">
          <div className="w-5 h-5 rounded-full border-2 border-[#2481cc] border-t-transparent animate-spin mb-1.5" />
          <span className="text-[9px]">Đang tải...</span>
        </div>
      ) : url ? (
        <img
          src={url}
          alt={name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
        />
      ) : (
        <div className="w-full h-full flex flex-col items-center justify-center text-slate-400 bg-slate-800 p-2 text-center">
          <ImageIcon className="w-6 h-6 text-[#2481cc] mb-1" />
          <span className="text-[9px] truncate max-w-full opacity-80">{name}</span>
        </div>
      )}

      {/* Hover action overlay */}
      <div className="absolute inset-0 bg-black/45 opacity-0 group-hover:opacity-100 flex items-center justify-center space-x-2 transition-opacity">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onPreview(url || undefined);
          }}
          className="p-1.5 rounded-full bg-black/60 text-white hover:bg-black/90 transition-colors"
          title="Xem ảnh"
        >
          <ImageIcon className="w-4 h-4" />
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDownload();
          }}
          className="p-1.5 rounded-full bg-black/60 text-white hover:bg-black/90 transition-colors"
          title="Tải về máy"
        >
          <Download className="w-4 h-4" />
        </button>
      </div>

      {/* Name banner at bottom */}
      <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-1 px-1.5">
        <p className="text-[9px] text-white/90 truncate">{name}</p>
      </div>
    </div>
  );
};

export const ChatInfoModal: React.FC<ChatInfoModalProps> = ({ isOpen, onClose }) => {
  const { activeConv, messages, startCall } = useChat();
  const [activeTab, setActiveTab] = useState<'media' | 'files' | 'pinned'>('media');
  const [previewImage, setPreviewImage] = useState<{ fileId: string; name: string; url?: string } | null>(null);

  if (!isOpen || !activeConv) return null;

  const isGroup = activeConv.type === 'group';
  const isDirect = activeConv.type === 'direct';

  // Filter media, files, pinned messages
  const mediaMsgs = messages.filter((m) => m.msg_type === 'image' && !m.is_deleted);
  const fileMsgs = messages.filter((m) => m.msg_type === 'file' && !m.is_deleted);
  const pinnedMsgs = messages.filter((m) => m.is_pinned && !m.is_deleted);

  const handleDownload = async (fileId?: string | null, origName?: string) => {
    if (!fileId) return;
    try {
      const res = await apiService.downloadFile(fileId);
      if (res && res.file_data) {
        await apiService.saveDownloadedFile(origName || 'downloaded_file', res.file_data);
      }
    } catch (e) {
      console.error('Download error:', e);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in select-none">
      <div className="w-[420px] max-h-[85vh] bg-white dark:bg-[#17212b] rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="h-14 px-5 border-b border-slate-200 dark:border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <User className="w-5 h-5 text-[#2481cc]" />
            <h3 className="font-semibold text-base text-slate-800 dark:text-slate-100">
              Thông tin hội thoại
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Profile Card */}
        <div className="p-6 flex flex-col items-center border-b border-slate-100 dark:border-slate-800/50 bg-slate-50/50 dark:bg-[#1c2733]/40">
          <div
            className="w-20 h-20 rounded-full flex items-center justify-center font-bold text-white text-2xl shadow-lg mb-3"
            style={{ backgroundColor: activeConv.avatar_color || (isGroup ? '#06b6d4' : '#2481cc') }}
          >
            {getInitials(activeConv.title)}
          </div>
          <h4 className="font-bold text-lg text-slate-900 dark:text-slate-100 text-center">
            {activeConv.title}
          </h4>
          <span className="text-xs mt-1">
            {isGroup ? (
              <span className="text-slate-400 font-medium">Nhóm trò chuyện</span>
            ) : activeConv.is_online ? (
              <span className="text-emerald-500 font-medium flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>Đang trực tuyến</span>
              </span>
            ) : (
              <span className="text-slate-400 font-medium">Ngoại tuyến</span>
            )}
          </span>

          {/* Quick call buttons */}
          {isDirect && (
            <div className="flex items-center space-x-3 mt-4">
              <button
                onClick={() => {
                  onClose();
                  startCall('voice');
                }}
                className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/50 text-xs font-semibold transition-colors"
              >
                <Phone className="w-3.5 h-3.5" />
                <span>Gọi thoại</span>
              </button>
              <button
                onClick={() => {
                  onClose();
                  startCall('video');
                }}
                className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-900/50 text-xs font-semibold transition-colors"
              >
                <Video className="w-3.5 h-3.5" />
                <span>Gọi video</span>
              </button>
            </div>
          )}
        </div>

        {/* Tab Selector */}
        <div className="flex border-b border-slate-200 dark:border-slate-800 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('media')}
            className={`flex-1 py-3 flex items-center justify-center space-x-1.5 border-b-2 transition-colors ${
              activeTab === 'media'
                ? 'border-[#2481cc] text-[#2481cc]'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400'
            }`}
          >
            <ImageIcon className="w-3.5 h-3.5" />
            <span>Ảnh ({mediaMsgs.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('files')}
            className={`flex-1 py-3 flex items-center justify-center space-x-1.5 border-b-2 transition-colors ${
              activeTab === 'files'
                ? 'border-[#2481cc] text-[#2481cc]'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Tệp tin ({fileMsgs.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('pinned')}
            className={`flex-1 py-3 flex items-center justify-center space-x-1.5 border-b-2 transition-colors ${
              activeTab === 'pinned'
                ? 'border-[#2481cc] text-[#2481cc]'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400'
            }`}
          >
            <Pin className="w-3.5 h-3.5" />
            <span>Ghim ({pinnedMsgs.length})</span>
          </button>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-4 min-h-[220px]">
          {/* Media Tab */}
          {activeTab === 'media' && (
            <div>
              {mediaMsgs.length === 0 ? (
                <div className="text-center py-10 text-slate-400 text-xs">
                  Chưa có hình ảnh nào được gửi
                </div>
              ) : (
                <div className="grid grid-cols-3 gap-2">
                  {mediaMsgs.map((m) => (
                    <MediaThumbnailItem
                      key={m.id}
                      fileId={String(m.file_id)}
                      name={m.original_name || 'image.png'}
                      onPreview={(url) => setPreviewImage({ fileId: String(m.file_id), name: m.original_name || 'image.png', url })}
                      onDownload={() => handleDownload(m.file_id, m.original_name || 'image.png')}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Files Tab */}
          {activeTab === 'files' && (
            <div className="space-y-2">
              {fileMsgs.length === 0 ? (
                <div className="text-center py-10 text-slate-400 text-xs">
                  Chưa có tệp tin nào được chia sẻ
                </div>
              ) : (
                fileMsgs.map((m) => (
                  <div
                    key={m.id}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors border border-slate-200/60 dark:border-slate-700/40"
                  >
                    <div className="flex items-center space-x-3 overflow-hidden">
                      <div className="w-9 h-9 rounded-lg bg-blue-500/10 text-[#2481cc] flex items-center justify-center flex-shrink-0">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div className="truncate">
                        <p className="text-xs font-semibold text-slate-800 dark:text-slate-100 truncate">
                          {m.original_name || m.content || 'Tài liệu'}
                        </p>
                        <p className="text-[10px] text-slate-400 mt-0.5">
                          {formatTime(m.created_at)}
                        </p>
                      </div>
                    </div>
                    {m.file_id && (
                      <button
                        onClick={() => handleDownload(m.file_id, m.original_name || 'document')}
                        className="p-1.5 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors flex-shrink-0"
                        title="Tải về"
                      >
                        <Download className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {/* Pinned Tab */}
          {activeTab === 'pinned' && (
            <div className="space-y-2">
              {pinnedMsgs.length === 0 ? (
                <div className="text-center py-10 text-slate-400 text-xs">
                  Chưa có tin nhắn nào được ghim
                </div>
              ) : (
                pinnedMsgs.map((m) => (
                  <div
                    key={m.id}
                    className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800/40 text-xs"
                  >
                    <div className="flex items-center space-x-1.5 font-bold text-amber-600 dark:text-amber-400 mb-1">
                      <Pin className="w-3 h-3" />
                      <span>{m.sender_name}</span>
                    </div>
                    <p className="text-slate-700 dark:text-slate-200 break-words">
                      {m.content}
                    </p>
                    <span className="text-[10px] text-slate-400 mt-1 block">
                      {formatTime(m.created_at)}
                    </span>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Fullscreen Image Preview Lightbox inside Info Modal */}
        {previewImage && (
          <div
            onClick={() => setPreviewImage(null)}
            className="fixed inset-0 z-[60] bg-black/90 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-150 select-none"
          >
            <div
              onClick={(e) => e.stopPropagation()}
              className="relative max-w-4xl max-h-[90vh] flex flex-col items-center"
            >
              <div className="absolute -top-11 right-0 flex items-center space-x-2">
                <button
                  onClick={() => handleDownload(previewImage.fileId, previewImage.name)}
                  className="p-2 text-white/80 hover:text-white rounded-full bg-white/10 hover:bg-white/20 transition-colors"
                  title="Tải ảnh về máy"
                >
                  <Download className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setPreviewImage(null)}
                  className="p-2 text-white/80 hover:text-white rounded-full bg-white/10 hover:bg-white/20 transition-colors"
                  title="Đóng"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {previewImage.url ? (
                <img
                  src={previewImage.url}
                  alt={previewImage.name}
                  className="max-h-[82vh] w-auto max-w-full rounded-2xl shadow-2xl object-contain border border-white/10"
                />
              ) : (
                <div className="p-12 text-white/70 text-xs">Đang tải ảnh...</div>
              )}

              <div className="mt-3 px-4 py-1.5 rounded-full bg-black/60 border border-white/10 text-xs text-white/90 font-medium">
                {previewImage.name}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

