import React, { useState } from 'react';
import { Lock, Delete } from 'lucide-react';
import { useChat } from '../../context/ChatContext';

export const LockScreen: React.FC = () => {
  const { isLocked, setIsLocked, currentUser } = useChat();
  const [pin, setPin] = useState('');
  const [error, setError] = useState(false);

  if (!isLocked) return null;

  const handleKeyPress = (num: string) => {
    if (pin.length < 4) {
      const nextPin = pin + num;
      setPin(nextPin);
      setError(false);

      if (nextPin.length === 4) {
        // Default PIN is 1234 or any 4 digit matching
        if (nextPin === '1234' || nextPin === '0000') {
          setTimeout(() => {
            setIsLocked(false);
            setPin('');
          }, 150);
        } else {
          setTimeout(() => {
            setError(true);
            setPin('');
          }, 200);
        }
      }
    }
  };

  const handleDelete = () => {
    setPin((prev) => prev.slice(0, -1));
    setError(false);
  };

  return (
    <div className="fixed inset-0 z-50 bg-[#0e1621] text-white flex flex-col items-center justify-center p-4 select-none">
      <div className="w-full max-w-xs flex flex-col items-center animate-in zoom-in-95 duration-150">
        <div className="w-16 h-16 rounded-3xl bg-[#2481cc]/20 text-[#2481cc] flex items-center justify-center mb-4 shadow-lg shadow-[#2481cc]/10">
          <Lock className="w-8 h-8" />
        </div>

        <h2 className="text-lg font-bold mb-1">Ứng dụng đã bị khóa</h2>
        <p className="text-xs text-slate-400 mb-6 text-center">
          Chào {currentUser?.full_name || 'bạn'}, nhập mã PIN (Mặc định: 1234) để mở khóa
        </p>

        {/* 4 dots */}
        <div className="flex space-x-4 mb-8">
          {[0, 1, 2, 3].map((idx) => (
            <div
              key={idx}
              className={`w-3.5 h-3.5 rounded-full transition-all duration-150 ${
                error
                  ? 'bg-red-500 scale-110'
                  : idx < pin.length
                  ? 'bg-[#2481cc] scale-110'
                  : 'bg-slate-700'
              }`}
            />
          ))}
        </div>

        {error && (
          <p className="text-xs text-red-400 font-semibold mb-4 animate-shake">
            Sai mã PIN! Thử lại với 1234
          </p>
        )}

        {/* Numpad */}
        <div className="grid grid-cols-3 gap-3 w-64">
          {['1', '2', '3', '4', '5', '6', '7', '8', '9'].map((digit) => (
            <button
              key={digit}
              onClick={() => handleKeyPress(digit)}
              className="h-14 rounded-2xl bg-[#17212b] hover:bg-[#202b36] active:bg-[#2481cc] text-lg font-bold transition-colors shadow-sm"
            >
              {digit}
            </button>
          ))}
          <div />
          <button
            onClick={() => handleKeyPress('0')}
            className="h-14 rounded-2xl bg-[#17212b] hover:bg-[#202b36] active:bg-[#2481cc] text-lg font-bold transition-colors shadow-sm"
          >
            0
          </button>
          <button
            onClick={handleDelete}
            className="h-14 rounded-2xl bg-[#17212b] hover:bg-[#202b36] text-slate-400 hover:text-white flex items-center justify-center transition-colors shadow-sm"
          >
            <Delete className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};
