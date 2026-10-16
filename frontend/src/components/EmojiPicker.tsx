import React, { useState } from 'react';
import { Smile, Heart, ThumbsUp, Flame, Coffee, X } from 'lucide-react';

interface EmojiPickerProps {
  onSelect: (emoji: string) => void;
  onClose?: () => void;
}

const EMOJI_CATEGORIES = [
  {
    id: 'smileys',
    name: 'Cảm xúc',
    icon: Smile,
    emojis: ['😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '😉', '😊', '😇', '🥰', '😍', '🤩', '😘', '😋', '😜', '🤪', '😎', '🥳', '😏', '😒', '😞', '😔', '😟', '😕', '🙁', '😣', '😖', '😫', '😩', '🥺', '😢', '😭', '😤', '😠', '😡', '🤬', '🤯', '😳', '🥵', '🥶', '😱', '😨', '😰', '🤔', '🤗', '🤫', '🤥', '😴'],
  },
  {
    id: 'gestures',
    name: 'Hành động',
    icon: ThumbsUp,
    emojis: ['👍', '👎', '👌', '✌️', '🤞', '🤟', '🤘', '🤙', '👈', '👉', '👆', '👇', '☝️', '✋', '🤚', '🖐️', '🖖', '👋', '🤝', '💪', '👏', '🙌', '👐', '🤲', '🙏', '✍️', '💅', '🤳'],
  },
  {
    id: 'hearts',
    name: 'Biểu tượng',
    icon: Heart,
    emojis: ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟', '☮️', '✝️', '☯️', '☸️', '♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'],
  },
  {
    id: 'popular',
    name: 'Nổi bật',
    icon: Flame,
    emojis: ['🔥', '✨', '🎉', '🎊', '🚀', '⭐', '🌟', '💥', '💯', '🎯', '🏆', '🥇', '👑', '💎', '💡', '🔔', '📢', '🎁', '🎈', '🎵', '🎶', '⚡', '☀️', '🌈', '🍀', '🌸', '🌹'],
  },
  {
    id: 'food',
    name: 'Đồ ăn',
    icon: Coffee,
    emojis: ['☕', '🍵', '🧃', '🥤', '🍺', '🍻', '🍷', '🍕', '🍔', '🍟', '🌭', '🍿', '🍣', '🍱', '🍜', '🍝', '🍦', '🍰', '🎂', '🍩', '🍪', '🍫', '🍬', '🍭', '🍎', '🍓', '🥑'],
  },
];

export const EmojiPicker: React.FC<EmojiPickerProps> = ({ onSelect, onClose }) => {
  const [activeTab, setActiveTab] = useState('smileys');

  const currentCategory = EMOJI_CATEGORIES.find((c) => c.id === activeTab) || EMOJI_CATEGORIES[0];

  return (
    <div className="w-80 h-72 bg-white dark:bg-[#1e2c3a] border border-slate-200 dark:border-slate-700/80 rounded-xl shadow-xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-100 z-50">
      {/* Category Tabs */}
      <div className="flex items-center justify-between px-2 pt-2 pb-1 border-b border-slate-200 dark:border-slate-700/60 bg-slate-50 dark:bg-[#17212b]">
        <div className="flex space-x-1">
          {EMOJI_CATEGORIES.map((cat) => {
            const Icon = cat.icon;
            const isActive = activeTab === cat.id;
            return (
              <button
                key={cat.id}
                onClick={() => setActiveTab(cat.id)}
                title={cat.name}
                className={`p-1.5 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-[#2481cc]/15 text-[#2481cc]'
                    : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
                }`}
              >
                <Icon className="w-4 h-4" />
              </button>
            );
          })}
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700/50"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Emoji Grid */}
      <div className="flex-1 p-2 overflow-y-auto grid grid-cols-7 gap-1 content-start">
        {currentCategory.emojis.map((emoji, index) => (
          <button
            key={index}
            onClick={() => onSelect(emoji)}
            className="w-9 h-9 flex items-center justify-center text-xl rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700/50 hover:scale-110 active:scale-95 transition-transform"
          >
            {emoji}
          </button>
        ))}
      </div>
    </div>
  );
};

