import React, { useState } from 'react';
import { Lock, User, AtSign, Eye, EyeOff } from 'lucide-react';
import { apiService } from '../../services/api';
import { useChat } from '../../context/ChatContext';

export const AuthModal: React.FC = () => {
  const { setCurrentUser } = useChat();
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (!username.trim() || !password) {
      setErrorMsg('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!');
      return;
    }

    setLoading(true);
    try {
      if (isRegister) {
        if (!fullName.trim()) {
          setErrorMsg('Vui lòng nhập họ và tên của bạn!');
          setLoading(false);
          return;
        }

        const res = await apiService.register(username.trim(), password, fullName.trim());
        if (res.success && res.user) {
          setCurrentUser(res.user);
        } else {
          setErrorMsg(res.error || 'Đăng ký thất bại. Tên đăng nhập có thể đã tồn tại.');
        }
      } else {
        const res = await apiService.login(username.trim(), password);
        if (res.success && res.user) {
          setCurrentUser(res.user);
        } else {
          setErrorMsg(res.error || 'Sai tên đăng nhập hoặc mật khẩu!');
        }
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Lỗi kết nối máy chủ. Hãy đảm bảo server Python đang chạy!');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 select-none">
      <div className="w-full max-w-sm bg-white dark:bg-[#17212b] border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl p-6 flex flex-col animate-in zoom-in-95 duration-150">
        {/* Brand Icon */}
        <div className="flex flex-col items-center mb-6">
          <img
            src="/logo.png"
            alt="Vibe Người Tốt"
            className="w-16 h-16 rounded-2xl object-cover shadow-lg border-2 border-amber-300 dark:border-amber-400 bg-amber-300 mb-3"
          />
          <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100">
            {isRegister ? 'Tạo Tài Khoản Mới' : 'Đăng Nhập Vibe Người Tốt'}
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Ứng dụng nhắn tin an toàn, tốc độ cao và bảo mật
          </p>
        </div>

        {/* Error message */}
        {errorMsg && (
          <div className="mb-4 p-2.5 rounded-xl bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-600 dark:text-red-400 text-xs font-medium text-center">
            {errorMsg}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-3">
          {isRegister && (
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                Họ và tên
              </label>
              <div className="relative flex items-center">
                <User className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Ví dụ: Vũ Duy Thái Sơn"
                  className="w-full h-10 pl-9 pr-3 rounded-xl bg-slate-100 dark:bg-[#242f3d] text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-[#2481cc]"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
              Tên tài khoản (Username)
            </label>
            <div className="relative flex items-center">
              <AtSign className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="vd: thaison99"
                className="w-full h-10 pl-9 pr-3 rounded-xl bg-slate-100 dark:bg-[#242f3d] text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-[#2481cc]"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
              Mật khẩu
            </label>
            <div className="relative flex items-center">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full h-10 pl-9 pr-10 rounded-xl bg-slate-100 dark:bg-[#242f3d] text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-[#2481cc]"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full h-10 mt-2 rounded-xl bg-[#2481cc] hover:bg-[#1d73b8] active:scale-98 text-white font-semibold text-xs transition-all shadow-md shadow-[#2481cc]/25 disabled:opacity-50"
          >
            {loading ? 'Đang xử lý...' : isRegister ? 'Đăng Ký Tài Khoản' : 'Đăng Nhập'}
          </button>
        </form>

        {/* Toggle Mode */}
        <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 text-center text-xs text-slate-500">
          {isRegister ? 'Đã có tài khoản?' : 'Chưa có tài khoản?'}{' '}
          <button
            type="button"
            onClick={() => {
              setIsRegister(!isRegister);
              setErrorMsg('');
            }}
            className="text-[#2481cc] font-semibold hover:underline"
          >
            {isRegister ? 'Đăng nhập ngay' : 'Đăng ký tài khoản mới'}
          </button>
        </div>
      </div>
    </div>
  );
};

