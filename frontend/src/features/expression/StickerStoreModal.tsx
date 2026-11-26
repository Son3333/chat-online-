import React from 'react';
import { X, Check, Sparkles, Download } from 'lucide-react';
import { STORE_STICKER_PACKS } from './expressionData';

interface StickerStoreModalProps {
  isOpen: boolean;
  onClose: () => void;
  installedPackIds: string[];
  onToggleInstallPack: (packId: string) => void;
}

export const StickerStoreModal: React.FC<StickerStoreModalProps> = ({
  isOpen,
  onClose,
  installedPackIds,
  onToggleInstallPack,
}) => {
  if (!isOpen) return null;

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4 select-none animate-in fade-in duration-150"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-2xl bg-white dark:bg-[#182533] border border-slate-200 dark:border-slate-700/80 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh] animate-in zoom-in-95 duration-150"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700/60 flex items-center justify-between bg-slate-50 dark:bg-[#17212b]">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-amber-500 to-rose-500 text-white flex items-center justify-center shadow-md">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-800 dark:text-slate-100 flex items-center space-x-2">
                <span>Cửa Hàng Sticker Vibe</span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-[#2481cc]/15 text-[#2481cc]">
                  Miễn phí
                </span>
              </h2>
              <p className="text-xs text-slate-400">Khám phá và thêm các bộ sticker biểu cảm phong phú</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700/60 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {STORE_STICKER_PACKS.map((pack) => {
            const isInstalled = installedPackIds.includes(pack.id);
            return (
              <div
                key={pack.id}
                className="p-4 rounded-2xl border border-slate-200 dark:border-slate-700/60 bg-slate-50/50 dark:bg-[#1e2a38]/40 hover:bg-slate-100 dark:hover:bg-[#1e2a38] transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
              >
                {/* Pack Info */}
                <div className="flex items-center space-x-4 min-w-0">
                  <img
                    src={pack.avatarUrl}
                    alt={pack.name}
                    className="w-14 h-14 rounded-2xl object-cover bg-white dark:bg-slate-800 p-1 border border-slate-200 dark:border-slate-700 flex-shrink-0 shadow-sm"
                  />
                  <div className="min-w-0">
                    <div className="flex items-center space-x-2">
                      <h3 className="font-bold text-sm text-slate-800 dark:text-slate-100 truncate">
                        {pack.name}
                      </h3>
                      <span className="text-[10px] px-2 py-0.5 rounded-md bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 flex-shrink-0">
                        {pack.category}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-1">
                      {pack.description}
                    </p>
                    <span className="text-[10px] text-slate-400 mt-1 block">
                      Tác giả: {pack.author} • {pack.stickers.length} stickers
                    </span>
                  </div>
                </div>

                {/* Stickers Thumbnail Strip & Action */}
                <div className="flex items-center space-x-3 self-end sm:self-center flex-shrink-0">
                  <div className="hidden md:flex items-center -space-x-1.5 mr-2">
                    {pack.stickers.slice(0, 4).map((stk) => (
                      <img
                        key={stk.id}
                        src={stk.url}
                        alt=""
                        className="w-7 h-7 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-0.5"
                      />
                    ))}
                  </div>

                  <button
                    onClick={() => onToggleInstallPack(pack.id)}
                    className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 transition-all shadow-sm active:scale-95 cursor-pointer ${
                      isInstalled
                        ? 'bg-rose-500/10 text-rose-500 hover:bg-rose-500 hover:text-white border border-rose-500/20'
                        : 'bg-[#2481cc] hover:bg-[#1d73b8] text-white shadow-md shadow-[#2481cc]/25'
                    }`}
                  >
                    {isInstalled ? (
                      <>
                        <Check className="w-3.5 h-3.5" />
                        <span>Đã thêm (Gỡ)</span>
                      </>
                    ) : (
                      <>
                        <Download className="w-3.5 h-3.5" />
                        <span>Thêm bộ sticker</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-200 dark:border-slate-700/60 bg-slate-50 dark:bg-[#17212b] flex items-center justify-between text-xs text-slate-400">
          <span>Kho sticker tự do & bản quyền sáng tạo bởi cộng đồng Vibe</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-slate-200 dark:bg-slate-700/80 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 font-semibold transition-colors"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
};
