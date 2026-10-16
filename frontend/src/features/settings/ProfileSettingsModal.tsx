import React, { useState, useRef, useEffect } from 'react';
import {
  X,
  ArrowLeft,
  Bell,
  Moon,
  Sun,
  Lock,
  Cloud,
  Users,
  KeyRound,
  LogOut,
  Check,
  Shield,
  ChevronRight,
  Camera,
  Phone,
  Smartphone,
  Trash2
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { getInitials } from '../../lib/utils';
import { apiService } from '../../services/api';

interface ProfileSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenContacts?: () => void;
}

const AVATAR_COLORS = [
  '#2481cc', // Telegram Blue
  '#2563eb', // Royal Blue
  '#0d9488', // Teal
  '#059669', // Emerald
  '#16a34a', // Green
  '#d97706', // Amber
  '#ea580c', // Orange
  '#e11d48', // Rose
  '#7c3aed', // Violet
  '#9333ea', // Purple
];

export const ProfileSettingsModal: React.FC<ProfileSettingsModalProps> = ({
  isOpen,
  onClose,
  onOpenContacts,
}) => {
  const {
    currentUser,
    setCurrentUser,
    theme,
    setTheme,
    setIsLocked,
    openSavedMessages,
    logout,
    refreshConversations,
  } = useChat();

  const [activeSubView, setActiveSubView] = useState<'main' | 'edit_profile' | 'change_password' | 'pin_code' | 'phone_verification'>('main');

  // Edit profile state
  const [fullName, setFullName] = useState(currentUser?.full_name || '');
  const [selectedColor, setSelectedColor] = useState(currentUser?.avatar_color || '#2481cc');
  const [previewAvatarUrl, setPreviewAvatarUrl] = useState<string>(currentUser?.avatar_url || '');
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Phone verification state
  const [phoneNumber, setPhoneNumber] = useState(currentUser?.phone_number || '');
  const [otpCode, setOtpCode] = useState('');
  const [sentOtp, setSentOtp] = useState<string | null>(null);
  const [otpCountdown, setOtpCountdown] = useState<number>(0);
  const [smsAlert, setSmsAlert] = useState<{ code: string; time: string } | null>(null);

  // Change password state
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Lock screen PIN state
  const [pinCode, setPinCode] = useState('');
  const [confirmPinCode, setConfirmPinCode] = useState('');

  // Notifications toggle (saved in localStorage)
  const [soundEnabled, setSoundEnabled] = useState<boolean>(() => {
    return localStorage.getItem('vibe_notification_sound') !== 'false';
  });

  // Countdown timer cho OTP
  useEffect(() => {
    if (otpCountdown > 0) {
      const timer = setTimeout(() => setOtpCountdown(otpCountdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [otpCountdown]);

  // Cập nhật state khi currentUser thay đổi
  useEffect(() => {
    if (currentUser) {
      setFullName(currentUser.full_name || '');
      setSelectedColor(currentUser.avatar_color || '#2481cc');
      setPreviewAvatarUrl(currentUser.avatar_url || '');
      setPhoneNumber(currentUser.phone_number || '');
    }
  }, [currentUser, isOpen]);

  if (!isOpen || !currentUser) return null;

  const handleToggleSound = () => {
    const next = !soundEnabled;
    setSoundEnabled(next);
    localStorage.setItem('vibe_notification_sound', String(next));
  };

  // Xử lý nén và chọn ảnh avatar từ máy tính
  const handleAvatarFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setErrorMsg('Vui lòng chọn tệp hình ảnh hợp lệ (PNG, JPG, WEBP, GIF)!');
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const MAX_SIZE = 256;
        let width = img.width;
        let height = img.height;
        if (width > height) {
          if (width > MAX_SIZE) {
            height = Math.round((height * MAX_SIZE) / width);
            width = MAX_SIZE;
          }
        } else {
          if (height > MAX_SIZE) {
            width = Math.round((width * MAX_SIZE) / height);
            height = MAX_SIZE;
          }
        }
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.drawImage(img, 0, 0, width, height);
          const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
          setPreviewAvatarUrl(dataUrl);
          setErrorMsg(null);
        }
      };
      img.src = event.target?.result as string;
    };
    reader.readAsDataURL(file);
  };

  const handleSaveProfile = async () => {
    if (!fullName.trim()) {
      setErrorMsg('Họ và tên không được để trống!');
      return;
    }
    setIsSaving(true);
    setErrorMsg(null);
    try {
      const res = await apiService.updateProfile(currentUser.id, {
        full_name: fullName.trim(),
        avatar_color: selectedColor,
        avatar_url: previewAvatarUrl || '',
      });
      if (res && res.success && res.user) {
        setCurrentUser(res.user);
        localStorage.setItem('vibe_user', JSON.stringify(res.user));
        setSuccessMsg('Đã cập nhật hồ sơ & ảnh đại diện thành công!');
        await refreshConversations();
        setTimeout(() => {
          setSuccessMsg(null);
          setActiveSubView('main');
        }, 800);
      } else {
        setErrorMsg(res.error || 'Cập nhật hồ sơ thất bại!');
      }
    } catch (e: any) {
      setErrorMsg(e.message || 'Lỗi kết nối máy chủ!');
    } finally {
      setIsSaving(false);
    }
  };

  // Gửi mã OTP xác minh số điện thoại từ Backend Server
  const handleSendOtp = async () => {
    const cleanPhone = phoneNumber.trim().replace(/\s+/g, '');
    if (!cleanPhone || cleanPhone.length < 9) {
      setErrorMsg('Vui lòng nhập số điện thoại hợp lệ (từ 9 đến 11 số)!');
      return;
    }
    setIsSaving(true);
    setErrorMsg(null);
    try {
      const res = await apiService.requestPhoneOtp(currentUser.id, cleanPhone);
      if (res && res.success && res.otp_code) {
        setSentOtp(res.otp_code);
        setSmsAlert({
          code: res.otp_code,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        });
        setOtpCountdown(60);
        setSuccessMsg(`Mã OTP bảo mật đã được tạo bởi máy chủ cho ${cleanPhone}`);

        // Phát thông báo Toast Notification của hệ thống Windows
        try {
          if ('Notification' in window) {
            if (Notification.permission === 'granted') {
              new Notification('Vibe Messenger - Mã xác thực OTP', {
                body: `Mã OTP xác thực số điện thoại ${cleanPhone} của bạn là: ${res.otp_code}. Có hiệu lực trong 5 phút.`,
              });
            } else if (Notification.permission !== 'denied') {
              Notification.requestPermission().then((perm) => {
                if (perm === 'granted') {
                  new Notification('Vibe Messenger - Mã xác thực OTP', {
                    body: `Mã OTP xác thực số điện thoại ${cleanPhone} của bạn là: ${res.otp_code}. Có hiệu lực trong 5 phút.`,
                  });
                }
              });
            }
          }
        } catch (notifErr) {
          console.warn('Notification error:', notifErr);
        }
      } else {
        setErrorMsg(res.error || 'Không thể tạo mã OTP từ máy chủ!');
      }
    } catch (e: any) {
      setErrorMsg(e.message || 'Lỗi kết nối máy chủ khi yêu cầu mã OTP!');
    } finally {
      setIsSaving(false);
    }
  };

  // Xác minh mã OTP số điện thoại với Backend Server
  const handleVerifyOtp = async () => {
    if (!otpCode.trim() || otpCode.trim().length !== 6) {
      setErrorMsg('Mã OTP phải bao gồm đúng 6 chữ số!');
      return;
    }
    setIsSaving(true);
    setErrorMsg(null);
    try {
      const cleanPhone = phoneNumber.trim().replace(/\s+/g, '');
      const res = await apiService.verifyPhoneOtp(currentUser.id, cleanPhone, otpCode.trim());
      if (res && res.success && res.user) {
        setCurrentUser(res.user);
        localStorage.setItem('vibe_user', JSON.stringify(res.user));
        setSuccessMsg('🎉 Số điện thoại đã được xác minh thành công trên hệ thống!');
        setOtpCode('');
        setSentOtp(null);
        await refreshConversations();
        setTimeout(() => {
          setSuccessMsg(null);
          setSmsAlert(null);
          setActiveSubView('main');
        }, 1200);
      } else {
        setErrorMsg(res.error || 'Mã OTP không chính xác hoặc đã hết hiệu lực (5 phút)!');
      }
    } catch (e: any) {
      setErrorMsg(e.message || 'Lỗi kết nối máy chủ khi xác thực OTP!');
    } finally {
      setIsSaving(false);
    }
  };

  // Gỡ số điện thoại
  const handleRemovePhone = async () => {
    setIsSaving(true);
    setErrorMsg(null);
    try {
      const res = await apiService.updateProfile(currentUser.id, {
        phone_number: '',
        is_phone_verified: 0,
      });
      if (res && res.success && res.user) {
        setCurrentUser(res.user);
        localStorage.setItem('vibe_user', JSON.stringify(res.user));
        setPhoneNumber('');
        setSuccessMsg('Đã xóa số điện thoại khỏi tài khoản!');
        setTimeout(() => {
          setSuccessMsg(null);
          setActiveSubView('main');
        }, 800);
      } else {
        setErrorMsg(res.error || 'Lỗi khi gỡ số điện thoại!');
      }
    } catch (e: any) {
      setErrorMsg(e.message || 'Lỗi kết nối máy chủ!');
    } finally {
      setIsSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (!newPassword) {
      setErrorMsg('Vui lòng nhập mật khẩu mới!');
      return;
    }
    if (newPassword !== confirmPassword) {
      setErrorMsg('Mật khẩu xác nhận không khớp!');
      return;
    }
    setIsSaving(true);
    setErrorMsg(null);
    try {
      const res = await apiService.updateProfile(currentUser.id, {
        new_password: newPassword,
      });
      if (res && res.success) {
        setSuccessMsg('Đã đổi mật khẩu thành công!');
        setNewPassword('');
        setConfirmPassword('');
        setTimeout(() => {
          setSuccessMsg(null);
          setActiveSubView('main');
        }, 1000);
      } else {
        setErrorMsg(res.error || 'Đổi mật khẩu thất bại!');
      }
    } catch (e: any) {
      setErrorMsg(e.message || 'Lỗi khi đổi mật khẩu!');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSavePin = async (remove = false) => {
    setIsSaving(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      if (remove) {
        const res = await apiService.updateProfile(currentUser.id, { pin_code: '' });
        if (res && res.success && res.user) {
          setCurrentUser(res.user);
          localStorage.setItem('vibe_user', JSON.stringify(res.user));
          localStorage.removeItem(`vibe_pin_${currentUser.id}`);
          setSuccessMsg('Đã tắt mã PIN khóa màn hình!');
          setPinCode('');
          setConfirmPinCode('');
          setTimeout(() => {
            setSuccessMsg(null);
            setActiveSubView('main');
          }, 800);
        } else {
          setErrorMsg(res.error || 'Không thể tắt mã PIN!');
        }
        return;
      }

      const cleanPin = pinCode.trim();
      if (!cleanPin || cleanPin.length !== 4 || !/^\d{4}$/.test(cleanPin)) {
        setErrorMsg('Mã PIN bắt buộc phải đúng 4 chữ số (0-9)!');
        return;
      }
      if (cleanPin !== confirmPinCode.trim()) {
        setErrorMsg('Mã PIN xác nhận không trùng khớp!');
        return;
      }

      const res = await apiService.updateProfile(currentUser.id, { pin_code: cleanPin });
      if (res && res.success && res.user) {
        setCurrentUser(res.user);
        localStorage.setItem('vibe_user', JSON.stringify(res.user));
        localStorage.setItem(`vibe_pin_${currentUser.id}`, cleanPin);
        setSuccessMsg('Đã thiết lập mã PIN 4 số thành công!');
        setPinCode('');
        setConfirmPinCode('');
        setTimeout(() => {
          setSuccessMsg(null);
          setActiveSubView('main');
        }, 800);
      } else {
        setErrorMsg(res.error || 'Lỗi khi cài đặt mã PIN!');
      }
    } catch (e: any) {
      setErrorMsg(e.message || 'Lỗi kết nối máy chủ!');
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
        className="w-full max-w-sm bg-white dark:bg-[#17212b] border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl flex flex-col overflow-hidden max-h-[90vh] animate-in zoom-in-95 duration-150"
      >
        {/* Top Header */}
        <div className="h-14 px-4 border-b border-slate-100 dark:border-slate-800/80 flex items-center justify-between bg-white dark:bg-[#17212b]">
          <div className="flex items-center space-x-2.5">
            {activeSubView !== 'main' ? (
              <button
                onClick={() => {
                  setErrorMsg(null);
                  setSuccessMsg(null);
                  setActiveSubView('main');
                }}
                className="p-1.5 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
            ) : null}
            <h3 className="font-bold text-base text-slate-800 dark:text-slate-100">
              {activeSubView === 'main'
                ? 'Cài đặt'
                : activeSubView === 'edit_profile'
                ? 'Chỉnh sửa hồ sơ'
                : activeSubView === 'change_password'
                ? 'Đổi mật khẩu'
                : activeSubView === 'pin_code'
                ? 'Cài đặt mã PIN'
                : 'Xác minh số điện thoại'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto">
          {activeSubView === 'main' ? (
            <div className="flex flex-col pb-4">
              {/* Telegram-style Avatar Profile Card */}
              <div className="flex flex-col items-center justify-center pt-6 pb-5 px-4 bg-gradient-to-b from-blue-500/5 dark:from-blue-500/10 to-transparent">
                <div className="relative group/avatar cursor-pointer" onClick={() => setActiveSubView('edit_profile')} title="Nhấn để đổi ảnh đại diện hoặc họ tên">
                  <div
                    className="w-24 h-24 rounded-full flex items-center justify-center text-white font-bold text-2xl shadow-xl transition-transform group-hover/avatar:scale-105 overflow-hidden ring-4 ring-blue-500/20"
                    style={{ backgroundColor: currentUser.avatar_color || '#2481cc' }}
                  >
                    {currentUser.avatar_url ? (
                      <img src={currentUser.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
                    ) : (
                      getInitials(currentUser.full_name)
                    )}
                  </div>
                  <div className="absolute bottom-0 right-0 p-1.5 rounded-full bg-[#2481cc] text-white shadow-md border-2 border-white dark:border-[#17212b]">
                    <Camera className="w-3.5 h-3.5" />
                  </div>
                </div>

                <h2 className="mt-3.5 text-base font-bold text-slate-800 dark:text-slate-100 flex items-center space-x-1.5">
                  <span>{currentUser.full_name}</span>
                </h2>
                <div className="flex items-center space-x-1.5 mt-0.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-xs text-emerald-500 font-medium">Trực tuyến</span>
                </div>
              </div>

              {/* Account Info Section */}
              <div className="mx-4 my-2 p-3 rounded-2xl bg-slate-50 dark:bg-[#202b36] border border-slate-200/60 dark:border-slate-800/80 space-y-2.5">
                {/* Phone Number row */}
                <div
                  onClick={() => {
                    setErrorMsg(null);
                    setSuccessMsg(null);
                    setActiveSubView('phone_verification');
                  }}
                  className="flex items-center justify-between text-xs cursor-pointer hover:opacity-80 transition-opacity"
                  title="Nhấn để thiết lập hoặc xác minh số điện thoại"
                >
                  <span className="text-slate-500 dark:text-slate-400 flex items-center space-x-1.5">
                    <Phone className="w-3.5 h-3.5 text-emerald-500" />
                    <span>Số điện thoại</span>
                  </span>
                  <div className="flex items-center space-x-1.5">
                    <span className="font-semibold text-slate-800 dark:text-slate-100 font-mono">
                      {currentUser.phone_number || 'Chưa thiết lập'}
                    </span>
                    {currentUser.phone_number && currentUser.is_phone_verified ? (
                      <span className="px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 flex items-center space-x-0.5">
                        <Check className="w-2.5 h-2.5 stroke-[3]" />
                        <span>Đã xác minh</span>
                      </span>
                    ) : (
                      <span className="px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400">
                        {currentUser.phone_number ? 'Chưa xác minh' : 'Thêm ngay'}
                      </span>
                    )}
                  </div>
                </div>

                <div className="h-px bg-slate-200/60 dark:bg-slate-700/60" />

                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500 dark:text-slate-400">Tên người dùng</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-100 font-mono">
                    @{currentUser.username}
                  </span>
                </div>

                <div className="h-px bg-slate-200/60 dark:bg-slate-700/60" />

                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500 dark:text-slate-400">Mã định danh ID</span>
                  <span className="font-semibold text-[#2481cc] font-mono">
                    #{currentUser.id}
                  </span>
                </div>
              </div>

              {/* Settings Action Items List */}
              <div className="mx-4 mt-2 rounded-2xl bg-slate-50 dark:bg-[#202b36] border border-slate-200/60 dark:border-slate-800/80 overflow-hidden divide-y divide-slate-200/50 dark:divide-slate-700/50">
                {/* 1. Edit Profile & Avatar */}
                <button
                  onClick={() => setActiveSubView('edit_profile')}
                  className="w-full px-3.5 py-3 text-left hover:bg-slate-100 dark:hover:bg-slate-700/50 flex items-center justify-between text-xs transition-colors cursor-pointer"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-7 h-7 rounded-lg bg-blue-500/15 text-[#2481cc] flex items-center justify-center">
                      <Camera className="w-4 h-4" />
                    </div>
                    <span className="font-medium text-slate-700 dark:text-slate-200">
                      Chỉnh sửa hồ sơ & Ảnh đại diện
                    </span>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                </button>

                {/* 2. Phone Verification */}
                <button
                  onClick={() => {
                    setErrorMsg(null);
                    setSuccessMsg(null);
                    setActiveSubView('phone_verification');
                  }}
                  className="w-full px-3.5 py-3 text-left hover:bg-slate-100 dark:hover:bg-slate-700/50 flex items-center justify-between text-xs transition-colors cursor-pointer"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-7 h-7 rounded-lg bg-teal-500/15 text-teal-500 flex items-center justify-center">
                      <Phone className="w-4 h-4" />
                    </div>
                    <div className="flex flex-col">
                      <span className="font-medium text-slate-700 dark:text-slate-200">
                        Số điện thoại & Xác minh
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        currentUser.phone_number && currentUser.is_phone_verified
                          ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
                          : 'bg-amber-500/15 text-amber-600 dark:text-amber-400'
                      }`}
                    >
                      {currentUser.phone_number && currentUser.is_phone_verified
                        ? 'Đã xác minh'
                        : currentUser.phone_number
                        ? 'Chờ xác minh'
                        : 'Chưa thêm'}
                    </span>
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                  </div>
                </button>

                {/* 2. Saved Messages / Cloud */}
                <button
                  onClick={() => {
                    onClose();
                    openSavedMessages();
                  }}
                  className="w-full px-3.5 py-3 text-left hover:bg-slate-100 dark:hover:bg-slate-700/50 flex items-center justify-between text-xs transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-7 h-7 rounded-lg bg-indigo-500/15 text-indigo-500 flex items-center justify-center">
                      <Cloud className="w-4 h-4" />
                    </div>
                    <span className="font-medium text-slate-700 dark:text-slate-200">
                      Cloud của tôi (Saved Messages)
                    </span>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                </button>

                {/* 3. Contacts & Friends */}
                {onOpenContacts && (
                  <button
                    onClick={() => {
                      onClose();
                      onOpenContacts();
                    }}
                    className="w-full px-3.5 py-3 text-left hover:bg-slate-100 dark:hover:bg-slate-700/50 flex items-center justify-between text-xs transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-7 h-7 rounded-lg bg-emerald-500/15 text-emerald-500 flex items-center justify-center">
                        <Users className="w-4 h-4" />
                      </div>
                      <span className="font-medium text-slate-700 dark:text-slate-200">
                        Danh bạ & Bạn bè
                      </span>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                  </button>
                )}

                {/* 4. Notification Sounds */}
                <button
                  onClick={handleToggleSound}
                  className="w-full px-3.5 py-3 text-left hover:bg-slate-100 dark:hover:bg-slate-700/50 flex items-center justify-between text-xs transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-7 h-7 rounded-lg bg-rose-500/15 text-rose-500 flex items-center justify-center">
                      <Bell className="w-4 h-4" />
                    </div>
                    <span className="font-medium text-slate-700 dark:text-slate-200">
                      Âm thanh thông báo
                    </span>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      soundEnabled
                        ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
                        : 'bg-slate-200 dark:bg-slate-700 text-slate-500'
                    }`}
                  >
                    {soundEnabled ? 'Bật' : 'Tắt'}
                  </span>
                </button>

                {/* 5. Theme Toggle */}
                <button
                  onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                  className="w-full px-3.5 py-3 text-left hover:bg-slate-100 dark:hover:bg-slate-700/50 flex items-center justify-between text-xs transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-7 h-7 rounded-lg bg-amber-500/15 text-amber-500 flex items-center justify-center">
                      {theme === 'dark' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
                    </div>
                    <span className="font-medium text-slate-700 dark:text-slate-200">
                      Giao diện (Chủ đề)
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400 capitalize">
                    {theme === 'dark' ? 'Giao diện Tối' : 'Giao diện Sáng'}
                  </span>
                </button>

                {/* 6. Change Password */}
                <button
                  onClick={() => setActiveSubView('change_password')}
                  className="w-full px-3.5 py-3 text-left hover:bg-slate-100 dark:hover:bg-slate-700/50 flex items-center justify-between text-xs transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-7 h-7 rounded-lg bg-violet-500/15 text-violet-500 flex items-center justify-center">
                      <KeyRound className="w-4 h-4" />
                    </div>
                    <span className="font-medium text-slate-700 dark:text-slate-200">
                      Đổi mật khẩu tài khoản
                    </span>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                </button>

                {/* 7. Set PIN Code */}
                <button
                  onClick={() => {
                    setErrorMsg(null);
                    setSuccessMsg(null);
                    setPinCode('');
                    setConfirmPinCode('');
                    setActiveSubView('pin_code');
                  }}
                  className="w-full px-3.5 py-3 text-left hover:bg-slate-100 dark:hover:bg-slate-700/50 flex items-center justify-between text-xs transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-7 h-7 rounded-lg bg-emerald-500/15 text-emerald-500 flex items-center justify-center">
                      <Lock className="w-4 h-4" />
                    </div>
                    <span className="font-medium text-slate-700 dark:text-slate-200">
                      Mã PIN khóa màn hình
                    </span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        currentUser.pin_code
                          ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400'
                          : 'bg-slate-200 dark:bg-slate-700 text-slate-500'
                      }`}
                    >
                      {currentUser.pin_code ? 'Đã cài đặt' : 'Chưa thiết lập'}
                    </span>
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                  </div>
                </button>

                {/* 8. App Screen Lock */}
                <button
                  onClick={() => {
                    onClose();
                    setIsLocked(true);
                  }}
                  className="w-full px-3.5 py-3 text-left hover:bg-slate-100 dark:hover:bg-slate-700/50 flex items-center justify-between text-xs transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-7 h-7 rounded-lg bg-cyan-500/15 text-cyan-500 flex items-center justify-center">
                      <Lock className="w-4 h-4" />
                    </div>
                    <span className="font-medium text-slate-700 dark:text-slate-200">
                      Khóa màn hình (Ctrl+L)
                    </span>
                  </div>
                  <Shield className="w-3.5 h-3.5 text-cyan-500" />
                </button>
              </div>

              {/* Logout Button */}
              <div className="mx-4 mt-3">
                <button
                  onClick={() => {
                    onClose();
                    logout();
                  }}
                  className="w-full py-2.5 px-4 rounded-2xl bg-red-50 hover:bg-red-100 dark:bg-red-500/10 dark:hover:bg-red-500/20 text-red-600 dark:text-red-400 font-semibold text-xs flex items-center justify-center space-x-2 transition-colors cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Đăng xuất tài khoản</span>
                </button>
              </div>
            </div>
          ) : activeSubView === 'edit_profile' ? (
            /* Sub-view: Edit Profile */
            <div className="p-5 flex flex-col space-y-4 text-xs">
              {/* Preview Avatar with Image Upload */}
              <div className="flex flex-col items-center justify-center pb-2">
                <input
                  type="file"
                  ref={fileInputRef}
                  accept="image/*"
                  onChange={handleAvatarFileSelect}
                  className="hidden"
                />

                <div
                  className="relative group/avatar cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                  title="Nhấn để tải ảnh đại diện từ máy tính"
                >
                  <div
                    className="w-24 h-24 rounded-full flex items-center justify-center text-white font-bold text-2xl shadow-xl overflow-hidden ring-4 ring-blue-500/20 transition-transform group-hover/avatar:scale-105"
                    style={{ backgroundColor: selectedColor }}
                  >
                    {previewAvatarUrl ? (
                      <img src={previewAvatarUrl} alt="Avatar" className="w-full h-full object-cover" />
                    ) : (
                      getInitials(fullName || currentUser.full_name)
                    )}
                  </div>
                  <div className="absolute inset-0 rounded-full bg-black/40 opacity-0 group-hover/avatar:opacity-100 flex flex-col items-center justify-center text-white transition-opacity">
                    <Camera className="w-6 h-6 mb-1" />
                    <span className="text-[10px] font-bold">Đổi ảnh</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2 mt-3">
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="px-3 py-1.5 rounded-xl bg-blue-500/15 hover:bg-blue-500/25 text-[#2481cc] font-semibold text-xs flex items-center space-x-1.5 transition-colors cursor-pointer"
                  >
                    <Camera className="w-3.5 h-3.5" />
                    <span>{previewAvatarUrl ? 'Đổi ảnh khác' : 'Tải ảnh từ máy'}</span>
                  </button>
                  {previewAvatarUrl && (
                    <button
                      type="button"
                      onClick={() => setPreviewAvatarUrl('')}
                      className="px-2.5 py-1.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-500 font-semibold text-xs flex items-center space-x-1 transition-colors cursor-pointer"
                      title="Gỡ ảnh tùy chỉnh, sử dụng chữ cái đại diện"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>Gỡ ảnh</span>
                    </button>
                  )}
                </div>
                <span className="text-slate-400 text-[11px] mt-1.5">Ảnh tải lên được tự động tối ưu hóa</span>
              </div>

              {/* Name Input */}
              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-200 mb-1.5">
                  Họ và tên hiển thị:
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Nhập họ và tên..."
                  className="w-full h-10 px-3.5 rounded-xl bg-slate-100 dark:bg-[#202b36] text-slate-800 dark:text-slate-100 text-xs focus:outline-none focus:ring-2 focus:ring-[#2481cc] border border-transparent dark:border-slate-700/60"
                />
              </div>

              {/* Color Presets */}
              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-200 mb-2">
                  Chọn màu sắc đại diện:
                </label>
                <div className="grid grid-cols-5 gap-2.5">
                  {AVATAR_COLORS.map((c) => (
                    <button
                      key={c}
                      onClick={() => setSelectedColor(c)}
                      className="w-10 h-10 rounded-full flex items-center justify-center transition-transform hover:scale-110 active:scale-95 shadow-sm"
                      style={{ backgroundColor: c }}
                    >
                      {selectedColor === c && <Check className="w-4 h-4 text-white stroke-[3]" />}
                    </button>
                  ))}
                </div>
              </div>

              {errorMsg && (
                <div className="p-2.5 rounded-xl bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 text-xs">
                  {errorMsg}
                </div>
              )}

              {successMsg && (
                <div className="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-semibold flex items-center space-x-1.5">
                  <Check className="w-3.5 h-3.5" />
                  <span>{successMsg}</span>
                </div>
              )}

              <button
                disabled={isSaving}
                onClick={handleSaveProfile}
                className="w-full py-2.5 rounded-xl bg-[#2481cc] hover:bg-[#1b6ca8] text-white font-bold text-xs transition-all active:scale-95 disabled:opacity-50 shadow-md shadow-blue-500/20"
              >
                {isSaving ? 'Đang lưu...' : 'Lưu Thay Đổi'}
              </button>
            </div>
          ) : activeSubView === 'change_password' ? (
            /* Sub-view: Change Password */
            <div className="p-5 flex flex-col space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-200 mb-1.5">
                  Mật khẩu mới:
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Tối thiểu 6 ký tự (Hoa, thường, số, ký tự đặc biệt)..."
                  className="w-full h-10 px-3.5 rounded-xl bg-slate-100 dark:bg-[#202b36] text-slate-800 dark:text-slate-100 text-xs focus:outline-none focus:ring-2 focus:ring-[#2481cc] border border-transparent dark:border-slate-700/60"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-200 mb-1.5">
                  Xác nhận mật khẩu mới:
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Nhập lại mật khẩu mới..."
                  className="w-full h-10 px-3.5 rounded-xl bg-slate-100 dark:bg-[#202b36] text-slate-800 dark:text-slate-100 text-xs focus:outline-none focus:ring-2 focus:ring-[#2481cc] border border-transparent dark:border-slate-700/60"
                />
              </div>

              {errorMsg && (
                <div className="p-2.5 rounded-xl bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 text-xs">
                  {errorMsg}
                </div>
              )}

              {successMsg && (
                <div className="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-semibold flex items-center space-x-1.5">
                  <Check className="w-3.5 h-3.5" />
                  <span>{successMsg}</span>
                </div>
              )}

              <button
                disabled={isSaving}
                onClick={handleChangePassword}
                className="w-full py-2.5 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-bold text-xs transition-all active:scale-95 disabled:opacity-50 shadow-md shadow-violet-500/20"
              >
                {isSaving ? 'Đang cập nhật...' : 'Cập Nhật Mật Khẩu'}
              </button>
            </div>
          ) : activeSubView === 'pin_code' ? (
            /* Sub-view: PIN Code Setup */
            <div className="p-5 flex flex-col space-y-4 text-xs">
              <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-slate-700 dark:text-slate-200 space-y-1">
                <div className="flex items-center space-x-2 font-bold text-emerald-600 dark:text-emerald-400">
                  <Shield className="w-4 h-4" />
                  <span>Mã PIN bảo mật ứng dụng</span>
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                  {currentUser.pin_code
                    ? 'Bạn đã cài mã PIN 4 số riêng. Khi khóa màn hình (Ctrl+L), chỉ bạn mới có thể mở khóa bằng mã này.'
                    : 'Thiết lập mã PIN 4 chữ số cá nhân để khóa bảo vệ ứng dụng khi bạn tạm rời máy tính.'}
                </p>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-200 mb-1.5">
                  {currentUser.pin_code ? 'Nhập mã PIN 4 số mới:' : 'Nhập mã PIN 4 chữ số:'}
                </label>
                <input
                  type="password"
                  inputMode="numeric"
                  maxLength={4}
                  value={pinCode}
                  onChange={(e) => setPinCode(e.target.value.replace(/\D/g, '').slice(0, 4))}
                  placeholder="••••"
                  className="w-full h-11 px-3.5 rounded-xl bg-slate-100 dark:bg-[#202b36] text-slate-800 dark:text-slate-100 text-center text-xl tracking-[0.6em] font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500 border border-transparent dark:border-slate-700/60"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-200 mb-1.5">
                  Xác nhận lại mã PIN 4 số:
                </label>
                <input
                  type="password"
                  inputMode="numeric"
                  maxLength={4}
                  value={confirmPinCode}
                  onChange={(e) => setConfirmPinCode(e.target.value.replace(/\D/g, '').slice(0, 4))}
                  placeholder="••••"
                  className="w-full h-11 px-3.5 rounded-xl bg-slate-100 dark:bg-[#202b36] text-slate-800 dark:text-slate-100 text-center text-xl tracking-[0.6em] font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500 border border-transparent dark:border-slate-700/60"
                />
              </div>

              {errorMsg && (
                <div className="p-2.5 rounded-xl bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 text-xs">
                  {errorMsg}
                </div>
              )}

              {successMsg && (
                <div className="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-semibold flex items-center space-x-1.5">
                  <Check className="w-3.5 h-3.5" />
                  <span>{successMsg}</span>
                </div>
              )}

              <button
                disabled={isSaving || pinCode.length !== 4 || confirmPinCode.length !== 4}
                onClick={() => handleSavePin(false)}
                className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition-all active:scale-95 disabled:opacity-50 shadow-md shadow-emerald-500/20 cursor-pointer"
              >
                {isSaving ? 'Đang lưu...' : (currentUser.pin_code ? 'Cập Nhật Mã PIN Mới' : 'Lưu Mã PIN Khóa')}
              </button>

              {currentUser.pin_code && (
                <button
                  type="button"
                  disabled={isSaving}
                  onClick={() => handleSavePin(true)}
                  className="w-full py-2 rounded-xl bg-red-50 dark:bg-red-500/10 hover:bg-red-100 dark:hover:bg-red-500/20 text-red-600 dark:text-red-400 font-semibold text-xs transition-all active:scale-95 cursor-pointer"
                >
                  Tắt / Xóa Mã PIN Này
                </button>
              )}
            </div>
          ) : (
            /* Sub-view: Phone Number & Verification (OTP) */
            <div className="p-5 flex flex-col space-y-4 text-xs">
              <div className="p-3.5 rounded-2xl bg-teal-500/10 border border-teal-500/20 text-slate-700 dark:text-slate-200 space-y-1">
                <div className="flex items-center space-x-2 font-bold text-teal-600 dark:text-teal-400">
                  <Phone className="w-4 h-4" />
                  <span>Xác thực số điện thoại chính thức</span>
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                  {currentUser.phone_number && currentUser.is_phone_verified
                    ? `Tài khoản đã liên kết và xác minh thành công với số ${currentUser.phone_number}. Người dùng khác có thể tìm thấy bạn qua số điện thoại này.`
                    : 'Nhập số điện thoại để nhận mã xác minh OTP từ Máy chủ (phát qua Thông báo Windows Toast & SMS), giúp kích hoạt tài khoản chính chủ và tìm kiếm bạn bè.'}
                </p>
              </div>

              {/* Input Phone Number */}
              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-200 mb-1.5">
                  Số điện thoại của bạn:
                </label>
                <div className="flex space-x-2">
                  <input
                    type="tel"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    placeholder="VD: 0912345678 hoặc +84..."
                    className="flex-1 h-10 px-3.5 rounded-xl bg-slate-100 dark:bg-[#202b36] text-slate-800 dark:text-slate-100 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-teal-500 border border-transparent dark:border-slate-700/60"
                  />
                  <button
                    type="button"
                    disabled={isSaving || otpCountdown > 0 || !phoneNumber.trim()}
                    onClick={handleSendOtp}
                    className="px-3.5 h-10 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs transition-all active:scale-95 disabled:opacity-50 whitespace-nowrap cursor-pointer shadow-sm"
                  >
                    {isSaving ? 'Đang tạo...' : otpCountdown > 0 ? `Gửi lại (${otpCountdown}s)` : 'Gửi mã OTP'}
                  </button>
                </div>
              </div>

              {/* Server OTP Notification Alert */}
              {smsAlert && (
                <div className="p-3.5 rounded-2xl bg-gradient-to-r from-blue-500/10 via-indigo-500/10 to-teal-500/10 border border-blue-500/30 text-slate-800 dark:text-slate-100 shadow-sm animate-in fade-in slide-in-from-top-2">
                  <div className="flex items-center justify-between mb-1.5 text-[11px] font-bold text-blue-600 dark:text-blue-400">
                    <span className="flex items-center space-x-1.5">
                      <Smartphone className="w-3.5 h-3.5" />
                      <span>MÃ XÁC THỰC MÁY CHỦ (SERVER OTP)</span>
                    </span>
                    <span className="text-[10px] text-slate-400 font-normal">{smsAlert.time}</span>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-300">
                    Mã xác thực từ máy chủ cho số điện thoại của bạn là: <strong className="text-blue-600 dark:text-blue-400 font-mono text-sm tracking-widest">{smsAlert.code}</strong>. Mã đã được lưu trữ trong CSDL và có hiệu lực 5 phút.
                  </p>
                  <button
                    type="button"
                    onClick={() => setOtpCode(smsAlert.code)}
                    className="mt-2.5 px-3 py-1 rounded-lg bg-[#2481cc] hover:bg-[#1b6ca8] text-white font-bold text-[11px] flex items-center space-x-1 transition-colors shadow-sm cursor-pointer"
                  >
                    <Check className="w-3 h-3 stroke-[3]" />
                    <span>Tự động điền mã {smsAlert.code}</span>
                  </button>
                </div>
              )}

              {/* OTP Input */}
              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-200 mb-1.5">
                  Nhập mã OTP xác thực (6 chữ số):
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="••••••"
                  className="w-full h-12 px-3.5 rounded-xl bg-slate-100 dark:bg-[#202b36] text-slate-800 dark:text-slate-100 text-center text-xl tracking-[0.8em] font-mono focus:outline-none focus:ring-2 focus:ring-teal-500 border border-transparent dark:border-slate-700/60"
                />
              </div>

              {errorMsg && (
                <div className="p-2.5 rounded-xl bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 text-xs">
                  {errorMsg}
                </div>
              )}

              {successMsg && (
                <div className="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-semibold flex items-center space-x-1.5">
                  <Check className="w-3.5 h-3.5" />
                  <span>{successMsg}</span>
                </div>
              )}

              <button
                disabled={isSaving || otpCode.length !== 6 || !sentOtp}
                onClick={handleVerifyOtp}
                className="w-full py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs transition-all active:scale-95 disabled:opacity-50 shadow-md shadow-teal-500/20 cursor-pointer"
              >
                {isSaving ? 'Đang xác minh...' : 'Xác Minh & Kích Hoạt Số Điện Thoại'}
              </button>

              {currentUser.phone_number && (
                <button
                  type="button"
                  disabled={isSaving}
                  onClick={handleRemovePhone}
                  className="w-full py-2 rounded-xl bg-red-50 dark:bg-red-500/10 hover:bg-red-100 dark:hover:bg-red-500/20 text-red-600 dark:text-red-400 font-semibold text-xs transition-all active:scale-95 cursor-pointer"
                >
                  Xóa số điện thoại này khỏi tài khoản
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
