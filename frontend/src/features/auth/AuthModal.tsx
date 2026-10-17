import React, { useState, useEffect } from 'react';
import { Lock, User, AtSign, Eye, EyeOff, MessageCircle, Server, Globe, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react';
import { apiService } from '../../services/api';
import { useChat } from '../../context/ChatContext';
import APP_LOGO from '../../assets/logo';

export const AuthModal: React.FC = () => {
  const { setCurrentUser } = useChat();
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [serverSuccessMsg, setServerSuccessMsg] = useState('');
  const [loading, setLoading] = useState(false);

  // Cấu hình máy chủ kết nối (Mặc định là máy chủ WAN Internet bore.pub:38888)
  const [serverConfig, setServerConfig] = useState<{ host: string; port: number; isWan: boolean }>({
    host: 'bore.pub',
    port: 38888,
    isWan: true,
  });
  const [showServerSettings, setShowServerSettings] = useState(false);
  const [customHost, setCustomHost] = useState('bore.pub');
  const [customPort, setCustomPort] = useState('38888');
  const [serverSwitching, setServerSwitching] = useState(false);

  useEffect(() => {
    apiService.getServerConfig().then((cfg) => {
      if (cfg && cfg.host) {
        setServerConfig(cfg);
        setCustomHost(cfg.host);
        setCustomPort(String(cfg.port));
      }
    });
  }, []);

  const handleSwitchServer = async (targetHost: string, targetPort: number) => {
    setServerSwitching(true);
    setErrorMsg('');
    setServerSuccessMsg('');
    try {
      const res = await apiService.setServerConfig(targetHost, targetPort);
      setServerConfig({ host: res.host, port: res.port, isWan: res.isWan });
      setCustomHost(res.host);
      setCustomPort(String(res.port));
      if (res.connected) {
        setServerSuccessMsg(`Đã kết nối thành công tới ${res.host}:${res.port}!`);
        setTimeout(() => {
          setShowServerSettings(false);
          setServerSuccessMsg('');
        }, 1200);
      } else {
        setErrorMsg(`Không thể kết nối tới ${res.host}:${res.port}. Hãy kiểm tra lại địa chỉ.`);
      }
    } catch (err: any) {
      setErrorMsg(`Lỗi đổi máy chủ: ${err.message}`);
    } finally {
      setServerSwitching(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setServerSuccessMsg('');

    const cleanUsername = username.trim().replace(/^@+/, '');

    if (!cleanUsername || !password) {
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

        const res = await apiService.register(cleanUsername, password, fullName.trim());
        if (res.success && res.user) {
          setCurrentUser(res.user);
        } else {
          setErrorMsg(res.error || 'Đăng ký thất bại. Tên đăng nhập có thể đã tồn tại.');
        }
      } else {
        const res = await apiService.login(cleanUsername, password);
        if (res.success && res.user) {
          setCurrentUser(res.user);
        } else {
          setErrorMsg(res.error || 'Sai tên đăng nhập hoặc mật khẩu!');
        }
      }
    } catch (err: any) {
      const msg = err.message || '';
      setShowServerSettings(true);
      setErrorMsg(
        msg.includes('quá thời gian') || msg.includes('timeout')
          ? `Kết nối tới máy chủ (${serverConfig.host}:${serverConfig.port}) quá thời gian chờ. Hãy kiểm tra kết nối mạng hoặc thử lại!`
          : (msg || `Không thể kết nối đến máy chủ (${serverConfig.host}:${serverConfig.port}). Hãy đảm bảo server đang chạy!`)
      );
    } finally {
      setLoading(false);
    }
  };

  const [logoError, setLogoError] = useState(false);

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 select-none">
      <div className="w-full max-w-sm bg-white dark:bg-[#17212b] border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl p-6 flex flex-col animate-in zoom-in-95 duration-150">
        {/* Brand Icon */}
        <div className="flex flex-col items-center mb-4">
          {logoError ? (
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-[#2481cc] to-indigo-600 flex items-center justify-center text-white shadow-lg mb-3">
              <MessageCircle className="w-8 h-8" />
            </div>
          ) : (
            <img
              src={APP_LOGO}
              alt="Vibe Người Tốt"
              onError={() => setLogoError(true)}
              className="w-16 h-16 rounded-2xl object-cover shadow-lg border-2 border-amber-300 dark:border-amber-400 bg-amber-300 mb-3"
            />
          )}
          <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100">
            {isRegister ? 'Tạo Tài Khoản Mới' : 'Đăng Nhập Vibe Người Tốt'}
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Ứng dụng nhắn tin an toàn, tốc độ cao và bảo mật
          </p>

          {/* Server status pill */}
          <div className="mt-2.5 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 dark:bg-[#242f3d] border border-slate-200 dark:border-slate-700 text-[11px] text-slate-600 dark:text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>
              {serverConfig.isWan ? '🌐 WAN: ' : '💻 Cục bộ: '}
              <strong className="font-mono text-[#2481cc]">{serverConfig.host}:{serverConfig.port}</strong>
            </span>
            <button
              type="button"
              onClick={() => setShowServerSettings(!showServerSettings)}
              className="ml-1 text-slate-400 hover:text-[#2481cc] font-medium flex items-center"
              title="Đổi địa chỉ máy chủ"
            >
              {showServerSettings ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
          </div>
        </div>

        {/* Server Config Drawer */}
        {showServerSettings && (
          <div className="mb-4 p-3 rounded-xl bg-slate-50 dark:bg-[#202b36] border border-slate-200 dark:border-slate-700 text-xs animate-in fade-in duration-150">
            <div className="font-semibold text-slate-700 dark:text-slate-200 mb-2 flex items-center gap-1.5">
              <Server className="w-3.5 h-3.5 text-[#2481cc]" />
              Chọn Máy Chủ Kết Nối
            </div>
            
            <div className="grid grid-cols-2 gap-1.5 mb-2.5">
              <button
                type="button"
                disabled={serverSwitching}
                onClick={() => handleSwitchServer('bore.pub', 38888)}
                className={`py-1.5 px-2 rounded-lg text-[11px] font-medium border flex items-center justify-center gap-1 transition-all ${
                  serverConfig.host === 'bore.pub' && serverConfig.port === 38888
                    ? 'bg-[#2481cc] text-white border-[#2481cc]'
                    : 'bg-white dark:bg-[#2b3947] text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-600 hover:border-[#2481cc]'
                }`}
              >
                <Globe className="w-3 h-3" />
                WAN (bore.pub)
              </button>

              <button
                type="button"
                disabled={serverSwitching}
                onClick={() => handleSwitchServer('127.0.0.1', 8888)}
                className={`py-1.5 px-2 rounded-lg text-[11px] font-medium border flex items-center justify-center gap-1 transition-all ${
                  serverConfig.host === '127.0.0.1' && serverConfig.port === 8888
                    ? 'bg-[#2481cc] text-white border-[#2481cc]'
                    : 'bg-white dark:bg-[#2b3947] text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-600 hover:border-[#2481cc]'
                }`}
              >
                <Server className="w-3 h-3" />
                Cục bộ (127.0.0.1)
              </button>
            </div>

            {/* Custom server address */}
            <div className="flex gap-1.5">
              <input
                type="text"
                value={customHost}
                onChange={(e) => setCustomHost(e.target.value)}
                placeholder="IP / Host (vd: bore.pub)"
                className="flex-1 h-7 px-2 rounded-lg bg-white dark:bg-[#2b3947] border border-slate-200 dark:border-slate-600 text-xs text-slate-800 dark:text-slate-100"
              />
              <input
                type="number"
                value={customPort}
                onChange={(e) => setCustomPort(e.target.value)}
                placeholder="Port"
                className="w-16 h-7 px-1.5 text-center rounded-lg bg-white dark:bg-[#2b3947] border border-slate-200 dark:border-slate-600 text-xs text-slate-800 dark:text-slate-100"
              />
              <button
                type="button"
                disabled={serverSwitching || !customHost.trim() || !customPort.trim()}
                onClick={() => handleSwitchServer(customHost.trim(), Number(customPort.trim()))}
                className="h-7 px-2.5 rounded-lg bg-[#2481cc] text-white text-[11px] font-medium hover:bg-[#1d73b8] disabled:opacity-50"
              >
                {serverSwitching ? '...' : 'Lưu'}
              </button>
            </div>
          </div>
        )}

        {/* Server Success message */}
        {serverSuccessMsg && (
          <div className="mb-4 p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-medium text-center flex items-center justify-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            {serverSuccessMsg}
          </div>
        )}

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
                placeholder="vd: thaison99 hoặc @thaison99"
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
              setServerSuccessMsg('');
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
