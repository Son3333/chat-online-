import React, { useMemo, useState } from 'react';
import { X, Sparkles } from 'lucide-react';
import { StickerItem } from '../../types';
import { CONTEXT_EMOTION_RULES, removeVietnameseTones, DEFAULT_STICKER_PACKS } from './expressionData';

interface StickerSuggestionsBarProps {
  inputText: string;
  onSelectSticker: (sticker: StickerItem) => void;
  onSelectEmoji: (emoji: string) => void;
}

export const StickerSuggestionsBar: React.FC<StickerSuggestionsBarProps> = ({
  inputText,
  onSelectSticker,
  onSelectEmoji,
}) => {
  const [isDismissed, setIsDismissed] = useState(false);
  const [lastMatchedQuery, setLastMatchedQuery] = useState('');

  // Thu thập toàn bộ stickers có sẵn trong hệ thống
  const allStickers = useMemo(() => {
    return DEFAULT_STICKER_PACKS.flatMap((pack) => pack.stickers);
  }, []);

  // Phân tích từ khóa cảm xúc theo thời gian thực (Real-time local context analysis)
  const matchResult = useMemo(() => {
    if (!inputText || inputText.trim().length === 0) return null;
    const cleanText = removeVietnameseTones(inputText);

    for (const rule of CONTEXT_EMOTION_RULES) {
      const isMatched = rule.keywords.some((kw) => {
        const cleanKw = removeVietnameseTones(kw);
        return cleanText.includes(cleanKw);
      });

      if (isMatched) {
        // Tìm các sticker phù hợp theo từ khóa khớp
        const matchedStickers = allStickers.filter((stk) =>
          stk.keywords.some((skw) => removeVietnameseTones(skw).includes(rule.stickerKeywordMatch))
        );

        return {
          rule,
          matchedStickers: matchedStickers.slice(0, 6),
          suggestedEmojis: rule.suggestedEmojis.slice(0, 4),
        };
      }
    }

    return null;
  }, [inputText, allStickers]);

  // Reset trạng thái ẩn khi người dùng gõ từ khóa mới
  React.useEffect(() => {
    if (matchResult && matchResult.rule.stickerKeywordMatch !== lastMatchedQuery) {
      setIsDismissed(false);
      setLastMatchedQuery(matchResult.rule.stickerKeywordMatch);
    }
  }, [matchResult, lastMatchedQuery]);

  if (!matchResult || isDismissed || matchResult.matchedStickers.length === 0) {
    return null;
  }

  return (
    <div className="mb-2 px-3 py-1.5 rounded-2xl bg-white/95 dark:bg-[#1a2530]/95 backdrop-blur-md border border-slate-200 dark:border-slate-700/80 shadow-lg flex items-center justify-between animate-in fade-in slide-in-from-bottom-2 duration-150 select-none z-30">
      {/* Label and Quick Items */}
      <div className="flex items-center space-x-2.5 overflow-x-auto py-0.5 scrollbar-none flex-1 mr-2">
        <div className="flex items-center space-x-1 text-[11px] font-bold text-[#2481cc] flex-shrink-0 bg-[#2481cc]/10 dark:bg-[#2481cc]/20 px-2 py-1 rounded-lg">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Gợi ý:</span>
        </div>

        {/* Suggested Stickers */}
        <div className="flex items-center space-x-1.5 flex-shrink-0">
          {matchResult.matchedStickers.map((sticker) => (
            <button
              key={sticker.id}
              onClick={() => onSelectSticker(sticker)}
              title={`Gửi sticker: ${sticker.name}`}
              className="w-10 h-10 p-0.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700/60 hover:scale-110 active:scale-95 transition-all flex items-center justify-center cursor-pointer group"
            >
              <img
                src={sticker.url}
                alt={sticker.name}
                className="w-full h-full object-contain filter drop-shadow-xs"
              />
            </button>
          ))}
        </div>

        <div className="w-px h-6 bg-slate-200 dark:bg-slate-700/60 flex-shrink-0 mx-1" />

        {/* Suggested Emojis */}
        <div className="flex items-center space-x-1 flex-shrink-0">
          {matchResult.suggestedEmojis.map((emoji, idx) => (
            <button
              key={idx}
              onClick={() => onSelectEmoji(emoji)}
              className="w-7 h-7 flex items-center justify-center text-lg rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700/50 hover:scale-110 active:scale-90 transition-transform"
            >
              {emoji}
            </button>
          ))}
        </div>
      </div>

      {/* Dismiss Button */}
      <button
        onClick={() => setIsDismissed(true)}
        title="Đóng thanh gợi ý"
        className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700/50 transition-colors flex-shrink-0"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};
