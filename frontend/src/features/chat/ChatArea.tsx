import React, { useRef, useEffect, useState, useMemo } from 'react';
import { Pin, X, Download, MessageCircle, ShieldAlert, UserPlus, Ban, Check, Clock } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { apiService } from '../../services/api';
import APP_LOGO from '../../assets/logo';
import { ChatHeader } from './ChatHeader';
import { ChatBubble } from './ChatBubble';
import { ChatComposer } from './ChatComposer';
import { FilePreviewModal } from './FilePreviewModal';

export const ChatArea: React.FC = () => {
  const {
    activeConv,
    messages,
    loadingMessages,
    currentUser,
    pinnedMessage,
    unpinMessage,
    friends,
    pendingFriends,
    sentFriendRequestIds,
    refreshFriends,
    refreshConversations,
  } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [previewImage, setPreviewImage] = useState<{ fileId: string; name: string; url?: string } | null>(null);
  const [previewFile, setPreviewFile] = useState<{ fileId: string | number; name: string; fileSize?: number; fileType?: string } | null>(null);
  const [logoError, setLogoError] = useState(false);

  // Filter messages strictly for active conversation to guarantee ZERO cross-chat leakage
  const convMessages = useMemo(() => {
    if (!activeConv) return [];
    return messages.filter((m) => !m.conversation_id || String(m.conversation_id) === String(activeConv.id));
  }, [messages, activeConv]);

  // Auto scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [convMessages]);

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

  const isDirect = activeConv.type === 'direct';
  const partnerId =
    activeConv.partner_id ||
    (typeof activeConv.id === 'string' && activeConv.id.startsWith('direct_')
      ? Number(activeConv.id.replace('direct_', ''))
      : undefined);

  const isFriend = Boolean(partnerId && friends.some((f) => f.id === partnerId));
  const isSent = Boolean(partnerId && sentFriendRequestIds.includes(partnerId));
  const isIncoming = Boolean(partnerId && pendingFriends.some((p) => p.id === partnerId));
  const showStrangerBanner = Boolean(isDirect && partnerId && !isFriend);

  const handleAddFriend = async () => {
    if (!currentUser || !partnerId) return;
    const res = await apiService.sendFriendRequest(currentUser.id, partnerId);
    if (res && res.success) {
      await refreshFriends();
    }
  };

  const handleAcceptRequest = async () => {
    if (!currentUser || !partnerId) return;
    const res = await apiService.acceptFriendRequest(currentUser.id, partnerId);
    if (res && res.success) {
      await refreshFriends();
      await refreshConversations();
    }
  };

  const handleRejectRequest = async () => {
    if (!currentUser || !partnerId) return;
    const res = await apiService.rejectFriendRequest(currentUser.id, partnerId);
    if (res && res.success) {
      await refreshFriends();
    }
  };

  const handleCancelRequest = async () => {
    if (!currentUser || !partnerId) return;
    const res = await apiService.removeFriend(currentUser.id, partnerId);
    if (res && res.success) {
      await refreshFriends();
    }
  };

  const handleBlockUser = async () => {
    if (!currentUser || !partnerId) return;
    if (!confirm(`Bạn có chắc chắn muốn chặn ${activeConv.title}? Họ sẽ không thể nhắn tin cho bạn.`)) return;
    const res = await apiService.blockUser(currentUser.id, partnerId);
    if (res && res.success) {
      await refreshFriends();
      await refreshConversations();
    }
  };

  return (
    <div className="flex-1 h-full flex flex-col bg-slate-50 dark:bg-[#0e1621] relative overflow-hidden">
      {/* 1. Header */}
      <ChatHeader />

      {/* 2. Stranger Warning & Friend Request Banner */}
      {showStrangerBanner && (
        <div className="px-4 py-2 bg-gradient-to-r from-amber-500/15 via-amber-500/10 to-transparent border-b border-amber-500/25 dark:border-amber-500/30 flex items-center justify-between text-xs animate-in slide-in-from-top-1 duration-150 select-none">
          <div className="flex items-center space-x-2 mr-3 truncate">
            <ShieldAlert className="w-4 h-4 text-amber-500 flex-shrink-0" />
            <span className="text-slate-700 dark:text-slate-200 truncate">
              {isIncoming ? (
                <>
                  <strong className="font-semibold text-slate-800 dark:text-slate-100">{activeConv.title}</strong> đã gửi lời mời kết bạn cho bạn.
                </>
              ) : isSent ? (
                <>
                  Đã gửi lời mời kết bạn tới <strong className="font-semibold text-slate-800 dark:text-slate-100">{activeConv.title}</strong> (Đang chờ đồng ý).
                </>
              ) : (
                <>
                  <strong className="font-semibold text-slate-800 dark:text-slate-100">{activeConv.title}</strong> chưa có trong danh bạ bạn bè.
                </>
              )}
            </span>
          </div>

          <div className="flex items-center space-x-1.5 flex-shrink-0">
            {isIncoming ? (
              <>
                <button
                  onClick={handleAcceptRequest}
                  className="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-medium flex items-center space-x-1 shadow-sm transition-colors cursor-pointer"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Đồng ý</span>
                </button>
                <button
                  onClick={handleRejectRequest}
                  className="px-2.5 py-1 rounded-lg bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 font-medium transition-colors cursor-pointer"
                >
                  <X className="w-3.5 h-3.5" />
                  <span>Từ chối</span>
                </button>
              </>
            ) : isSent ? (
              <button
                onClick={handleCancelRequest}
                title="Bấm vào để hủy lời mời kết bạn đã gửi"
                className="px-2.5 py-1 rounded-lg bg-amber-500/15 hover:bg-rose-500/15 text-amber-600 dark:text-amber-400 hover:text-rose-600 dark:hover:text-rose-400 border border-amber-500/25 hover:border-rose-500/30 font-medium flex items-center space-x-1 transition-all active:scale-95 cursor-pointer group/btn"
              >
                <Clock className="w-3.5 h-3.5 group-hover/btn:hidden" />
                <X className="w-3.5 h-3.5 hidden group-hover/btn:inline-block text-rose-500" />
                <span className="group-hover/btn:hidden">Chờ duyệt</span>
                <span className="hidden group-hover/btn:inline-block font-semibold">Hủy lời mời</span>
              </button>
            ) : (
              <button
                onClick={handleAddFriend}
                className="px-2.5 py-1 rounded-lg bg-[#2481cc] hover:bg-[#1b6ca8] text-white font-medium flex items-center space-x-1 shadow-sm transition-colors cursor-pointer"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>Kết bạn</span>
              </button>
            )}

            <button
              onClick={handleBlockUser}
              className="px-2.5 py-1 rounded-lg bg-rose-500/10 text-rose-600 dark:text-rose-400 hover:bg-rose-600 hover:text-white border border-rose-500/20 font-medium flex items-center space-x-1 transition-colors cursor-pointer"
            >
              <Ban className="w-3.5 h-3.5" />
              <span>Chặn</span>
            </button>
          </div>
        </div>
      )}

      {/* 3. Pinned Message Banner */}
      {pinnedMessage && (
        <div className="h-10 px-4 bg-slate-100 dark:bg-[#1a2530] border-b border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs animate-in slide-in-from-top-1 duration-150 select-none">
          <div
            onClick={() => {
              const el = document.getElementById(`msg-${pinnedMessage.id}`);
              el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }}
            className="flex items-center space-x-2 truncate cursor-pointer flex-1 mr-2 hover:opacity-80 transition-opacity"
            title="Bấm để xem tin nhắn đã ghim"
          >
            <Pin className="w-3.5 h-3.5 text-[#2481cc] rotate-45 flex-shrink-0" />
            <span className="font-semibold text-[#2481cc]">Tin nhắn đã ghim:</span>
            <span className="truncate text-slate-600 dark:text-slate-300">
              {pinnedMessage.content || pinnedMessage.original_name}
            </span>
          </div>
          <button
            onClick={unpinMessage}
            title="Bỏ ghim tin nhắn này"
            className="p-1 rounded-md text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700/60 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* 4. Messages List */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col space-y-1">
        {loadingMessages ? (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-400 text-xs py-16 select-none animate-in fade-in duration-150">
            <div className="w-9 h-9 border-3 border-[#2481cc]/25 border-t-[#2481cc] rounded-full animate-spin mb-3 shadow-xs" />
            <p className="font-semibold text-slate-600 dark:text-slate-300">Đang tải lịch sử tin nhắn...</p>
            <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">Vui lòng đợi trong giây lát</p>
          </div>
        ) : convMessages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-400 text-xs py-16 select-none animate-in fade-in duration-200">
            <div className="w-12 h-12 rounded-2xl bg-slate-200/50 dark:bg-[#1a2533] flex items-center justify-center text-[#2481cc] mb-2 shadow-xs">
              <MessageCircle className="w-6 h-6" />
            </div>
            <p className="font-semibold text-slate-600 dark:text-slate-300">Chưa có tin nhắn nào</p>
            <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">Gửi tin nhắn hoặc đính kèm tệp để bắt đầu cuộc trò chuyện!</p>
          </div>
        ) : (
          convMessages.map((msg) => {
            const isSelf = msg.sender_id === currentUser?.id;
            return (
              <div key={msg.id} id={`msg-${msg.id}`} className="w-full flex flex-col">
                <BubbleErrorBoundary>
                  <ChatBubble
                    message={msg}
                    isSelf={isSelf}
                    onOpenImage={(fileId, name, dataUrl) => setPreviewImage({ fileId, name, url: dataUrl })}
                    onOpenFilePreview={(fileId, name, size, type) =>
                      setPreviewFile({ fileId, name, fileSize: size, fileType: type })
                    }
                  />
                </BubbleErrorBoundary>
              </div>
            );
          })
        )}
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

      {/* 6. Universal File Preview Modal (PDF, Code, Text, Media, Office, Archive) */}
      {previewFile && (
        <FilePreviewModal
          isOpen={Boolean(previewFile)}
          onClose={() => setPreviewFile(null)}
          fileId={previewFile.fileId}
          fileName={previewFile.name}
          fileSize={previewFile.fileSize}
          fileType={previewFile.fileType}
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

class BubbleErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean }> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(error: any) {
    console.warn('[BubbleErrorBoundary] Caught message rendering error:', error);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-2 text-xs text-slate-400 italic bg-black/5 dark:bg-black/20 rounded-lg">
          [Không thể hiển thị tin nhắn này]
        </div>
      );
    }
    return this.props.children;
  }
}

