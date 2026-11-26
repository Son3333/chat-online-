import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  Image as ImageIcon,
  FileText,
  Pin,
  Download,
  User,
  Phone,
  Video,
  Users,
  Crown,
  Shield,
  VolumeX,
  Volume2,
  UserMinus,
  LogOut,
  MoreVertical,
  AlertTriangle,
  Camera,
  Edit2,
  Edit3,
  Check,
  UserPlus,
  Search
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { getInitials, formatTime } from '../../lib/utils';
import { apiService } from '../../services/api';
import { ConversationMember } from '../../types';
import {
  getGroupRoleRank,
  getGroupRoleLabel,
  isGroupTopLeader,
  isGroupLeaderOrCoLeader,
  isGroupPrivileged,
} from '../../lib/groupPermissions';

interface ChatInfoModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialOpenAddMember?: boolean;
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

      <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-1 px-1.5">
        <p className="text-[9px] text-white/90 truncate">{name}</p>
      </div>
    </div>
  );
};

export const ChatInfoModal: React.FC<ChatInfoModalProps> = ({ isOpen, onClose, initialOpenAddMember }) => {
  const { activeConv, setActiveConv, setMessages, refreshConversations, messages, startCall, currentUser, friends } = useChat();
  const isGroup = activeConv?.type === 'group';
  const isDirect = activeConv?.type === 'direct';

  const [activeTab, setActiveTab] = useState<'members' | 'media' | 'files' | 'pinned'>(
    isGroup ? 'members' : 'media'
  );
  const [previewImage, setPreviewImage] = useState<{ fileId: string; name: string; url?: string } | null>(null);

  // Group members state
  const [members, setMembers] = useState<ConversationMember[]>([]);
  const [loadingMembers, setLoadingMembers] = useState(false);
  const [selectedMember, setSelectedMember] = useState<ConversationMember | null>(null);

  // Modals & Popups
  const [kickModalMember, setKickModalMember] = useState<ConversationMember | null>(null);
  const [muteModalMember, setMuteModalMember] = useState<ConversationMember | null>(null);
  const [customMuteText, setCustomMuteText] = useState('');
  const [showGroupMuteModal, setShowGroupMuteModal] = useState(false);
  const [customGroupMuteText, setCustomGroupMuteText] = useState(activeConv?.custom_mute_text || '');
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [leaveSilent, setLeaveSilent] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showAddMemberModal, setShowAddMemberModal] = useState(false);
  const [addMemberSearch, setAddMemberSearch] = useState('');
  const [selectedFriendIds, setSelectedFriendIds] = useState<number[]>([]);
  const [addMemberError, setAddMemberError] = useState('');

  useEffect(() => {
    if (isOpen && initialOpenAddMember && isGroup) {
      setActiveTab('members');
      setSelectedFriendIds([]);
      setAddMemberSearch('');
      setAddMemberError('');
      setShowAddMemberModal(true);
    }
  }, [isOpen, initialOpenAddMember, isGroup]);

  // Nickname & Group Info states
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [newGroupTitle, setNewGroupTitle] = useState('');
  const [nicknameModalMember, setNicknameModalMember] = useState<ConversationMember | null>(null);
  const [memberNicknameInput, setMemberNicknameInput] = useState('');
  const groupAvatarInputRef = useRef<HTMLInputElement>(null);

  // Handle change group name
  const handleSaveGroupName = async () => {
    if (!newGroupTitle.trim() || !activeConv || !currentUser) return;
    setIsProcessing(true);
    try {
      const res = await apiService.updateGroupInfo(activeConv.id, currentUser.id, { title: newGroupTitle.trim() });
      if (res && res.success) {
        setActiveConv({ ...activeConv, title: newGroupTitle.trim() });
        setIsEditingTitle(false);
        refreshConversations();
      } else {
        alert(res?.error || 'Không thể đổi tên nhóm!');
      }
    } catch (e: any) {
      alert(e.message || 'Không thể cập nhật tên nhóm lúc này!');
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle change group avatar
  const handleGroupAvatarUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !activeConv || !currentUser) return;
    if (file.size > 5 * 1024 * 1024) {
      alert('Vui lòng chọn ảnh có dung lượng dưới 5MB!');
      return;
    }
    const reader = new FileReader();
    reader.onload = async () => {
      const base64 = reader.result as string;
      setIsProcessing(true);
      try {
        const res = await apiService.updateGroupInfo(activeConv.id, currentUser.id, { avatar_url: base64 });
        if (res && res.success) {
          setActiveConv({ ...activeConv, avatar_url: base64 });
          refreshConversations();
        } else {
          alert(res?.error || 'Không thể cập nhật ảnh đại diện nhóm!');
        }
      } catch (err: any) {
        alert(err.message || 'Lỗi khi gửi ảnh đại diện!');
      } finally {
        setIsProcessing(false);
      }
    };
    reader.readAsDataURL(file);
  };

  // Handle set nickname for member
  const handleSaveMemberNickname = async () => {
    if (!nicknameModalMember || !activeConv || !currentUser) return;
    setIsProcessing(true);
    const targetId = Number(nicknameModalMember.user_id || nicknameModalMember.id);
    try {
      const res = await apiService.setConversationNickname(
        activeConv.id,
        currentUser.id,
        targetId,
        memberNicknameInput.trim()
      );
      if (res && res.success) {
        setMembers((prev) =>
          prev.map((m) =>
            Number(m.user_id || m.id) === targetId ? { ...m, nickname: memberNicknameInput.trim() } : m
          )
        );
        setActiveConv({
          ...activeConv,
          nicknames: { ...(activeConv.nicknames || {}), [targetId]: memberNicknameInput.trim() }
        });
        setNicknameModalMember(null);
        setMemberNicknameInput('');
        refreshConversations();
      } else {
        alert(res?.error || 'Không thể đặt biệt danh!');
      }
    } catch (err: any) {
      alert(err.message || 'Không thể hoàn tất thao tác. Vui lòng kiểm tra lại kết nối mạng!');
    } finally {
      setIsProcessing(false);
    }
  };

  // Fetch members when group modal opens
  const fetchMembers = async () => {
    if (!activeConv || !isGroup) return;
    setLoadingMembers(true);
    try {
      const res = await apiService.getConversationMembers(activeConv.id);
      if (res && res.members) {
        setMembers(res.members);
      }
    } catch (e) {
      console.warn('Error fetching group members:', e);
    } finally {
      setLoadingMembers(false);
    }
  };

  useEffect(() => {
    if (isOpen && isGroup) {
      fetchMembers();
      setActiveTab('members');
    } else if (isOpen) {
      setActiveTab('media');
    }
  }, [isOpen, activeConv?.id, isGroup]);

  useEffect(() => {
    if (!isOpen || !isGroup) return;
    return apiService.onServerEvent((event) => {
      if (['member_role_updated', 'member_kicked', 'member_mute_updated', 'refresh_conversations'].includes(event.type)) {
        fetchMembers();
      }
    });
  }, [isOpen, isGroup, activeConv?.id]);

  if (!isOpen || !activeConv || !currentUser) return null;

  // Filter media, files, pinned messages
  const mediaMsgs = messages.filter((m) => m.msg_type === 'image' && !m.is_deleted);
  const fileMsgs = messages.filter((m) => m.msg_type === 'file' && !m.is_deleted);
  const pinnedMsgs = messages.filter((m) => m.is_pinned && !m.is_deleted);

  const myRole = activeConv.my_role || 'member';
  const myRank = getGroupRoleRank(myRole);

  // Permission checks aligned with backend ROLE_RANKS (owner/admin=4, co_leader=3, deputy=2, member=1)
  const canKick = (target: ConversationMember) => {
    const tId = Number(target.user_id || target.id);
    if (tId === currentUser.id) return false;
    const targetRank = getGroupRoleRank(target.role);
    if (myRank >= 4) return targetRank < 4;
    if (myRank === 3 && targetRank < 3) return true;
    if (myRank === 2 && targetRank < 2) return true;
    return false;
  };

  const canMute = (target: ConversationMember) => {
    const tId = Number(target.user_id || target.id);
    if (tId === currentUser.id) return false;
    const targetRank = getGroupRoleRank(target.role);
    if (myRank >= 4) return targetRank < 4;
    if (myRank === 3 && targetRank < 3) return true;
    if (myRank === 2 && targetRank < 2) return true;
    return false;
  };

  const canPromote = (target: ConversationMember) => {
    const tId = Number(target.user_id || target.id);
    if (tId === currentUser.id) return false;
    const targetRank = getGroupRoleRank(target.role);
    if (myRank >= 4) return targetRank < 4;
    if (myRank === 3 && targetRank < 3) return true;
    return false;
  };

  const handleConfirmAddMembers = async () => {
    if (!activeConv || selectedFriendIds.length === 0) return;
    setIsProcessing(true);
    setAddMemberError('');
    try {
      let addedCount = 0;
      let lastError = '';
      for (const friendId of selectedFriendIds) {
        const res = await apiService.addGroupMember(activeConv.id, friendId);
        if (res && res.success) {
          addedCount++;
        } else if (res?.message) {
          lastError = res.message;
        }
      }
      if (addedCount > 0) {
        const memRes = await apiService.getConversationMembers(activeConv.id);
        if (memRes && memRes.success && memRes.members) {
          setMembers(memRes.members);
        }
        await refreshConversations();
        setSelectedFriendIds([]);
        setAddMemberSearch('');
        setShowAddMemberModal(false);
      } else {
        setAddMemberError(lastError || 'Không thể thêm thành viên vào nhóm.');
      }
    } catch (e: any) {
      setAddMemberError(e?.message || 'Không thể thêm thành viên vào nhóm.');
    } finally {
      setIsProcessing(false);
    }
  };

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

  // Kick member action
  const handleConfirmKick = async () => {
    if (!kickModalMember) return;
    setIsProcessing(true);
    try {
      const targetId = Number(kickModalMember.user_id || kickModalMember.id);
      const res = await apiService.kickMember(activeConv.id, currentUser.id, targetId);
      if (res && res.success) {
        setKickModalMember(null);
        setSelectedMember(null);
        await fetchMembers();
        refreshConversations();
      } else {
        alert(res.error || 'Không thể kích thành viên này!');
      }
    } catch (e: any) {
      alert(e.message || 'Không thể hoàn tất thao tác. Vui lòng kiểm tra lại kết nối mạng!');
    } finally {
      setIsProcessing(false);
    }
  };

  // Set member mute
  const handleConfirmMute = async (isMuted: boolean, targetMember?: ConversationMember) => {
    const target = targetMember || muteModalMember;
    if (!target) return;
    setIsProcessing(true);
    try {
      const targetId = Number(target.user_id || target.id);
      const res = await apiService.setMemberMute(
        activeConv.id,
        currentUser.id,
        targetId,
        isMuted,
        isMuted ? customMuteText.trim() : undefined
      );
      if (res && res.success) {
        setMuteModalMember(null);
        setSelectedMember(null);
        setCustomMuteText('');
        await fetchMembers();
      } else {
        alert(res?.message || res?.error || 'Lỗi thao tác cấm ngôn!');
      }
    } catch (e: any) {
      alert(e.message || 'Không thể hoàn tất thao tác. Vui lòng kiểm tra lại kết nối mạng!');
    } finally {
      setIsProcessing(false);
    }
  };

  // Update member role
  const handleSetRole = async (targetUserId: number, newRole: string) => {
    setIsProcessing(true);
    try {
      const res = await apiService.updateMemberRole(activeConv.id, currentUser.id, targetUserId, newRole);
      if (res && res.success) {
        setSelectedMember(null);
        await fetchMembers();
        refreshConversations();
      } else {
        alert(res.error || 'Không thể thay đổi quyền hạn thành viên!');
      }
    } catch (e: any) {
      alert(e.message || 'Không thể hoàn tất thao tác. Vui lòng kiểm tra lại kết nối mạng!');
    } finally {
      setIsProcessing(false);
    }
  };

  // Group mute toggle
  const handleToggleGroupMute = async (enable: boolean) => {
    setIsProcessing(true);
    try {
      const res = await apiService.setGroupMute(
        activeConv.id,
        currentUser.id,
        enable,
        customGroupMuteText.trim() || 'Nhóm đang ở chế độ cấm chat (Chỉ Ban quản trị được phát ngôn)'
      );
      if (res && res.success) {
        setShowGroupMuteModal(false);
        setActiveConv({ ...activeConv, is_muted: enable ? 1 : 0, custom_mute_text: customGroupMuteText.trim() });
        refreshConversations();
      } else {
        alert(res.error || 'Lỗi cài đặt cấm chat nhóm!');
      }
    } catch (e: any) {
      alert(e.message || 'Không thể hoàn tất thao tác. Vui lòng kiểm tra lại kết nối mạng!');
    } finally {
      setIsProcessing(false);
    }
  };

  // Leave group
  const handleConfirmLeaveGroup = async () => {
    setIsProcessing(true);
    try {
      const res = await apiService.leaveGroup(activeConv.id, currentUser.id, leaveSilent);
      if (res && res.success) {
        setShowLeaveModal(false);
        onClose();
        setActiveConv(null);
        setMessages([]);
        refreshConversations();
      } else {
        alert(res.error || 'Lỗi khi rời khỏi nhóm!');
      }
    } catch (e: any) {
      alert(e.message || 'Không thể hoàn tất thao tác. Vui lòng kiểm tra lại kết nối mạng!');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in select-none">
      <div className="w-[440px] max-h-[88vh] bg-white dark:bg-[#17212b] rounded-3xl shadow-2xl border border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="h-14 px-5 border-b border-slate-200 dark:border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {isGroup ? <Users className="w-5 h-5 text-[#2481cc]" /> : <User className="w-5 h-5 text-[#2481cc]" />}
            <h3 className="font-bold text-base text-slate-800 dark:text-slate-100">
              {isGroup ? 'Thông tin nhóm' : 'Thông tin hội thoại'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Profile Card */}
        <div className="p-5 flex flex-col items-center border-b border-slate-100 dark:border-slate-800/50 bg-slate-50/50 dark:bg-[#1c2733]/40">
          <div className="relative group mb-3">
            <div
              className="w-20 h-20 rounded-full flex items-center justify-center font-bold text-white text-2xl shadow-lg overflow-hidden ring-4 ring-blue-500/10"
              style={{ backgroundColor: activeConv.avatar_color || (isGroup ? '#06b6d4' : '#2481cc') }}
            >
              {activeConv.avatar_url ? (
                <img src={activeConv.avatar_url} alt="" className="w-full h-full object-cover" />
              ) : (
                getInitials(activeConv.title)
              )}
            </div>
            {isGroup && isGroupLeaderOrCoLeader(myRole) && (
              <>
                <input
                  type="file"
                  ref={groupAvatarInputRef}
                  onChange={handleGroupAvatarUpload}
                  accept="image/*"
                  className="hidden"
                />
                <button
                  type="button"
                  onClick={() => groupAvatarInputRef.current?.click()}
                  className="absolute bottom-0 right-0 p-1.5 rounded-full bg-[#2481cc] text-white shadow-md hover:bg-blue-600 transition-transform active:scale-95 cursor-pointer"
                  title="Đổi ảnh đại diện nhóm"
                >
                  <Camera className="w-3.5 h-3.5" />
                </button>
              </>
            )}
          </div>

          {isGroup && isEditingTitle ? (
            <div className="flex items-center space-x-1.5 my-1">
              <input
                type="text"
                value={newGroupTitle}
                onChange={(e) => setNewGroupTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSaveGroupName();
                  if (e.key === 'Escape') setIsEditingTitle(false);
                }}
                className="px-2.5 py-1 text-sm rounded-xl bg-white dark:bg-[#202b36] border border-blue-500 text-slate-900 dark:text-slate-100 outline-none font-semibold text-center"
                autoFocus
              />
              <button
                type="button"
                onClick={handleSaveGroupName}
                disabled={isProcessing}
                className="p-1.5 rounded-lg bg-emerald-500 text-white hover:bg-emerald-600 cursor-pointer"
                title="Lưu tên nhóm"
              >
                <Check className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => setIsEditingTitle(false)}
                className="p-1.5 rounded-lg bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-200 hover:bg-slate-300 cursor-pointer"
                title="Hủy"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-1.5 justify-center">
              <h4 className="font-bold text-lg text-slate-900 dark:text-slate-100 text-center">
                {activeConv.title}
              </h4>
              {isGroup && isGroupLeaderOrCoLeader(myRole) && (
                <button
                  type="button"
                  onClick={() => {
                    setNewGroupTitle(activeConv.title || '');
                    setIsEditingTitle(true);
                  }}
                  className="p-1 rounded-lg text-slate-400 hover:text-[#2481cc] hover:bg-blue-50 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                  title="Đổi tên nhóm"
                >
                  <Edit2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          )}
          {activeConv.partner_username && (
            <span className="text-xs text-[#2481cc] font-medium mt-0.5">
              @{activeConv.partner_username}
            </span>
          )}
          <span className="text-xs mt-1">
            {isGroup ? (
              <span className="text-slate-400 font-medium">
                Nhóm trò chuyện • {members.length > 0 ? members.length : (activeConv.member_count || 0)} thành viên
              </span>
            ) : activeConv.is_online ? (
              <span className="text-emerald-500 font-medium flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>Đang trực tuyến</span>
              </span>
            ) : (
              <span className="text-slate-400 font-medium">Ngoại tuyến</span>
            )}
          </span>

          {/* Quick call buttons for Direct */}
          {isDirect && (
            <div className="flex items-center space-x-3 mt-4">
              <button
                onClick={() => {
                  onClose();
                  startCall('voice');
                }}
                className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/50 text-xs font-semibold transition-colors cursor-pointer"
              >
                <Phone className="w-3.5 h-3.5" />
                <span>Gọi thoại</span>
              </button>
              <button
                onClick={() => {
                  onClose();
                  startCall('video');
                }}
                className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-900/50 text-xs font-semibold transition-colors cursor-pointer"
              >
                <Video className="w-3.5 h-3.5" />
                <span>Gọi video</span>
              </button>
            </div>
          )}
        </div>

        {/* Tab Selector */}
        <div className="flex border-b border-slate-200 dark:border-slate-800 text-xs font-semibold">
          {isGroup && (
            <button
              onClick={() => setActiveTab('members')}
              className={`flex-1 py-3 flex items-center justify-center space-x-1.5 border-b-2 transition-colors ${
                activeTab === 'members'
                  ? 'border-[#2481cc] text-[#2481cc]'
                  : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400'
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              <span>Thành viên ({members.length > 0 ? members.length : (activeConv.member_count || 0)})</span>
            </button>
          )}
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
        <div className="flex-1 overflow-y-auto p-4 min-h-[260px]">
          {/* Members Tab */}
          {isGroup && activeTab === 'members' && (
            <div className="space-y-3">
              {/* Add Member Action Button */}
              {isGroupPrivileged(myRole) && (
                <button
                  type="button"
                  onClick={() => {
                    setSelectedFriendIds([]);
                    setAddMemberSearch('');
                    setAddMemberError('');
                    setShowAddMemberModal(true);
                  }}
                  className="w-full py-2.5 px-3 rounded-2xl bg-[#2481cc]/10 hover:bg-[#2481cc]/20 text-[#2481cc] border border-[#2481cc]/20 flex items-center justify-center space-x-2 text-xs font-semibold transition-colors cursor-pointer"
                >
                  <UserPlus className="w-4 h-4" />
                  <span>Thêm thành viên vào nhóm</span>
                </button>
              )}

              {/* Group Mute Admin Banner */}
              {isGroupLeaderOrCoLeader(myRole) && (
                <div className="p-3 rounded-2xl bg-slate-50 dark:bg-[#202b36] border border-slate-200/60 dark:border-slate-700/60 flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2.5">
                    {activeConv.is_muted ? (
                      <VolumeX className="w-4 h-4 text-red-500" />
                    ) : (
                      <Volume2 className="w-4 h-4 text-emerald-500" />
                    )}
                    <div>
                      <span className="font-semibold text-slate-800 dark:text-slate-100 block">
                        Cấm chat toàn nhóm
                      </span>
                      <span className="text-[10px] text-slate-400">
                        {activeConv.is_muted ? 'Chỉ Ban quản trị được gửi tin' : 'Mọi thành viên đều được gửi tin'}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      if (activeConv.is_muted) {
                        handleToggleGroupMute(false);
                      } else {
                        setShowGroupMuteModal(true);
                      }
                    }}
                    className={`px-3 py-1 rounded-xl font-bold text-[11px] transition-colors cursor-pointer ${
                      activeConv.is_muted
                        ? 'bg-emerald-500/15 text-emerald-600 hover:bg-emerald-500/25'
                        : 'bg-red-500/15 text-red-600 hover:bg-red-500/25'
                    }`}
                  >
                    {activeConv.is_muted ? 'Mở lại chat' : 'Khóa mõm cả nhóm'}
                  </button>
                </div>
              )}

              {/* Members List */}
              <div className="divide-y divide-slate-100 dark:divide-slate-800/80">
                {loadingMembers ? (
                  <div className="py-8 flex flex-col items-center justify-center text-slate-400 text-xs">
                    <div className="w-5 h-5 rounded-full border-2 border-[#2481cc] border-t-transparent animate-spin mb-2" />
                    <span>Đang tải danh sách thành viên...</span>
                  </div>
                ) : members.length === 0 ? (
                  <div className="py-8 text-center text-slate-400 text-xs">
                    Chưa có danh sách thành viên
                  </div>
                ) : (
                  members.map((m) => {
                  const mId = Number(m.user_id || m.id);
                  const isMe = mId === currentUser.id;
                  const memberRole = m.role || 'member';

                  return (
                    <div
                      key={mId}
                      className="py-2.5 flex items-center justify-between text-xs hover:bg-slate-50/60 dark:hover:bg-slate-800/30 px-2 rounded-xl transition-colors"
                    >
                      <div className="flex items-center space-x-3 overflow-hidden">
                        <div
                          className="w-9 h-9 rounded-full flex items-center justify-center font-bold text-white text-xs flex-shrink-0 overflow-hidden ring-2 ring-blue-500/10"
                          style={{ backgroundColor: m.avatar_color || '#2481cc' }}
                        >
                          {m.avatar_url ? (
                            <img src={m.avatar_url} alt="" className="w-full h-full object-cover" />
                          ) : (
                            getInitials(m.full_name)
                          )}
                        </div>
                        <div className="truncate">
                          <div className="flex items-center space-x-1.5">
                            <span className="font-semibold text-slate-800 dark:text-slate-100 truncate">
                              {m.nickname ? `${m.nickname} (${m.full_name})` : m.full_name} {isMe && '(Bạn)'}
                            </span>
                            {/* Role Badge */}
                            {isGroupTopLeader(memberRole) ? (
                              <span className="px-1.5 py-0.2 rounded-full text-[9px] font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 flex items-center space-x-0.5">
                                <Crown className="w-2.5 h-2.5" />
                                <span>{getGroupRoleLabel(memberRole)}</span>
                              </span>
                            ) : memberRole === 'co_leader' ? (
                              <span className="px-1.5 py-0.2 rounded-full text-[9px] font-bold bg-purple-500/15 text-purple-600 dark:text-purple-400 flex items-center space-x-0.5">
                                <Shield className="w-2.5 h-2.5" />
                                <span>Đồng thủ lĩnh</span>
                              </span>
                            ) : memberRole === 'deputy' ? (
                              <span className="px-1.5 py-0.2 rounded-full text-[9px] font-bold bg-blue-500/15 text-blue-600 dark:text-blue-400 flex items-center space-x-0.5">
                                <Shield className="w-2.5 h-2.5" />
                                <span>Phó nhóm</span>
                              </span>
                            ) : (
                              <span className="px-1.5 py-0.2 rounded-full text-[9px] text-slate-400 bg-slate-100 dark:bg-slate-800">
                                Thành viên
                              </span>
                            )}
                          </div>
                          <div className="flex items-center space-x-1.5 mt-0.5">
                            <span className="text-[10px] text-slate-400 font-mono">@{m.username}</span>
                            {Boolean(m.is_muted) && (
                              <span className="text-[9px] font-bold text-red-500 bg-red-500/10 px-1 rounded flex items-center space-x-0.5">
                                <VolumeX className="w-2.5 h-2.5" />
                                <span>Bị khóa mõm</span>
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Action Menu Trigger */}
                      <div className="relative">
                        <button
                          type="button"
                          onClick={() => setSelectedMember(Number(selectedMember?.user_id || selectedMember?.id) === mId ? null : m)}
                          className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200/60 dark:hover:bg-slate-700/60 cursor-pointer"
                          title="Tùy chọn"
                        >
                          <MoreVertical className="w-4 h-4" />
                        </button>

                        {/* Dropdown Menu */}
                        {Number(selectedMember?.user_id || selectedMember?.id) === mId && (
                          <div className="absolute right-0 top-8 z-20 w-44 bg-white dark:bg-[#1f2b38] rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700/80 p-1.5 divide-y divide-slate-100 dark:divide-slate-700/50 animate-in fade-in zoom-in-95">
                            {/* Nickname Option */}
                            <div className="py-1">
                              <button
                                type="button"
                                onClick={() => {
                                  setNicknameModalMember(m);
                                  setMemberNicknameInput(m.nickname || '');
                                  setSelectedMember(null);
                                }}
                                className="w-full px-2.5 py-1.5 text-left text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg flex items-center space-x-1.5 cursor-pointer"
                              >
                                <Edit3 className="w-3.5 h-3.5" />
                                <span>Đặt biệt danh</span>
                              </button>
                            </div>

                            {/* Promotion Options */}
                            {!isMe && canPromote(m) && (
                              <div className="py-1">
                                {isGroupTopLeader(myRole) && memberRole !== 'co_leader' && (
                                  <button
                                    onClick={() => handleSetRole(mId, 'co_leader')}
                                    className="w-full px-2.5 py-1.5 text-left text-xs font-medium text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg flex items-center space-x-1.5 cursor-pointer"
                                  >
                                    <Shield className="w-3.5 h-3.5" />
                                    <span>Lên Đồng thủ lĩnh</span>
                                  </button>
                                )}
                                {memberRole !== 'deputy' && (
                                  <button
                                    onClick={() => handleSetRole(mId, 'deputy')}
                                    className="w-full px-2.5 py-1.5 text-left text-xs font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg flex items-center space-x-1.5 cursor-pointer"
                                  >
                                    <Shield className="w-3.5 h-3.5" />
                                    <span>Lên Phó nhóm</span>
                                  </button>
                                )}
                                {memberRole !== 'member' && (
                                  <button
                                    onClick={() => handleSetRole(mId, 'member')}
                                    className="w-full px-2.5 py-1.5 text-left text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700/50 rounded-lg flex items-center space-x-1.5 cursor-pointer"
                                  >
                                    <User className="w-3.5 h-3.5" />
                                    <span>Về Thành viên</span>
                                  </button>
                                )}
                              </div>
                            )}

                            {/* Mute / Unmute Option */}
                            {!isMe && canMute(m) && (
                              <div className="py-1">
                                {m.is_muted ? (
                                  <button
                                    onClick={() => handleConfirmMute(false, m)}
                                    className="w-full px-2.5 py-1.5 text-left text-xs font-medium text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 rounded-lg flex items-center space-x-1.5 cursor-pointer"
                                  >
                                    <Volume2 className="w-3.5 h-3.5" />
                                    <span>Mở khóa mõm</span>
                                  </button>
                                ) : (
                                  <button
                                    onClick={() => {
                                      setMuteModalMember(m);
                                      setCustomMuteText(`Bạn bị khóa mõm bởi ${currentUser.full_name}`);
                                    }}
                                    className="w-full px-2.5 py-1.5 text-left text-xs font-medium text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 rounded-lg flex items-center space-x-1.5 cursor-pointer"
                                  >
                                    <VolumeX className="w-3.5 h-3.5" />
                                    <span>Khóa mõm cá nhân</span>
                                  </button>
                                )}
                              </div>
                            )}

                            {/* Kick Option */}
                            {!isMe && canKick(m) && (
                              <div className="pt-1">
                                <button
                                  onClick={() => setKickModalMember(m)}
                                  className="w-full px-2.5 py-1.5 text-left text-xs font-bold text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg flex items-center space-x-1.5 cursor-pointer"
                                >
                                  <UserMinus className="w-3.5 h-3.5" />
                                  <span>Kích khỏi nhóm</span>
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
              </div>

              {/* Leave Group Button */}
              <div className="pt-4 mt-2 border-t border-slate-100 dark:border-slate-800">
                <button
                  onClick={() => setShowLeaveModal(true)}
                  className="w-full py-2.5 rounded-xl bg-red-50 hover:bg-red-100 dark:bg-red-500/10 dark:hover:bg-red-500/20 text-red-600 dark:text-red-400 font-bold text-xs flex items-center justify-center space-x-2 transition-colors cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Rời khỏi nhóm này</span>
                </button>
              </div>
            </div>
          )}

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
                        className="p-1.5 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors flex-shrink-0 cursor-pointer"
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

        {/* Kick Confirmation Modal */}
        {kickModalMember && (
          <div className="fixed inset-0 z-[70] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in">
            <div className="w-full max-w-xs bg-white dark:bg-[#1a232f] rounded-2xl p-5 shadow-2xl border border-red-500/20 space-y-3">
              <div className="flex items-center space-x-2 text-red-600 dark:text-red-400 font-bold text-sm">
                <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                <span>Xác nhận kích thành viên</span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                Bạn có chắc chắn muốn kích <strong>{kickModalMember.full_name}</strong> khỏi nhóm không?
              </p>
              <div className="p-2.5 rounded-xl bg-red-500/10 text-red-600 dark:text-red-400 text-[11px] font-medium leading-relaxed">
                ⚠️ Cảnh báo: Toàn bộ đoạn chat và quyền truy cập nhóm này sẽ bị <strong>xóa vĩnh viễn</strong> đối với thành viên bị kích!
              </div>
              <div className="flex space-x-2 pt-1">
                <button
                  type="button"
                  disabled={isProcessing}
                  onClick={() => setKickModalMember(null)}
                  className="flex-1 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-semibold text-xs cursor-pointer"
                >
                  Hủy
                </button>
                <button
                  type="button"
                  disabled={isProcessing}
                  onClick={handleConfirmKick}
                  className="flex-1 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs shadow-md shadow-red-500/20 cursor-pointer"
                >
                  {isProcessing ? 'Đang kích...' : 'Kích ngay'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Custom Mute Member Modal */}
        {muteModalMember && (
          <div className="fixed inset-0 z-[70] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in">
            <div className="w-full max-w-xs bg-white dark:bg-[#1a232f] rounded-2xl p-5 shadow-2xl border border-amber-500/20 space-y-3 text-xs">
              <div className="flex items-center space-x-2 text-amber-600 dark:text-amber-400 font-bold text-sm">
                <VolumeX className="w-5 h-5 flex-shrink-0" />
                <span>Khóa mõm: {muteModalMember.full_name}</span>
              </div>
              <p className="text-slate-600 dark:text-slate-300">
                Nhập thông báo hiển thị tại ô nhập chat của thành viên khi bị đóng băng:
              </p>
              <input
                type="text"
                value={customMuteText}
                onChange={(e) => setCustomMuteText(e.target.value)}
                placeholder="VD: Bạn bị khóa mõm bởi [Tên]..."
                className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#242f3d] text-slate-800 dark:text-slate-100 text-xs focus:ring-2 focus:ring-amber-500 outline-none"
              />
              <div className="flex space-x-2 pt-1">
                <button
                  type="button"
                  disabled={isProcessing}
                  onClick={() => setMuteModalMember(null)}
                  className="flex-1 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-semibold cursor-pointer"
                >
                  Hủy
                </button>
                <button
                  type="button"
                  disabled={isProcessing}
                  onClick={() => handleConfirmMute(true)}
                  className="flex-1 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-bold shadow-md cursor-pointer"
                >
                  {isProcessing ? 'Đang lưu...' : 'Khóa mõm'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Group Mute Settings Modal */}
        {showGroupMuteModal && (
          <div className="fixed inset-0 z-[70] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in">
            <div className="w-full max-w-xs bg-white dark:bg-[#1a232f] rounded-2xl p-5 shadow-2xl border border-red-500/20 space-y-3 text-xs">
              <div className="flex items-center space-x-2 text-red-600 dark:text-red-400 font-bold text-sm">
                <VolumeX className="w-5 h-5 flex-shrink-0" />
                <span>Cấm chat toàn bộ nhóm</span>
              </div>
              <p className="text-slate-600 dark:text-slate-300">
                Toàn bộ thành viên thường sẽ bị đóng băng ô nhập. Nhập thông báo hiển thị cho nhóm:
              </p>
              <input
                type="text"
                value={customGroupMuteText}
                onChange={(e) => setCustomGroupMuteText(e.target.value)}
                placeholder="Nhóm đang ở chế độ cấm chat..."
                className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#242f3d] text-slate-800 dark:text-slate-100 text-xs focus:ring-2 focus:ring-red-500 outline-none"
              />
              <div className="flex space-x-2 pt-1">
                <button
                  type="button"
                  disabled={isProcessing}
                  onClick={() => setShowGroupMuteModal(false)}
                  className="flex-1 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-semibold cursor-pointer"
                >
                  Hủy
                </button>
                <button
                  type="button"
                  disabled={isProcessing}
                  onClick={() => handleToggleGroupMute(true)}
                  className="flex-1 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold shadow-md cursor-pointer"
                >
                  {isProcessing ? 'Đang bật...' : 'Bật cấm chat'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Leave Group Modal (Silent vs Notice) */}
        {showLeaveModal && (
          <div className="fixed inset-0 z-[70] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in">
            <div className="w-full max-w-xs bg-white dark:bg-[#1a232f] rounded-2xl p-5 shadow-2xl border border-red-500/20 space-y-3 text-xs">
              <div className="flex items-center space-x-2 text-red-600 dark:text-red-400 font-bold text-sm">
                <LogOut className="w-5 h-5 flex-shrink-0" />
                <span>Rời khỏi nhóm trò chuyện</span>
              </div>
              <p className="text-slate-600 dark:text-slate-300">
                Chọn phương thức bạn muốn rời khỏi nhóm:
              </p>

              <div className="space-y-2">
                <label className="flex items-center space-x-2.5 p-2.5 rounded-xl border border-slate-200/80 dark:border-slate-700/80 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <input
                    type="radio"
                    name="leave_type"
                    checked={leaveSilent === true}
                    onChange={() => setLeaveSilent(true)}
                    className="text-[#2481cc]"
                  />
                  <div>
                    <span className="font-bold text-slate-800 dark:text-slate-100 block">Rời trong im lặng</span>
                    <span className="text-[10px] text-slate-400">Không gửi thông báo vào nhóm</span>
                  </div>
                </label>

                <label className="flex items-center space-x-2.5 p-2.5 rounded-xl border border-slate-200/80 dark:border-slate-700/80 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <input
                    type="radio"
                    name="leave_type"
                    checked={leaveSilent === false}
                    onChange={() => setLeaveSilent(false)}
                    className="text-[#2481cc]"
                  />
                  <div>
                    <span className="font-bold text-slate-800 dark:text-slate-100 block">Rời có thông báo</span>
                    <span className="text-[10px] text-slate-400">Gửi tin thông báo vào nhóm</span>
                  </div>
                </label>
              </div>

              <div className="p-2.5 rounded-xl bg-red-500/10 text-red-600 dark:text-red-400 text-[11px] font-medium">
                Mặc định toàn bộ lịch sử tin nhắn của nhóm sẽ được xóa sạch khỏi tài khoản của bạn.
              </div>

              <div className="flex space-x-2 pt-1">
                <button
                  type="button"
                  disabled={isProcessing}
                  onClick={() => setShowLeaveModal(false)}
                  className="flex-1 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-semibold cursor-pointer"
                >
                  Hủy
                </button>
                <button
                  type="button"
                  disabled={isProcessing}
                  onClick={handleConfirmLeaveGroup}
                  className="flex-1 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold shadow-md cursor-pointer"
                >
                  {isProcessing ? 'Đang rời...' : 'Rời nhóm'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Nickname Modal */}
        {nicknameModalMember && (
          <div className="fixed inset-0 z-[70] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in">
            <div className="w-full max-w-xs bg-white dark:bg-[#1a232f] rounded-2xl p-5 shadow-2xl border border-blue-500/20 space-y-3 text-xs">
              <div className="flex items-center space-x-2 text-blue-600 dark:text-blue-400 font-bold text-sm">
                <Edit3 className="w-5 h-5 flex-shrink-0" />
                <span>Đặt biệt danh</span>
              </div>
              <p className="text-slate-600 dark:text-slate-300">
                Đặt biệt danh cho <strong>{nicknameModalMember.full_name}</strong> trong cuộc trò chuyện này:
              </p>
              <input
                type="text"
                value={memberNicknameInput}
                onChange={(e) => setMemberNicknameInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSaveMemberNickname();
                }}
                placeholder="Nhập biệt danh (để trống để xóa)..."
                className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#242f3d] text-slate-800 dark:text-slate-100 text-xs focus:ring-2 focus:ring-blue-500 outline-none"
                autoFocus
              />
              <div className="flex space-x-2 pt-1">
                <button
                  type="button"
                  disabled={isProcessing}
                  onClick={() => setNicknameModalMember(null)}
                  className="flex-1 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-semibold cursor-pointer"
                >
                  Hủy
                </button>
                <button
                  type="button"
                  disabled={isProcessing}
                  onClick={handleSaveMemberNickname}
                  className="flex-1 py-2 rounded-xl bg-[#2481cc] hover:bg-blue-600 text-white font-bold shadow-md cursor-pointer"
                >
                  {isProcessing ? 'Đang lưu...' : 'Lưu biệt danh'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Add Member Modal */}
        {showAddMemberModal && (
          <div
            onClick={() => !isProcessing && setShowAddMemberModal(false)}
            className="fixed inset-0 z-[70] bg-black/60 backdrop-blur-xs flex items-center justify-center p-4"
          >
            <div
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-sm bg-white dark:bg-[#1e2c3a] rounded-3xl p-5 border border-slate-200 dark:border-slate-700/80 shadow-2xl animate-in zoom-in-95 flex flex-col max-h-[80vh]"
            >
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-700/60">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 rounded-xl bg-[#2481cc]/15 text-[#2481cc] flex items-center justify-center">
                    <UserPlus className="w-4 h-4" />
                  </div>
                  <h3 className="font-bold text-sm text-slate-800 dark:text-slate-100">
                    Thêm thành viên
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={() => !isProcessing && setShowAddMemberModal(false)}
                  className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {addMemberError && (
                <div className="mt-3 p-2 rounded-xl bg-red-500/10 border border-red-500/20 text-red-500 text-xs text-center">
                  {addMemberError}
                </div>
              )}

              <div className="relative mt-3">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={addMemberSearch}
                  onChange={(e) => setAddMemberSearch(e.target.value)}
                  placeholder="Tìm bạn bè để thêm..."
                  className="w-full h-9 pl-8 pr-3 rounded-xl bg-slate-100 dark:bg-[#242f3d] text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-[#2481cc]"
                />
              </div>

              <div className="flex-1 overflow-y-auto mt-3 space-y-1 min-h-[160px] max-h-[260px] pr-1">
                {(() => {
                  const existingIds = new Set(members.map((m) => Number(m.user_id || m.id)));
                  const availableFriends = friends.filter((f) => {
                    if (existingIds.has(Number(f.id))) return false;
                    if (!addMemberSearch.trim()) return true;
                    const q = addMemberSearch.toLowerCase();
                    return (
                      f.full_name.toLowerCase().includes(q) ||
                      f.username.toLowerCase().includes(q)
                    );
                  });

                  if (availableFriends.length === 0) {
                    return (
                      <div className="py-10 text-center text-xs text-slate-400">
                        Không có bạn bè phù hợp để thêm vào nhóm.
                      </div>
                    );
                  }

                  return availableFriends.map((friend) => {
                    const fId = Number(friend.id);
                    const isSelected = selectedFriendIds.includes(fId);
                    return (
                      <div
                        key={fId}
                        onClick={() =>
                          setSelectedFriendIds((prev) =>
                            prev.includes(fId) ? prev.filter((id) => id !== fId) : [...prev, fId]
                          )
                        }
                        className={`p-2 rounded-xl flex items-center justify-between cursor-pointer transition-colors ${
                          isSelected
                            ? 'bg-[#2481cc]/15 text-[#2481cc]'
                            : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200'
                        }`}
                      >
                        <div className="flex items-center space-x-2.5 min-w-0">
                          <div
                            className="w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs text-white flex-shrink-0 overflow-hidden"
                            style={{ backgroundColor: friend.avatar_color || '#2563eb' }}
                          >
                            {friend.avatar_url ? (
                              <img src={friend.avatar_url} alt="" className="w-full h-full object-cover" />
                            ) : (
                              getInitials(friend.full_name)
                            )}
                          </div>
                          <div className="flex flex-col text-xs truncate">
                            <span className="font-semibold truncate">{friend.full_name}</span>
                            <span className="text-[10px] opacity-70 truncate">@{friend.username}</span>
                          </div>
                        </div>
                        <div
                          className={`w-4 h-4 rounded-md border flex items-center justify-center flex-shrink-0 ${
                            isSelected
                              ? 'bg-[#2481cc] border-[#2481cc] text-white'
                              : 'border-slate-300 dark:border-slate-600'
                          }`}
                        >
                          {isSelected && <Check className="w-3 h-3" />}
                        </div>
                      </div>
                    );
                  });
                })()}
              </div>

              <div className="flex items-center space-x-2 mt-4 pt-3 border-t border-slate-100 dark:border-slate-700/60">
                <button
                  type="button"
                  disabled={isProcessing}
                  onClick={() => setShowAddMemberModal(false)}
                  className="flex-1 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-200"
                >
                  Hủy
                </button>
                <button
                  type="button"
                  disabled={isProcessing || selectedFriendIds.length === 0}
                  onClick={handleConfirmAddMembers}
                  className="flex-1 py-2 rounded-xl bg-[#2481cc] hover:bg-[#1d73b8] disabled:opacity-50 text-white text-xs font-semibold shadow-sm"
                >
                  {isProcessing ? 'Đang thêm...' : `Thêm (${selectedFriendIds.length})`}
                </button>
              </div>
            </div>
          </div>
        )}

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
                  className="p-2 text-white/80 hover:text-white rounded-full bg-white/10 hover:bg-white/20 transition-colors cursor-pointer"
                  title="Tải ảnh về máy"
                >
                  <Download className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setPreviewImage(null)}
                  className="p-2 text-white/80 hover:text-white rounded-full bg-white/10 hover:bg-white/20 transition-colors cursor-pointer"
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
