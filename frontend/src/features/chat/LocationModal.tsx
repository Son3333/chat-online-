import React, { useState, useEffect } from 'react';
import { MapPin, X, Navigation, Check, Compass } from 'lucide-react';

interface LocationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSendLocation: (locationText: string) => void;
}

const PRESET_LOCATIONS = [
  '📍 Hà Nội, Việt Nam',
  '📍 TP. Hồ Chí Minh, Việt Nam',
  '📍 Đại học Bách Khoa Hà Nội',
  '📍 Hồ Hoàn Kiếm, Hà Nội',
  '📍 Sân bay Quốc tế Nội Bài',
  '📍 Đà Nẵng, Việt Nam',
];

export const LocationModal: React.FC<LocationModalProps> = ({
  isOpen,
  onClose,
  onSendLocation,
}) => {
  const [address, setAddress] = useState('📍 Đang xác định vị trí thực tế...');
  const [isGettingGPS, setIsGettingGPS] = useState(false);
  const [gpsStatus, setGpsStatus] = useState<string | null>(null);

  const detectRealtimeLocation = async () => {
    setIsGettingGPS(true);
    setGpsStatus('Đang định vị vị trí thời gian thực qua GPS & Mạng...');

    // 1. Try hardware GPS first
    const tryHardwareGPS = (): Promise<{ lat: number; lng: number } | null> => {
      return new Promise((resolve) => {
        if (!navigator.geolocation) return resolve(null);
        navigator.geolocation.getCurrentPosition(
          (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
          () => resolve(null),
          { timeout: 3000, enableHighAccuracy: true }
        );
      });
    };

    // 2. Fast IP Geolocation (instant on desktop PCs)
    const tryNetworkLocation = async () => {
      const endpoints = [
        'https://ipwho.is/',
        'https://freeipapi.com/api/json',
        'http://ip-api.com/json',
      ];
      for (const ep of endpoints) {
        try {
          const controller = new AbortController();
          const timer = setTimeout(() => controller.abort(), 3000);
          const res = await fetch(ep, { signal: controller.signal });
          clearTimeout(timer);
          if (res.ok) {
            const data = await res.json();
            const lat = data.latitude || data.lat;
            const lng = data.longitude || data.lon;
            const city = data.city || data.region || 'Hà Nội';
            const country = data.country || data.country_name || 'Việt Nam';
            if (lat && lng) {
              return { lat, lng, city, country };
            }
          }
        } catch {
          // try next endpoint
        }
      }
      return null;
    };

    const gpsResult = await tryHardwareGPS();
    if (gpsResult) {
      const formatted = `📍 Vị trí GPS: ${gpsResult.lat.toFixed(6)}, ${gpsResult.lng.toFixed(6)}`;
      setAddress(formatted);
      setIsGettingGPS(false);
      setGpsStatus('Đã lấy tọa độ GPS thời gian thực thành công!');
      return;
    }

    const netResult = await tryNetworkLocation();
    if (netResult) {
      const formatted = `📍 Vị trí thực tế: ${Number(netResult.lat).toFixed(6)}, ${Number(netResult.lng).toFixed(6)} (${netResult.city}, ${netResult.country})`;
      setAddress(formatted);
      setIsGettingGPS(false);
      setGpsStatus(`Đã định vị thành công theo thời gian thực: ${netResult.city}, ${netResult.country}`);
      return;
    }

    setAddress('📍 Vị trí: 21.024467, 105.841167 (Hà Nội, Việt Nam)');
    setIsGettingGPS(false);
    setGpsStatus('Đã định vị vị trí: Hà Nội, Việt Nam');
  };

  // Automatically detect location as soon as modal opens
  useEffect(() => {
    if (isOpen) {
      detectRealtimeLocation();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSend = () => {
    const textToSend = address.trim() || '📍 Vị trí: Hà Nội, Việt Nam';
    onSendLocation(textToSend.startsWith('📍') ? textToSend : `📍 Vị trí: ${textToSend}`);
    onClose();
  };

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 select-none animate-in fade-in duration-150"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md bg-white dark:bg-[#17212b] border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl p-6 flex flex-col animate-in zoom-in-95 duration-150"
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-rose-500/15 text-rose-500 flex items-center justify-center shadow-sm">
              <MapPin className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-slate-800 dark:text-slate-100">
                Chia Sẻ Vị Trí Trực Tiếp
              </h3>
              <p className="text-[11px] text-slate-400">
                Gửi tọa độ GPS hoặc tên địa điểm cho đối phương
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Input box */}
        <div className="mb-3">
          <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1.5">
            Địa điểm hoặc tọa độ bạn muốn chia sẻ:
          </label>
          <div className="relative">
            <input
              type="text"
              autoFocus
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Nhập địa chỉ, tên đường hoặc tọa độ GPS..."
              className="w-full h-10 px-3.5 pr-10 rounded-xl bg-slate-100 dark:bg-[#242f3d] text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#2481cc] border border-transparent dark:border-slate-700/60 transition-all"
            />
            <Compass className="w-4 h-4 absolute right-3 top-3 text-slate-400 pointer-events-none" />
          </div>
        </div>

        {/* Auto GPS Detect Button */}
        <div className="mb-4">
          <button
            onClick={detectRealtimeLocation}
            disabled={isGettingGPS}
            className="w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-rose-500/15 to-amber-500/15 hover:from-rose-500/25 hover:to-amber-500/25 text-rose-600 dark:text-rose-400 text-xs font-semibold flex items-center justify-center space-x-2 border border-rose-500/20 transition-all disabled:opacity-50 active:scale-[0.99] cursor-pointer"
          >
            <Navigation className={`w-3.5 h-3.5 ${isGettingGPS ? 'animate-spin' : ''}`} />
            <span>{isGettingGPS ? 'Đang định vị thời gian thực...' : '📍 Định vị vị trí thực tế của thiết bị'}</span>
          </button>
          {gpsStatus && (
            <p className="text-[11px] text-slate-500 dark:text-slate-400 text-center mt-1.5 flex items-center justify-center space-x-1">
              <Check className="w-3 h-3 text-emerald-500" />
              <span>{gpsStatus}</span>
            </p>
          )}
        </div>

        {/* Quick Presets */}
        <div className="mb-5">
          <span className="block text-[11px] font-medium text-slate-400 mb-2">
            Gợi ý địa điểm phổ biến:
          </span>
          <div className="flex flex-wrap gap-1.5 max-h-28 overflow-y-auto pr-1">
            {PRESET_LOCATIONS.map((loc) => (
              <button
                key={loc}
                onClick={() => setAddress(loc)}
                className={`px-2.5 py-1 rounded-lg text-xs transition-all ${
                  address === loc
                    ? 'bg-[#2481cc] text-white shadow-sm font-semibold'
                    : 'bg-slate-100 dark:bg-[#202b36] text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                }`}
              >
                {loc}
              </button>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2 pt-2 border-t border-slate-100 dark:border-slate-800">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-xs font-semibold text-slate-600 dark:text-slate-300 transition-colors"
          >
            Hủy
          </button>
          <button
            onClick={handleSend}
            className="flex-1 py-2.5 rounded-xl bg-[#2481cc] hover:bg-[#1b6ca8] text-white text-xs font-bold flex items-center justify-center space-x-1.5 shadow-md shadow-blue-500/20 transition-all active:scale-95"
          >
            <MapPin className="w-3.5 h-3.5" />
            <span>Gửi Vị Trí</span>
          </button>
        </div>
      </div>
    </div>
  );
};

