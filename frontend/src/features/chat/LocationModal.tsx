import React, { useState, useEffect, useRef } from 'react';
import { MapPin, X, Navigation, Check, Send, Search, Loader2, Info } from 'lucide-react';

interface LocationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSendLocation: (locationText: string) => void;
}

const PRESET_LOCATIONS = [
  { name: 'Đại học Bách Khoa Hà Nội', lat: 21.004481, lng: 105.843653 },
  { name: 'Hồ Hoàn Kiếm, Hà Nội', lat: 21.028775, lng: 105.852378 },
  { name: 'Hà Nội, Việt Nam', lat: 21.028511, lng: 105.854167 },
  { name: 'TP. Hồ Chí Minh', lat: 10.776889, lng: 106.700806 },
  { name: 'Sân bay Nội Bài', lat: 21.221235, lng: 105.807185 },
  { name: 'Đà Nẵng, Việt Nam', lat: 16.054407, lng: 108.202167 },
];

export const LocationModal: React.FC<LocationModalProps> = ({
  isOpen,
  onClose,
  onSendLocation,
}) => {
  const [address, setAddress] = useState('📍 Đang xác định vị trí thực tế...');
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [isGettingGPS, setIsGettingGPS] = useState(false);
  const [gpsStatus, setGpsStatus] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const searchTimeoutRef = useRef<any>(null);

  const detectRealtimeLocation = async () => {
    setIsGettingGPS(true);
    setGpsStatus('Đang xác định vị trí qua mạng Internet...');

    // 1. Try hardware GPS (if laptop has GPS / browser location)
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

    // 2. Fast IP Geolocation
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
              return { lat: Number(lat), lng: Number(lng), city, country };
            }
          }
        } catch {
          // next
        }
      }
      return null;
    };

    const gpsResult = await tryHardwareGPS();
    if (gpsResult) {
      setCoords({ lat: gpsResult.lat, lng: gpsResult.lng });
      setAddress(`📍 Vị trí GPS: ${gpsResult.lat.toFixed(6)}, ${gpsResult.lng.toFixed(6)}`);
      setIsGettingGPS(false);
      setGpsStatus('Đã định vị thành công bằng GPS!');
      return;
    }

    const netResult = await tryNetworkLocation();
    if (netResult) {
      setCoords({ lat: netResult.lat, lng: netResult.lng });
      setAddress(`📍 Vị trí mạng: ${netResult.lat.toFixed(6)}, ${netResult.lng.toFixed(6)} (${netResult.city}, ${netResult.country})`);
      setIsGettingGPS(false);
      setGpsStatus(`Định vị ước tính theo IP mạng: ${netResult.city}`);
      return;
    }

    const fallbackLat = 21.024467;
    const fallbackLng = 105.841167;
    setCoords({ lat: fallbackLat, lng: fallbackLng });
    setAddress(`📍 Vị trí: ${fallbackLat.toFixed(6)}, ${fallbackLng.toFixed(6)} (Hà Nội, Việt Nam)`);
    setIsGettingGPS(false);
    setGpsStatus('Vị trí mặc định: Hà Nội');
  };

  const handleSearchChange = (val: string) => {
    setSearchQuery(val);
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    if (!val.trim() || val.trim().length < 2) {
      setSearchResults([]);
      return;
    }

    searchTimeoutRef.current = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await fetch(
          `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(val)}&countrycodes=vn&limit=5`,
          { headers: { 'Accept-Language': 'vi' } }
        );
        if (res.ok) {
          const data = await res.json();
          setSearchResults(data);
        }
      } catch {
        // search fallback
      } finally {
        setIsSearching(false);
      }
    }, 400);
  };

  const handleSelectSearchResult = (item: any) => {
    const lat = parseFloat(item.lat);
    const lng = parseFloat(item.lon);
    setCoords({ lat, lng });
    const shortName = item.display_name.split(',').slice(0, 3).join(', ');
    setAddress(`📍 ${shortName}: ${lat.toFixed(6)}, ${lng.toFixed(6)}`);
    setSearchResults([]);
    setSearchQuery('');
    setGpsStatus(`Đã chọn: ${shortName}`);
  };

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

  const handleSelectPreset = (p: { name: string; lat: number; lng: number }) => {
    setCoords({ lat: p.lat, lng: p.lng });
    setAddress(`📍 ${p.name}: ${p.lat.toFixed(6)}, ${p.lng.toFixed(6)}`);
    setSearchResults([]);
  };

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 select-none animate-in fade-in duration-150"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md bg-white dark:bg-[#17212b] border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl p-5 flex flex-col animate-in zoom-in-95 duration-150"
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-3">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-rose-500/15 text-rose-500 flex items-center justify-center shadow-sm">
              <MapPin className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-slate-800 dark:text-slate-100">
                Chia Sẻ Vị Trí Trực Tiếp
              </h3>
              <p className="text-[11px] text-slate-400">
                Gửi vị trí có bản đồ & chỉ đường Google Maps
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

        {/* Live Visual Map Preview */}
        <div className="relative w-full h-36 rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 mb-2.5 shadow-inner">
          {coords ? (
            <iframe
              title="Realtime Map Preview"
              width="100%"
              height="100%"
              frameBorder="0"
              scrolling="no"
              src={`https://www.openstreetmap.org/export/embed.html?bbox=${coords.lng - 0.007}%2C${coords.lat - 0.004}%2C${coords.lng + 0.007}%2C${coords.lat + 0.004}&layer=mapnik&marker=${coords.lat}%2C${coords.lng}`}
              className="w-full h-full pointer-events-none select-none"
            />
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center text-slate-400 animate-pulse">
              <Navigation className="w-6 h-6 animate-spin text-[#2481cc] mb-1.5" />
              <span className="text-xs">Đang tải bản đồ vệ tinh...</span>
            </div>
          )}
        </div>

        {/* Search Input Box */}
        <div className="relative mb-2">
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              placeholder="🔍 Tìm kiếm địa điểm, số nhà, tên đường..."
              className="w-full h-9 px-3.5 pr-8 rounded-xl bg-slate-100 dark:bg-[#242f3d] text-xs font-medium text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#2481cc] border border-transparent dark:border-slate-700/60 transition-all"
            />
            {isSearching ? (
              <Loader2 className="w-4 h-4 text-[#2481cc] absolute right-2.5 top-2.5 animate-spin" />
            ) : (
              <Search className="w-4 h-4 text-slate-400 absolute right-2.5 top-2.5 pointer-events-none" />
            )}
          </div>

          {/* Autocomplete Dropdown */}
          {searchResults.length > 0 && (
            <div className="absolute left-0 right-0 top-10 z-30 bg-white dark:bg-[#1f2b38] border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl overflow-hidden max-h-44 overflow-y-auto">
              {searchResults.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelectSearchResult(item)}
                  className="w-full px-3 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-700/50 flex items-start space-x-2 text-xs border-b border-slate-100 dark:border-slate-800 last:border-0"
                >
                  <MapPin className="w-3.5 h-3.5 text-rose-500 flex-shrink-0 mt-0.5" />
                  <span className="text-slate-700 dark:text-slate-200 line-clamp-2">
                    {item.display_name}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Current Address & Re-detect */}
        <div className="mb-2 p-2 rounded-xl bg-slate-50 dark:bg-[#1a2530] border border-slate-200/80 dark:border-slate-800 flex items-center justify-between text-xs">
          <div className="flex-1 min-w-0 pr-2">
            <span className="text-[10px] text-slate-400 block font-medium">Vị trí hiện tại sẽ gửi:</span>
            <span className="font-semibold text-slate-700 dark:text-slate-200 truncate block">
              {address}
            </span>
            {gpsStatus && (
              <span className="text-[10px] text-emerald-600 dark:text-emerald-400 mt-0.5 flex items-center space-x-1 truncate">
                <Check className="w-2.5 h-2.5 flex-shrink-0" />
                <span className="truncate">{gpsStatus}</span>
              </span>
            )}
          </div>
          <button
            onClick={detectRealtimeLocation}
            disabled={isGettingGPS}
            title="Định vị lại"
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors flex-shrink-0"
          >
            <Navigation className={`w-4 h-4 ${isGettingGPS ? 'animate-spin text-rose-500' : ''}`} />
          </button>
        </div>

        {/* Explain PC limitation */}
        <div className="mb-2.5 px-2 py-1.5 rounded-lg bg-blue-50/70 dark:bg-blue-950/30 text-[11px] text-blue-700 dark:text-blue-300 flex items-start space-x-1.5">
          <Info className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-[#2481cc]" />
          <span>
            Máy tính không có chip vệ tinh GPS như điện thoại nên định vị tự động ước lượng theo IP mạng. Bạn có thể <strong>tìm kiếm địa chỉ</strong> ở trên để ghim chính xác 100%.
          </span>
        </div>

        {/* Quick Presets */}
        <div className="mb-3.5">
          <span className="block text-[11px] font-medium text-slate-400 mb-1.5">
            Hoặc chọn nhanh địa điểm phổ biến:
          </span>
          <div className="flex flex-wrap gap-1.5 max-h-16 overflow-y-auto pr-1">
            {PRESET_LOCATIONS.map((loc) => (
              <button
                key={loc.name}
                onClick={() => handleSelectPreset(loc)}
                className={`px-2.5 py-1 rounded-lg text-xs transition-all ${
                  address.includes(loc.name)
                    ? 'bg-[#2481cc] text-white shadow-sm font-semibold'
                    : 'bg-slate-100 dark:bg-[#202b36] text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                }`}
              >
                📍 {loc.name}
              </button>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2 pt-2 border-t border-slate-100 dark:border-slate-800">
          <button
            onClick={onClose}
            className="py-2.5 px-4 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-xs font-semibold text-slate-600 dark:text-slate-300 transition-colors"
          >
            Hủy
          </button>
          <button
            onClick={handleSend}
            className="flex-1 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white text-xs font-bold flex items-center justify-center space-x-1.5 shadow-md shadow-emerald-600/20 transition-all"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Chia Sẻ Vị Trí Này</span>
          </button>
        </div>
      </div>
    </div>
  );
};
