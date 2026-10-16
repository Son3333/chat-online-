import React, { useState } from 'react';
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
  const [address, setAddress] = useState('📍 Hà Nội, Việt Nam');
  const [isGettingGPS, setIsGettingGPS] = useState(false);
  const [gpsStatus, setGpsStatus] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleGetGPS = () => {
    setIsGettingGPS(true);
    setGpsStatus('Đang truy vấn tọa độ thiết bị...');

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = pos.coords.latitude.toFixed(6);
          const lng = pos.coords.longitude.toFixed(6);
          const gpsLoc = `📍 Tọa độ GPS: ${lat}, ${lng}`;
          setAddress(gpsLoc);
          setIsGettingGPS(false);
          setGpsStatus('Đã lấy tọa độ GPS thành công!');
        },
        () => {
          setIsGettingGPS(false);
          setGpsStatus('Không có cảm biến GPS, đã giữ địa điểm mặc định.');
        },
        { timeout: 4000, enableHighAccuracy: true }
      );
    } else {
      setIsGettingGPS(false);
      setGpsStatus('Trình duyệt không hỗ trợ Geolocation.');
    }
  };

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
            onClick={handleGetGPS}
            disabled={isGettingGPS}
            className="w-full py-2 px-3 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 dark:text-rose-400 text-xs font-semibold flex items-center justify-center space-x-2 border border-rose-500/20 transition-colors disabled:opacity-50"
          >
            <Navigation className={`w-3.5 h-3.5 ${isGettingGPS ? 'animate-spin' : ''}`} />
            <span>{isGettingGPS ? 'Đang định vị GPS...' : '📍 Lấy tự động tọa độ GPS thiết bị'}</span>
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

