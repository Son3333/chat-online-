import React, { useState, useEffect } from 'react';
import { Phone, PhoneOff, Video, Mic, MicOff, Volume2 } from 'lucide-react';
import { useChat } from '../../context/ChatContext';

export const CallModal: React.FC = () => {
  const { incomingCall, activeCall, acceptCall, rejectCall, endCall } = useChat();
  const [callDuration, setCallDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);

  // Timer for active call
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (activeCall) {
      setCallDuration(0);
      interval = setInterval(() => {
        setCallDuration((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [activeCall]);

  const formatCallTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // 1. Incoming Call Prompt
  if (incomingCall && !activeCall) {
    return (
      <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 select-none">
        <div className="w-full max-w-xs bg-white dark:bg-[#17212b] border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl p-6 flex flex-col items-center animate-bounce-short">
          <div className="w-20 h-20 rounded-full bg-[#2481cc]/20 flex items-center justify-center text-[#2481cc] mb-4 animate-pulse">
            {incomingCall.callType === 'video' ? (
              <Video className="w-10 h-10" />
            ) : (
              <Phone className="w-10 h-10" />
            )}
          </div>

          <h3 className="font-bold text-base text-slate-800 dark:text-slate-100 text-center">
            {incomingCall.callerName}
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-6">
            Đang gọi {incomingCall.callType === 'video' ? 'video' : 'thoại'} đến bạn...
          </p>

          <div className="flex items-center space-x-6">
            <button
              onClick={rejectCall}
              title="Từ chối cuộc gọi"
              className="w-13 h-13 rounded-full bg-red-500 hover:bg-red-600 active:scale-95 text-white flex items-center justify-center shadow-lg shadow-red-500/30 transition-transform p-3.5"
            >
              <PhoneOff className="w-6 h-6" />
            </button>

            <button
              onClick={acceptCall}
              title="Chấp nhận cuộc gọi"
              className="w-13 h-13 rounded-full bg-emerald-500 hover:bg-emerald-600 active:scale-95 text-white flex items-center justify-center shadow-lg shadow-emerald-500/30 transition-transform p-3.5 animate-pulse"
            >
              <Phone className="w-6 h-6" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 2. Active Call Window
  if (activeCall) {
    return (
      <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4 select-none">
        <div className="w-full max-w-sm bg-white dark:bg-[#17212b] border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl p-6 flex flex-col items-center animate-in zoom-in-95 duration-150">
          <div className="w-20 h-20 rounded-full bg-emerald-500/20 text-emerald-500 flex items-center justify-center mb-4">
            {activeCall.callType === 'video' ? (
              <Video className="w-10 h-10" />
            ) : (
              <Volume2 className="w-10 h-10 animate-pulse" />
            )}
          </div>

          <h3 className="font-bold text-base text-slate-800 dark:text-slate-100 text-center">
            {activeCall.partnerName}
          </h3>
          <span className="mt-1 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-500 text-xs font-mono font-bold">
            {formatCallTime(callDuration)}
          </span>

          <div className="flex items-center space-x-4 mt-8">
            <button
              onClick={() => setIsMuted(!isMuted)}
              title={isMuted ? 'Bật Mic' : 'Tắt Mic'}
              className={`p-3.5 rounded-full transition-colors ${
                isMuted
                  ? 'bg-amber-500 text-white'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
              }`}
            >
              {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>

            <button
              onClick={endCall}
              title="Kết thúc cuộc gọi"
              className="p-3.5 rounded-full bg-red-500 hover:bg-red-600 active:scale-95 text-white shadow-lg shadow-red-500/30 transition-transform"
            >
              <PhoneOff className="w-6 h-6" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

