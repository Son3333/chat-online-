import React, { useState, useMemo } from 'react';
import {
  Search,
  Clock,
  Star,
  Smile,
  Sticker as StickerIcon,
  Film,
  Plus,
  X,
  Trash2,
} from 'lucide-react';
import { StickerItem, StickerPack, GifItem } from '../../types';
import {
  EMOJI_CATEGORIES,
  DEFAULT_STICKER_PACKS,
  STORE_STICKER_PACKS,
  DEFAULT_GIFS,
  removeVietnameseTones,
} from './expressionData';
import { StickerStoreModal } from './StickerStoreModal';

interface ExpressionHubProps {
  onSelectEmoji: (emoji: string) => void;
  onSelectSticker: (sticker: StickerItem, pack: StickerPack) => void;
  onSelectGif: (gif: GifItem) => void;
  onClose?: () => void;
}

export const ExpressionHub: React.FC<ExpressionHubProps> = ({
  onSelectEmoji,
  onSelectSticker,
  onSelectGif,
  onClose,
}) => {
  const [activeMainTab, setActiveMainTab] = useState<'recent' | 'favorites' | 'emoji' | 'sticker' | 'gif'>('emoji');
  const [searchQuery, setSearchQuery] = useState('');
  const [isStoreOpen, setIsStoreOpen] = useState(false);

  // Danh sách các bộ sticker đã cài đặt
  const [installedPackIds, setInstalledPackIds] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem('vibe_installed_sticker_packs');
      return saved ? JSON.parse(saved) : DEFAULT_STICKER_PACKS.map((p) => p.id);
    } catch {
      return DEFAULT_STICKER_PACKS.map((p) => p.id);
    }
  });

  // Pack sticker đang chọn xem
  const [activePackId, setActivePackId] = useState<string>(DEFAULT_STICKER_PACKS[0].id);

  // Bộ nhớ gần đây & Yêu thích
  const [recentItems, setRecentItems] = useState<{ type: 'emoji' | 'sticker' | 'gif'; data: any }[]>(() => {
    try {
      const saved = localStorage.getItem('vibe_recent_expressions');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [favorites, setFavorites] = useState<{ type: 'emoji' | 'sticker' | 'gif'; data: any }[]>(() => {
    try {
      const saved = localStorage.getItem('vibe_favorite_expressions');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Lưu lịch sử khi người dùng chọn biểu cảm
  const recordRecent = (type: 'emoji' | 'sticker' | 'gif', data: any) => {
    setRecentItems((prev) => {
      const filtered = prev.filter((item) => {
        if (type === 'emoji') return item.data !== data;
        return item.data?.id !== data?.id;
      });
      const updated = [{ type, data }, ...filtered].slice(0, 36);
      localStorage.setItem('vibe_recent_expressions', JSON.stringify(updated));
      return updated;
    });
  };

  const toggleFavorite = (type: 'emoji' | 'sticker' | 'gif', data: any, e: React.MouseEvent) => {
    e.stopPropagation();
    setFavorites((prev) => {
      const exists = prev.some((item) => {
        if (type === 'emoji') return item.data === data;
        return item.data?.id === data?.id;
      });
      let updated;
      if (exists) {
        updated = prev.filter((item) => (type === 'emoji' ? item.data !== data : item.data?.id !== data?.id));
      } else {
        updated = [{ type, data }, ...prev].slice(0, 48);
      }
      localStorage.setItem('vibe_favorite_expressions', JSON.stringify(updated));
      return updated;
    });
  };

  const isFavorited = (type: 'emoji' | 'sticker' | 'gif', data: any) => {
    return favorites.some((item) => {
      if (type === 'emoji') return item.data === data;
      return item.data?.id === data?.id;
    });
  };

  const handleToggleInstallPack = (packId: string) => {
    setInstalledPackIds((prev) => {
      const updated = prev.includes(packId) ? prev.filter((id) => id !== packId) : [...prev, packId];
      localStorage.setItem('vibe_installed_sticker_packs', JSON.stringify(updated));
      return updated;
    });
  };

  // Lấy các packs đã cài đặt
  const installedPacks = useMemo(() => {
    return STORE_STICKER_PACKS.filter((p) => installedPackIds.includes(p.id));
  }, [installedPackIds]);

  const currentStickerPack = useMemo(() => {
    return installedPacks.find((p) => p.id === activePackId) || installedPacks[0] || DEFAULT_STICKER_PACKS[0];
  }, [installedPacks, activePackId]);

  // Bộ lọc tìm kiếm tiếng Việt cho Emoji
  const filteredEmojis = useMemo(() => {
    if (!searchQuery.trim()) return null;
    const cleanQ = removeVietnameseTones(searchQuery);
    const results: { char: string; name: string }[] = [];
    EMOJI_CATEGORIES.forEach((cat) => {
      cat.emojis.forEach((em) => {
        const matchName = removeVietnameseTones(em.name).includes(cleanQ);
        const matchKw = em.keywords.some((kw) => removeVietnameseTones(kw).includes(cleanQ));
        if (matchName || matchKw) {
          results.push(em);
        }
      });
    });
    return results;
  }, [searchQuery]);

  // Bộ lọc tìm kiếm cho Stickers
  const filteredStickers = useMemo(() => {
    if (!searchQuery.trim()) return null;
    const cleanQ = removeVietnameseTones(searchQuery);
    const results: { sticker: StickerItem; pack: StickerPack }[] = [];
    installedPacks.forEach((pack) => {
      pack.stickers.forEach((stk) => {
        const matchName = removeVietnameseTones(stk.name).includes(cleanQ);
        const matchKw = stk.keywords.some((kw) => removeVietnameseTones(kw).includes(cleanQ));
        if (matchName || matchKw) {
          results.push({ sticker: stk, pack });
        }
      });
    });
    return results;
  }, [searchQuery, installedPacks]);

  // Bộ lọc tìm kiếm cho GIF
  const filteredGifs = useMemo(() => {
    if (!searchQuery.trim()) return DEFAULT_GIFS;
    const cleanQ = removeVietnameseTones(searchQuery);
    return DEFAULT_GIFS.filter(
      (g) => removeVietnameseTones(g.title).includes(cleanQ) || removeVietnameseTones(g.category).includes(cleanQ)
    );
  }, [searchQuery]);

  return (
    <>
      <div className="w-[360px] h-[460px] bg-white dark:bg-[#182533] border border-slate-200 dark:border-slate-700/80 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150 select-none z-50">
        {/* 1. Header Navigation Tabs */}
        <div className="flex items-center justify-between px-2.5 pt-2 pb-1.5 border-b border-slate-200 dark:border-slate-700/60 bg-slate-50 dark:bg-[#151f2b]">
          <div className="flex items-center space-x-1">
            <button
              onClick={() => setActiveMainTab('recent')}
              title="Gần đây"
              className={`p-2 rounded-xl transition-all ${
                activeMainTab === 'recent'
                  ? 'bg-[#2481cc]/15 text-[#2481cc] shadow-xs'
                  : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
              }`}
            >
              <Clock className="w-4 h-4" />
            </button>

            <button
              onClick={() => setActiveMainTab('favorites')}
              title="Yêu thích"
              className={`p-2 rounded-xl transition-all ${
                activeMainTab === 'favorites'
                  ? 'bg-amber-500/15 text-amber-500 shadow-xs'
                  : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
              }`}
            >
              <Star className="w-4 h-4" />
            </button>

            <button
              onClick={() => setActiveMainTab('emoji')}
              title="Biểu tượng Emoji"
              className={`p-2 rounded-xl transition-all ${
                activeMainTab === 'emoji'
                  ? 'bg-[#2481cc]/15 text-[#2481cc] shadow-xs'
                  : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
              }`}
            >
              <Smile className="w-4 h-4" />
            </button>

            <button
              onClick={() => setActiveMainTab('sticker')}
              title="Bộ Sticker phong phú"
              className={`p-2 rounded-xl transition-all ${
                activeMainTab === 'sticker'
                  ? 'bg-[#2481cc]/15 text-[#2481cc] shadow-xs'
                  : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
              }`}
            >
              <StickerIcon className="w-4 h-4" />
            </button>

            <button
              onClick={() => setActiveMainTab('gif')}
              title="Ảnh GIF động"
              className={`p-2 rounded-xl transition-all ${
                activeMainTab === 'gif'
                  ? 'bg-[#2481cc]/15 text-[#2481cc] shadow-xs'
                  : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
              }`}
            >
              <Film className="w-4 h-4" />
            </button>
          </div>

          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700/50"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* 2. Search Bar */}
        <div className="p-2 border-b border-slate-100 dark:border-slate-800/60 bg-white dark:bg-[#182533]">
          <div className="relative flex items-center">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={
                activeMainTab === 'emoji'
                  ? 'Tìm kiếm emoji (haha, tim, cuoi)...'
                  : activeMainTab === 'sticker'
                  ? 'Tìm sticker theo cảm xúc...'
                  : activeMainTab === 'gif'
                  ? 'Tìm ảnh GIF động...'
                  : 'Tìm kiếm biểu cảm...'
              }
              className="w-full h-8 pl-8 pr-7 rounded-xl bg-slate-100 dark:bg-[#202b36] text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-[#2481cc]"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 p-0.5 rounded-full text-slate-400 hover:text-slate-600"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>

        {/* 3. Main Content Views */}
        <div className="flex-1 overflow-y-auto p-2 scrollbar-thin">
          {/* TAB 1: GẦN ĐÂY */}
          {activeMainTab === 'recent' && (
            <div>
              <div className="flex items-center justify-between px-1 mb-2">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Đã sử dụng gần đây
                </span>
                {recentItems.length > 0 && (
                  <button
                    onClick={() => {
                      setRecentItems([]);
                      localStorage.removeItem('vibe_recent_expressions');
                    }}
                    className="text-[10px] text-rose-500 hover:underline flex items-center space-x-1"
                  >
                    <Trash2 className="w-3 h-3" />
                    <span>Xóa lịch sử</span>
                  </button>
                )}
              </div>

              {recentItems.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-slate-400 text-xs">
                  <Clock className="w-8 h-8 opacity-30 mb-2" />
                  <span>Chưa có biểu cảm nào được sử dụng gần đây</span>
                </div>
              ) : (
                <div className="grid grid-cols-5 gap-2 content-start">
                  {recentItems.map((item, idx) => {
                    if (item.type === 'emoji') {
                      return (
                        <button
                          key={idx}
                          onClick={() => {
                            onSelectEmoji(item.data);
                            recordRecent('emoji', item.data);
                          }}
                          className="w-12 h-12 flex items-center justify-center text-2xl rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700/50 hover:scale-110 active:scale-95 transition-transform"
                        >
                          {item.data}
                        </button>
                      );
                    }
                    if (item.type === 'sticker') {
                      return (
                        <button
                          key={idx}
                          onClick={() => {
                            onSelectSticker(item.data, currentStickerPack);
                            recordRecent('sticker', item.data);
                          }}
                          className="w-14 h-14 p-1 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700/50 hover:scale-110 active:scale-95 transition-all flex items-center justify-center"
                        >
                          <img src={item.data.url} alt="" className="w-full h-full object-contain" />
                        </button>
                      );
                    }
                    if (item.type === 'gif') {
                      return (
                        <button
                          key={idx}
                          onClick={() => {
                            onSelectGif(item.data);
                            recordRecent('gif', item.data);
                          }}
                          className="col-span-2 h-16 rounded-xl overflow-hidden hover:opacity-85 transition-opacity"
                        >
                          <img src={item.data.previewUrl || item.data.url} alt="" className="w-full h-full object-cover" />
                        </button>
                      );
                    }
                    return null;
                  })}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: YÊU THÍCH */}
          {activeMainTab === 'favorites' && (
            <div>
              <div className="px-1 mb-2 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Bộ sưu tập yêu thích
              </div>
              {favorites.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-slate-400 text-xs">
                  <Star className="w-8 h-8 opacity-30 text-amber-500 mb-2" />
                  <span>Bấm icon ngôi sao trên sticker hoặc GIF để lưu vào đây</span>
                </div>
              ) : (
                <div className="grid grid-cols-4 gap-2 content-start">
                  {favorites.map((item, idx) => (
                    <div
                      key={idx}
                      className="relative group p-1 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700/50 flex items-center justify-center"
                    >
                      {item.type === 'emoji' ? (
                        <button
                          onClick={() => onSelectEmoji(item.data)}
                          className="text-2xl hover:scale-110 transition-transform"
                        >
                          {item.data}
                        </button>
                      ) : (
                        <button
                          onClick={() => onSelectSticker(item.data, currentStickerPack)}
                          className="w-14 h-14"
                        >
                          <img src={item.data.url} alt="" className="w-full h-full object-contain" />
                        </button>
                      )}
                      <button
                        onClick={(e) => toggleFavorite(item.type, item.data, e)}
                        className="absolute -top-1 -right-1 p-1 rounded-full bg-black/60 text-amber-400 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <Star className="w-3 h-3 fill-current" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: EMOJI UNICODE */}
          {activeMainTab === 'emoji' && (
            <div>
              {filteredEmojis ? (
                <div>
                  <div className="px-1 mb-2 text-[11px] font-bold text-slate-400">
                    Kết quả tìm kiếm ({filteredEmojis.length})
                  </div>
                  <div className="grid grid-cols-7 gap-1 content-start">
                    {filteredEmojis.map((em, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          onSelectEmoji(em.char);
                          recordRecent('emoji', em.char);
                        }}
                        title={em.name}
                        className="w-10 h-10 flex items-center justify-center text-xl rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700/50 hover:scale-110 active:scale-90 transition-transform"
                      >
                        {em.char}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                EMOJI_CATEGORIES.map((cat) => (
                  <div key={cat.id} className="mb-4">
                    <div className="px-1 mb-1.5 text-[11px] font-bold text-slate-400 flex items-center space-x-1">
                      <span>{cat.icon}</span>
                      <span>{cat.name}</span>
                    </div>
                    <div className="grid grid-cols-7 gap-1 content-start">
                      {cat.emojis.map((em, idx) => (
                        <button
                          key={idx}
                          onClick={() => {
                            onSelectEmoji(em.char);
                            recordRecent('emoji', em.char);
                          }}
                          title={em.name}
                          className="w-10 h-10 flex items-center justify-center text-xl rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700/50 hover:scale-110 active:scale-90 transition-transform"
                        >
                          {em.char}
                        </button>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* TAB 4: STICKERS */}
          {activeMainTab === 'sticker' && (
            <div>
              {filteredStickers ? (
                <div>
                  <div className="px-1 mb-2 text-[11px] font-bold text-slate-400">
                    Sticker tìm thấy ({filteredStickers.length})
                  </div>
                  <div className="grid grid-cols-4 gap-2 content-start">
                    {filteredStickers.map(({ sticker, pack }) => (
                      <button
                        key={sticker.id}
                        onClick={() => {
                          onSelectSticker(sticker, pack);
                          recordRecent('sticker', sticker);
                        }}
                        title={sticker.name}
                        className="p-1 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700/60 hover:scale-110 active:scale-95 transition-all flex flex-col items-center group"
                      >
                        <img src={sticker.url} alt={sticker.name} className="w-16 h-16 object-contain" />
                        <span className="text-[10px] text-slate-400 truncate max-w-full mt-1">
                          {sticker.name}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              ) : currentStickerPack ? (
                <div>
                  <div className="flex items-center justify-between px-1 mb-2">
                    <span className="text-[11px] font-bold text-slate-500 dark:text-slate-300">
                      {currentStickerPack.name}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      {currentStickerPack.stickers.length} stickers
                    </span>
                  </div>

                  <div className="grid grid-cols-4 gap-2 content-start">
                    {currentStickerPack.stickers.map((stk) => (
                      <div
                        key={stk.id}
                        onClick={() => {
                          onSelectSticker(stk, currentStickerPack);
                          recordRecent('sticker', stk);
                        }}
                        title={stk.name}
                        className="relative p-1.5 rounded-2xl hover:bg-slate-100 dark:hover:bg-slate-700/60 hover:scale-110 active:scale-95 transition-all flex flex-col items-center cursor-pointer group"
                      >
                        <img
                          src={stk.url}
                          alt={stk.name}
                          className="w-16 h-16 object-contain filter drop-shadow-xs"
                        />
                        <span className="text-[10px] text-slate-500 dark:text-slate-400 truncate max-w-full mt-1">
                          {stk.name}
                        </span>

                        {/* Favorite button on hover */}
                        <button
                          onClick={(e) => toggleFavorite('sticker', stk, e)}
                          title="Thêm vào yêu thích"
                          className="absolute top-1 right-1 p-1 rounded-full bg-black/60 text-slate-300 hover:text-amber-400 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <Star
                            className={`w-3 h-3 ${isFavorited('sticker', stk) ? 'fill-amber-400 text-amber-400' : ''}`}
                          />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          )}

          {/* TAB 5: GIF ĐỘNG */}
          {activeMainTab === 'gif' && (
            <div>
              <div className="grid grid-cols-2 gap-2 content-start">
                {filteredGifs.map((gif) => (
                  <div
                    key={gif.id}
                    onClick={() => {
                      onSelectGif(gif);
                      recordRecent('gif', gif);
                    }}
                    className="relative group rounded-xl overflow-hidden h-28 bg-slate-100 dark:bg-slate-800 cursor-pointer shadow-xs border border-black/5 dark:border-white/5 hover:opacity-90 transition-opacity"
                  >
                    <img
                      src={gif.previewUrl || gif.url}
                      alt={gif.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-2">
                      <span className="text-[10px] text-white font-medium truncate">{gif.title}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 4. Bottom Sticker Pack Switcher (Khi ở tab Sticker) */}
        {activeMainTab === 'sticker' && (
          <div className="px-2 py-1.5 border-t border-slate-200 dark:border-slate-700/60 bg-slate-50 dark:bg-[#151f2b] flex items-center justify-between">
            <div className="flex items-center space-x-1.5 overflow-x-auto scrollbar-none py-0.5 flex-1 mr-2">
              {installedPacks.map((pack) => (
                <button
                  key={pack.id}
                  onClick={() => setActivePackId(pack.id)}
                  title={pack.name}
                  className={`w-8 h-8 rounded-xl p-0.5 flex items-center justify-center transition-all ${
                    activePackId === pack.id
                      ? 'bg-[#2481cc]/20 ring-2 ring-[#2481cc]'
                      : 'hover:bg-slate-200 dark:hover:bg-slate-700/60 opacity-70 hover:opacity-100'
                  }`}
                >
                  <img src={pack.avatarUrl} alt="" className="w-full h-full rounded-lg object-cover" />
                </button>
              ))}
            </div>

            {/* Nút mở Sticker Store */}
            <button
              onClick={() => setIsStoreOpen(true)}
              title="Khám phá thêm bộ sưu tập trong Sticker Store"
              className="p-1.5 rounded-xl bg-[#2481cc] text-white hover:bg-[#1d73b8] active:scale-95 shadow-sm transition-all flex items-center space-x-1 text-xs font-semibold flex-shrink-0"
            >
              <Plus className="w-3.5 h-3.5" />
              <span className="hidden sm:inline text-[11px]">Kho</span>
            </button>
          </div>
        )}
      </div>

      {/* 5. Sticker Store Modal Popup */}
      <StickerStoreModal
        isOpen={isStoreOpen}
        onClose={() => setIsStoreOpen(false)}
        installedPackIds={installedPackIds}
        onToggleInstallPack={handleToggleInstallPack}
      />
    </>
  );
};
