import React, { useState, useEffect, useRef } from 'react';
import {
  Phone,
  PhoneOff,
  Video,
  VideoOff,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Monitor,
  Maximize2,
  Minimize2,
  ShieldCheck,
  Radio
} from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { getInitials } from '../../lib/utils';

export const CallModal: React.FC = () => {
  const { incomingCall, activeCall, acceptCall, rejectCall, endCall } = useChat();
  const [callDuration, setCallDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(false);
  const [isSpeakerMuted, setIsSpeakerMuted] = useState(false);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const localVideoRef = useRef<HTMLVideoElement>(null);
  const localStreamRef = useRef<MediaStream | null>(null);

  // Timer for active call duration
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

  // Handle local camera stream when activeCall is a Video Call
  useEffect(() => {
    if (activeCall && activeCall.callType === 'video') {
      let isSubscribed = true;

      const startCamera = async () => {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 1280 }, height: { ideal: 720 } },
            audio: true,
          });
          if (!isSubscribed) {
            stream.getTracks().forEach((track) => track.stop());
            return;
          }
          localStreamRef.current = stream;
          if (localVideoRef.current) {
            localVideoRef.current.srcObject = stream;
          }
        } catch (err) {
          console.warn('[VideoCall] Could not access real camera, falling back to simulated preview:', err);
        }
      };

      startCamera();

      return () => {
        isSubscribed = false;
        if (localStreamRef.current) {
          localStreamRef.current.getTracks().forEach((track) => track.stop());
          localStreamRef.current = null;
        }
      };
    }
  }, [activeCall]);

  const toggleMute = () => {
    if (localStreamRef.current) {
      localStreamRef.current.getAudioTracks().forEach((track) => {
        track.enabled = isMuted; // toggle
      });
    }
    setIsMuted(!isMuted);
  };

  const toggleVideo = () => {
    if (localStreamRef.current) {
      localStreamRef.current.getVideoTracks().forEach((track) => {
        track.enabled = isVideoOff; // toggle
      });
    }
    setIsVideoOff(!isVideoOff);
  };

  const toggleScreenShare = async () => {
    if (!isScreenSharing) {
      try {
        let screenStream: MediaStream | null = null;

        // Method 1: Try getDisplayMedia (supported by Electron setDisplayMediaRequestHandler)
        if (navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia) {
          try {
            screenStream = await navigator.mediaDevices.getDisplayMedia({
              video: true,
              audio: false,
            });
          } catch (e1) {
            console.warn('[ScreenShare] getDisplayMedia error, falling back to desktopCapturer:', e1);
          }
        }

        // Method 2: Try desktopCapturer via Electron IPC
        if (!screenStream && (window as any).api?.getScreenSourceId) {
          try {
            const sourceId = await (window as any).api.getScreenSourceId();
            if (sourceId) {
              screenStream = await (navigator.mediaDevices as any).getUserMedia({
                audio: false,
                video: {
                  mandatory: {
                    chromeMediaSource: 'desktop',
                    chromeMediaSourceId: sourceId,
                    minWidth: 1280,
                    maxWidth: 1920,
                    minHeight: 720,
                    maxHeight: 1080,
                  },
                },
              });
            }
          } catch (e2) {
            console.warn('[ScreenShare] getUserMedia desktop error:', e2);
          }
        }

        if (screenStream) {
          if (localVideoRef.current) {
            localVideoRef.current.srcObject = screenStream;
          }
          setIsScreenSharing(true);
          const videoTrack = screenStream.getVideoTracks()[0];
          if (videoTrack) {
            videoTrack.onended = () => {
              setIsScreenSharing(false);
              if (localStreamRef.current && localVideoRef.current) {
                localVideoRef.current.srcObject = localStreamRef.current;
              }
            };
          }
        } else {
          alert('Không thể bắt luồng chia sẻ màn hình. Hãy đảm bảo bạn đã cấp quyền chia sẻ màn hình!');
        }
      } catch (err: any) {
        console.warn('Screen share error:', err);
        alert('Lỗi chia sẻ màn hình: ' + (err?.message || err));
      }
    } else {
      setIsScreenSharing(false);
      if (localStreamRef.current && localVideoRef.current) {
        localVideoRef.current.srcObject = localStreamRef.current;
      }
    }
  };

  const handleEndCall = () => {
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((track) => track.stop());
      localStreamRef.current = null;
    }
    endCall();
  };

  const formatCallTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // 1. INCOMING CALL PROMPT
  if (incomingCall && !activeCall) {
    const isIncomingVideo = incomingCall.callType === 'video';
    return (
      <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md flex items-center justify-center p-4 select-none animate-in fade-in duration-200">
        <div className="w-full max-w-sm bg-white dark:bg-[#17212b] border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl p-6 flex flex-col items-center animate-in zoom-in-95 duration-200">
          <div
            className={`w-24 h-24 rounded-full flex items-center justify-center mb-4 shadow-xl animate-pulse ${
              isIncomingVideo
                ? 'bg-gradient-to-tr from-emerald-500 to-teal-400 text-white shadow-emerald-500/30'
                : 'bg-gradient-to-tr from-blue-600 to-cyan-500 text-white shadow-blue-500/30'
            }`}
          >
            {isIncomingVideo ? <Video className="w-12 h-12" /> : <Phone className="w-12 h-12" />}
          </div>

          <h3 className="font-bold text-lg text-slate-800 dark:text-slate-100 text-center">
            {incomingCall.callerName}
          </h3>
          <div className="flex items-center space-x-1.5 mt-1 mb-6 text-xs text-slate-500 dark:text-slate-400">
            <Radio className="w-3.5 h-3.5 text-emerald-500 animate-ping" />
            <span>Đang có cuộc gọi {isIncomingVideo ? 'Video HD' : 'Thoại bảo mật'} đến...</span>
          </div>

          <div className="flex items-center space-x-8">
            <button
              onClick={rejectCall}
              title="Từ chối cuộc gọi"
              className="group flex flex-col items-center space-y-1.5"
            >
              <div className="w-14 h-14 rounded-full bg-red-500 hover:bg-red-600 active:scale-95 text-white flex items-center justify-center shadow-lg shadow-red-500/30 transition-transform">
                <PhoneOff className="w-6 h-6" />
              </div>
              <span className="text-[11px] font-semibold text-red-500">Từ chối</span>
            </button>

            <button
              onClick={acceptCall}
              title="Trả lời cuộc gọi"
              className="group flex flex-col items-center space-y-1.5"
            >
              <div
                className={`w-14 h-14 rounded-full text-white flex items-center justify-center shadow-lg active:scale-95 transition-transform animate-bounce-short ${
                  isIncomingVideo
                    ? 'bg-emerald-500 hover:bg-emerald-600 shadow-emerald-500/30'
                    : 'bg-blue-600 hover:bg-blue-700 shadow-blue-500/30'
                }`}
              >
                {isIncomingVideo ? <Video className="w-6 h-6" /> : <Phone className="w-6 h-6" />}
              </div>
              <span className="text-[11px] font-semibold text-emerald-500">Trả lời</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 1.5. OUTGOING CALL RINGING PROMPT
  if (activeCall && activeCall.isOutgoing && !activeCall.isConnected) {
    const isVideo = activeCall.callType === 'video';
    return (
      <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4 select-none animate-in fade-in duration-200">
        <div className="w-full max-w-sm bg-white dark:bg-[#17212b] border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl p-7 flex flex-col items-center animate-in zoom-in-95 duration-200">
          <div className="relative mb-6">
            <div className="absolute inset-0 rounded-full bg-blue-500/20 animate-ping opacity-60" />
            <div className="absolute -inset-4 rounded-full border border-blue-500/25 animate-pulse" />
            <div
              className={`w-28 h-28 rounded-full flex items-center justify-center text-white text-3xl font-bold shadow-2xl relative z-10 ${
                isVideo
                  ? 'bg-gradient-to-tr from-emerald-600 to-teal-400 shadow-emerald-500/30'
                  : 'bg-gradient-to-tr from-blue-600 to-cyan-500 shadow-blue-500/30'
              }`}
            >
              {getInitials(activeCall.partnerName)}
            </div>
          </div>

          <h3 className="font-bold text-lg text-slate-800 dark:text-slate-100 text-center mb-1">
            {activeCall.partnerName}
          </h3>
          <div className="flex items-center space-x-1.5 text-xs text-[#2481cc] dark:text-cyan-400 font-medium mb-8">
            <Radio className="w-3.5 h-3.5 animate-ping" />
            <span>Đang đổ chuông {isVideo ? 'Video Call' : 'Thoại'}...</span>
          </div>

          <button
            onClick={handleEndCall}
            title="Hủy cuộc gọi"
            className="px-6 py-3 rounded-full bg-red-600 hover:bg-red-700 active:scale-95 text-white font-bold text-xs flex items-center space-x-2 shadow-lg shadow-red-600/30 transition-transform cursor-pointer"
          >
            <PhoneOff className="w-5 h-5" />
            <span>Hủy cuộc gọi</span>
          </button>
        </div>
      </div>
    );
  }

  // 2. ACTIVE CALL
  if (activeCall) {
    const isVideo = activeCall.callType === 'video';

    // ----------------------------------------------------------------------------------
    // A. VIDEO CALL INTERFACE (GIAO DIỆN GỌI VIDEO CAO CẤP CÓ CAMERA TRỰC TIẾP)
    // ----------------------------------------------------------------------------------
    if (isVideo) {
      return (
        <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-xl flex items-center justify-center p-3 select-none animate-in fade-in duration-200">
          <div
            className={`bg-[#0e1621] border border-slate-800 rounded-3xl shadow-2xl flex flex-col overflow-hidden transition-all duration-300 relative ${
              isFullscreen ? 'w-screen h-screen rounded-none p-0' : 'w-full max-w-4xl h-[620px]'
            }`}
          >
            {/* Top Bar: Caller Info & Status */}
            <div className="absolute top-0 inset-x-0 h-16 bg-gradient-to-b from-black/80 to-transparent z-20 flex items-center justify-between px-6">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold text-sm">
                  {getInitials(activeCall.partnerName)}
                </div>
                <div className="flex flex-col">
                  <span className="font-bold text-sm text-white flex items-center space-x-2">
                    <span>{activeCall.partnerName}</span>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-[10px] font-medium border border-emerald-500/30 flex items-center space-x-1">
                      <ShieldCheck className="w-3 h-3 text-emerald-400" />
                      <span>Video HD 1080p • Đã mã hóa</span>
                    </span>
                  </span>
                  <span className="text-xs text-emerald-400 font-mono font-semibold">
                    {formatCallTime(callDuration)}
                  </span>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setIsFullscreen(!isFullscreen)}
                  className="p-2 rounded-xl bg-white/10 hover:bg-white/20 text-white transition-colors"
                  title={isFullscreen ? 'Thu nhỏ cửa sổ' : 'Toàn màn hình'}
                >
                  {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Main Stage: Remote Video Screen */}
            <div className="flex-1 w-full h-full relative flex items-center justify-center bg-slate-950 overflow-hidden">
              {/* Partner Video Mock/Stream */}
              <div className="w-full h-full flex flex-col items-center justify-center relative">
                {/* Background ambient lighting */}
                <div className="absolute inset-0 bg-gradient-to-tr from-cyan-950/40 via-slate-950 to-blue-950/30" />

                {/* Simulated Remote Webcam Display */}
                <div className="relative z-10 flex flex-col items-center text-center p-6">
                  <div className="relative mb-6">
                    <div className="w-32 h-32 rounded-full bg-gradient-to-tr from-emerald-600 via-teal-500 to-cyan-500 p-1 shadow-2xl shadow-emerald-500/20 animate-pulse">
                      <div className="w-full h-full rounded-full bg-[#17212b] flex items-center justify-center text-white text-3xl font-bold">
                        {getInitials(activeCall.partnerName)}
                      </div>
                    </div>
                    <div className="absolute bottom-1 right-1 w-6 h-6 rounded-full bg-emerald-500 border-2 border-[#0e1621] flex items-center justify-center text-white">
                      <Video className="w-3.5 h-3.5" />
                    </div>
                  </div>

                  <h4 className="text-lg font-bold text-white mb-1">{activeCall.partnerName}</h4>
                  <p className="text-xs text-slate-400 max-w-sm">
                    Đang truyền phát Video HD thời gian thực qua giao thức đường hầm bảo mật.
                  </p>
                </div>

                {/* Floating Self Camera View (Picture-In-Picture) */}
                <div className="absolute bottom-20 right-6 w-48 h-36 bg-slate-900 border-2 border-emerald-500/50 rounded-2xl shadow-2xl overflow-hidden z-30 group">
                  <video
                    ref={localVideoRef}
                    autoPlay
                    playsInline
                    muted
                    className={`w-full h-full object-cover mirror ${isVideoOff ? 'hidden' : 'block'}`}
                  />
                  {isVideoOff && (
                    <div className="w-full h-full flex flex-col items-center justify-center text-slate-400 bg-slate-900 p-2 text-center">
                      <VideoOff className="w-8 h-8 text-amber-500 mb-1" />
                      <span className="text-[10px]">Camera của bạn đã tắt</span>
                    </div>
                  )}
                  <div className="absolute bottom-1.5 left-2 px-1.5 py-0.5 rounded bg-black/60 text-white text-[9px] font-semibold backdrop-blur-sm">
                    Bạn {isMuted ? '(Đã tắt mic)' : ''}
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Floating Control Bar */}
            <div className="absolute bottom-4 inset-x-0 z-40 flex items-center justify-center space-x-3 px-4">
              <div className="bg-[#17212b]/90 backdrop-blur-xl border border-slate-700/80 rounded-2xl p-2.5 flex items-center space-x-3 shadow-2xl">
                {/* 1. Mute Audio */}
                <button
                  onClick={toggleMute}
                  title={isMuted ? 'Bật Microphone' : 'Tắt Microphone'}
                  className={`p-3.5 rounded-xl transition-all font-medium text-xs flex items-center space-x-2 ${
                    isMuted
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      : 'bg-white/10 hover:bg-white/15 text-white'
                  }`}
                >
                  {isMuted ? <MicOff className="w-5 h-5 text-amber-400" /> : <Mic className="w-5 h-5" />}
                  <span className="hidden sm:inline">{isMuted ? 'Bật Mic' : 'Tắt Mic'}</span>
                </button>

                {/* 2. Toggle Camera */}
                <button
                  onClick={toggleVideo}
                  title={isVideoOff ? 'Bật Camera' : 'Tắt Camera'}
                  className={`p-3.5 rounded-xl transition-all font-medium text-xs flex items-center space-x-2 ${
                    isVideoOff
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      : 'bg-white/10 hover:bg-white/15 text-white'
                  }`}
                >
                  {isVideoOff ? <VideoOff className="w-5 h-5 text-amber-400" /> : <Video className="w-5 h-5" />}
                  <span className="hidden sm:inline">{isVideoOff ? 'Bật Cam' : 'Tắt Cam'}</span>
                </button>

                {/* 3. Screen Share */}
                <button
                  onClick={toggleScreenShare}
                  title={isScreenSharing ? 'Dừng chia sẻ màn hình máy tính' : 'Chia sẻ màn hình máy tính / cửa sổ ứng dụng (Screen Share)'}
                  className={`p-3.5 rounded-xl transition-all font-medium text-xs flex items-center space-x-2 ${
                    isScreenSharing
                      ? 'bg-cyan-500/25 text-cyan-300 border border-cyan-400/40 ring-2 ring-cyan-400/20'
                      : 'bg-white/10 hover:bg-white/15 text-white'
                  }`}
                >
                  <Monitor className="w-5 h-5 text-cyan-400" />
                  <span className="hidden sm:inline font-semibold">
                    {isScreenSharing ? 'Dừng Chia Sẻ' : 'Chia Sẻ Màn Hình'}
                  </span>
                </button>

                {/* 4. End Call Button */}
                <button
                  onClick={handleEndCall}
                  title="Kết thúc cuộc gọi Video"
                  className="px-5 py-3.5 rounded-xl bg-red-600 hover:bg-red-700 active:scale-95 text-white font-bold text-xs flex items-center space-x-2 shadow-lg shadow-red-600/40 transition-transform cursor-pointer"
                >
                  <PhoneOff className="w-5 h-5" />
                  <span>Kết Thúc</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    // ----------------------------------------------------------------------------------
    // B. VOICE CALL INTERFACE (GIAO DIỆN GỌI THOẠI CHUYÊN BIỆT VỚI SÓNG ÂM THANH SỐNG ĐỘNG)
    // ----------------------------------------------------------------------------------
    return (
      <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4 select-none animate-in fade-in duration-200">
        <div className="w-full max-w-sm bg-gradient-to-b from-white to-slate-50 dark:from-[#1e2a36] dark:to-[#17212b] border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl p-7 flex flex-col items-center animate-in zoom-in-95 duration-150 relative overflow-hidden">
          {/* Audio Waveform Indicator badge */}
          <div className="px-3 py-1 rounded-full bg-blue-500/10 text-[#2481cc] dark:text-cyan-400 text-xs font-semibold flex items-center space-x-1.5 mb-6">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Cuộc gọi thoại bảo mật</span>
          </div>

          {/* Concentric Pulsing Avatar Rings */}
          <div className="relative mb-6">
            <div className="absolute inset-0 rounded-full bg-blue-500/20 animate-ping opacity-50" />
            <div className="absolute -inset-3 rounded-full border-2 border-blue-500/20 animate-pulse" />
            <div className="w-28 h-28 rounded-full bg-gradient-to-tr from-blue-600 to-cyan-500 p-1 shadow-xl shadow-blue-500/30 relative z-10 flex items-center justify-center text-white text-3xl font-bold">
              {getInitials(activeCall.partnerName)}
            </div>
          </div>

          <h3 className="font-bold text-lg text-slate-800 dark:text-slate-100 text-center">
            {activeCall.partnerName}
          </h3>

          <div className="mt-2 flex items-center space-x-2">
            <span className="px-3 py-0.5 rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 text-xs font-mono font-bold">
              {formatCallTime(callDuration)}
            </span>
          </div>

          {/* Animated Audio Equalizer Bars */}
          <div className="flex items-center space-x-1 my-6 h-8">
            <span className="w-1 bg-[#2481cc] rounded-full animate-bounce h-4" />
            <span className="w-1 bg-[#2481cc] rounded-full animate-bounce h-7 delay-75" />
            <span className="w-1 bg-[#2481cc] rounded-full animate-bounce h-5 delay-150" />
            <span className="w-1 bg-[#2481cc] rounded-full animate-bounce h-8 delay-100" />
            <span className="w-1 bg-[#2481cc] rounded-full animate-bounce h-6 delay-200" />
            <span className="w-1 bg-[#2481cc] rounded-full animate-bounce h-4 delay-300" />
          </div>

          {/* Voice Call Controls Toolbar */}
          <div className="flex items-center space-x-5 mt-2">
            <button
              onClick={toggleMute}
              title={isMuted ? 'Bật Microphone' : 'Tắt Microphone'}
              className={`p-3.5 rounded-full transition-colors ${
                isMuted
                  ? 'bg-amber-500 text-white shadow-lg shadow-amber-500/30'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>

            <button
              onClick={() => setIsSpeakerMuted(!isSpeakerMuted)}
              title={isSpeakerMuted ? 'Bật Loa ngoài' : 'Tắt Loa ngoài'}
              className={`p-3.5 rounded-full transition-colors ${
                isSpeakerMuted
                  ? 'bg-amber-500 text-white shadow-lg shadow-amber-500/30'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              {isSpeakerMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
            </button>

            <button
              onClick={handleEndCall}
              title="Kết thúc cuộc gọi thoại"
              className="p-4 rounded-full bg-red-600 hover:bg-red-700 active:scale-95 text-white shadow-xl shadow-red-600/40 transition-transform cursor-pointer"
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
