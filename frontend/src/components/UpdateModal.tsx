import React, { useState } from 'react';
import { Sparkles, RefreshCw, X, ArrowUpCircle, CheckCircle2, AlertCircle } from 'lucide-react';
import { apiService } from '../services/api';

export interface UpdateInfo {
  remoteHash: string;
  localHash: string;
  message: string;
}

interface UpdateModalProps {
  updateInfo: UpdateInfo;
  onDismiss: () => void;
}

export const UpdateModal: React.FC<UpdateModalProps> = ({ updateInfo, onDismiss }) => {
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleApplyUpdate = async () => {
    setIsUpdating(true);
    setError(null);
    try {
      const res = await apiService.applyUpdate();
      if (!res.success) {
        setIsUpdating(false);
        setError(res.error || 'Có lỗi xảy ra khi đồng bộ từ GitHub.');
      }
    } catch (e: any) {
      setIsUpdating(false);
      setError(e.message || 'Không thể áp dụng cập nhật.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-150 select-none">
      <div
        className="w-full max-w-md bg-white dark:bg-[#1e2c3a] border border-slate-200 dark:border-slate-700/80 rounded-2xl shadow-2xl p-6 flex flex-col space-y-4 animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-blue-500/10 dark:bg-blue-500/20 text-[#2481cc] flex items-center justify-center shadow-inner">
              <Sparkles className="w-5 h-5 text-[#2481cc]" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-slate-800 dark:text-slate-100">
                Có Bản Cập Nhật Mới!
              </h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                Phát hiện mã nguồn mới trên GitHub repository
              </p>
            </div>
          </div>
          {!isUpdating && (
            <button
              onClick={onDismiss}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Update Details Box */}
        <div className="p-3.5 bg-slate-50 dark:bg-[#17212b] border border-slate-200/70 dark:border-slate-800 rounded-xl space-y-2 text-xs">
          <div className="flex items-start space-x-2">
            <ArrowUpCircle className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <span className="font-semibold text-slate-700 dark:text-slate-200">
                Nội dung cập nhật:
              </span>
              <p className="mt-0.5 text-slate-600 dark:text-slate-300 italic font-mono bg-white dark:bg-[#202b36] p-2 rounded border border-slate-200 dark:border-slate-700/60 break-words">
                "{updateInfo.message}"
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between pt-1 text-[11px] text-slate-500 dark:text-slate-400">
            <span>Bản hiện tại: <code className="bg-slate-200 dark:bg-slate-800 px-1 py-0.5 rounded">{updateInfo.localHash.slice(0, 7)}</code></span>
            <span>➜</span>
            <span>Bản mới: <code className="bg-blue-100 dark:bg-blue-900/40 text-[#2481cc] px-1 py-0.5 rounded font-bold">{updateInfo.remoteHash.slice(0, 7)}</code></span>
          </div>
        </div>

        <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
          Bạn có quyền quyết định: Bấm <strong>"Cập nhật ngay"</strong> để tự động đồng bộ và tải tính năng mới nhất, hoặc bấm <strong>"Để sau"</strong> để tiếp tục sử dụng ứng dụng bình thường mà không bị gián đoạn.
        </p>

        {error && (
          <div className="p-2.5 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800/60 text-red-600 dark:text-red-400 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center space-x-2.5 pt-2">
          <button
            disabled={isUpdating}
            onClick={onDismiss}
            className="flex-1 py-2 px-3 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-semibold transition-colors disabled:opacity-50"
          >
            Để sau
          </button>

          <button
            disabled={isUpdating}
            onClick={handleApplyUpdate}
            className="flex-1 py-2 px-3 rounded-xl bg-[#2481cc] hover:bg-[#1d6fa5] text-white text-xs font-semibold flex items-center justify-center space-x-1.5 shadow-sm transition-all disabled:opacity-75"
          >
            {isUpdating ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Đang cập nhật...</span>
              </>
            ) : (
              <>
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Cập nhật ngay</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

