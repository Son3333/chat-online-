import React, { useState, useEffect, useRef } from 'react';
import { X, Check, Sparkles, Upload, ZoomIn, ZoomOut, Move, Trash2 } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { apiService } from '../../services/api';

interface ChatThemeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PRESET_THEMES = [
  { id: 'default', name: 'Mặc định', bgClass: 'bg-slate-50 dark:bg-[#0e1621]', preview: 'linear-gradient(to bottom right, #f8fafc, #0e1621)' },
  { id: 'ocean', name: 'Đại dương xanh', bgClass: 'bg-gradient-to-br from-cyan-950/40 via-blue-900/30 to-slate-900', preview: 'linear-gradient(135deg, #083344, #1e3a8a, #0f172a)' },
  { id: 'sunset', name: 'Hoàng hôn tím', bgClass: 'bg-gradient-to-br from-purple-950/40 via-pink-900/25 to-slate-900', preview: 'linear-gradient(135deg, #3b0764, #831843, #0f172a)' },
  { id: 'emerald', name: 'Rừng nhiệt đới', bgClass: 'bg-gradient-to-br from-emerald-950/40 via-teal-900/25 to-slate-900', preview: 'linear-gradient(135deg, #022c22, #134e4a, #0f172a)' },
  { id: 'amber', name: 'Cà phê ấm áp', bgClass: 'bg-gradient-to-br from-amber-950/40 via-orange-950/30 to-slate-900', preview: 'linear-gradient(135deg, #451a03, #431407, #0f172a)' },
  { id: 'neon_night', name: 'Đêm Neon Cyber', bgClass: 'bg-gradient-to-br from-indigo-950/50 via-slate-900 to-black', preview: 'linear-gradient(135deg, #1e1b4b, #0f172a, #000000)' },
  { id: 'rose', name: 'Hồng ngọt ngào', bgClass: 'bg-gradient-to-br from-rose-950/40 via-pink-950/30 to-slate-900', preview: 'linear-gradient(135deg, #4c0519, #500724, #0f172a)' },
];

export const ChatThemeModal: React.FC<ChatThemeModalProps> = ({ isOpen, onClose }) => {
  const { activeConv, currentUser, refreshConversations, setActiveConv } = useChat();
  const [selectedTheme, setSelectedTheme] = useState<string>('default');
  const [customBgUrl, setCustomBgUrl] = useState<string>('');
  const [isSaving, setIsSaving] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // States for Image Cropper / Adjuster
  const [rawImageSrc, setRawImageSrc] = useState<string | null>(null);
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const imageRef = useRef<HTMLImageElement | null>(null);

  // Synchronize state strictly with the currently active conversation
  useEffect(() => {
    if (!isOpen || !activeConv) return;
    const currentTheme = activeConv.theme || 'default';
    const isCustom = currentTheme.startsWith('data:image/') || currentTheme.startsWith('http');
    if (isCustom) {
      setSelectedTheme('custom');
      setCustomBgUrl(currentTheme);
    } else {
      setSelectedTheme(currentTheme);
      setCustomBgUrl('');
    }
    // Reset any pending crop session
    setRawImageSrc(null);
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, [isOpen, activeConv?.id, activeConv?.theme]);

  if (!isOpen || !activeConv || !currentUser) return null;

  const handleSelectTheme = (themeId: string) => {
    setSelectedTheme(themeId);
    setCustomBgUrl('');
  };

  const handleCustomImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      alert('Vui lòng chọn tệp hình ảnh hợp lệ (PNG, JPG, WEBP)!');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = reader.result as string;
      setRawImageSrc(base64);
      setZoom(1);
      setPan({ x: 0, y: 0 });
    };
    reader.readAsDataURL(file);
    // Reset file input so user can choose the same file again if desired
    e.target.value = '';
  };

  // Drag & Pan handlers for Cropper
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Confirm Cropped Area using HTML5 Canvas
  const handleApplyCroppedImage = () => {
    if (!rawImageSrc || !imageRef.current) return;

    const img = imageRef.current;
    const canvas = document.createElement('canvas');
    // Target resolution for wallpaper (16:9 ratio, crisp yet lightweight)
    const targetWidth = 1280;
    const targetHeight = 720;
    canvas.width = targetWidth;
    canvas.height = targetHeight;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Viewport box in UI (aspect ratio 16:9)
    // Map pan & zoom onto the canvas
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, targetWidth, targetHeight);

    // Calculate scaling
    const containerWidth = 320;
    const containerHeight = 180;
    const scaleFactor = targetWidth / containerWidth;

    const renderX = pan.x * scaleFactor;
    const renderY = pan.y * scaleFactor;
    const renderW = (containerWidth * zoom * scaleFactor);
    const renderH = (containerHeight * zoom * scaleFactor);

    // Natural aspect ratio scaling
    const imgAspect = img.naturalWidth / img.naturalHeight;
    const containerAspect = containerWidth / containerHeight;

    let drawW = renderW;
    let drawH = renderH;
    if (imgAspect > containerAspect) {
      drawW = renderH * imgAspect;
    } else {
      drawH = renderW / imgAspect;
    }

    ctx.drawImage(img, renderX + (targetWidth - drawW) / 2, renderY + (targetHeight - drawH) / 2, drawW, drawH);

    const croppedBase64 = canvas.toDataURL('image/jpeg', 0.85);
    setCustomBgUrl(croppedBase64);
    setSelectedTheme('custom');
    setRawImageSrc(null);
  };

  const handleRemoveCustomBg = () => {
    setCustomBgUrl('');
    setSelectedTheme('default');
  };

  const handleSaveTheme = async () => {
    setIsSaving(true);
    try {
      const themeValue = selectedTheme === 'custom' ? customBgUrl : selectedTheme;
      const res = await apiService.updateConversationTheme(activeConv.id, currentUser.id, themeValue);
      if (res && res.success) {
        setActiveConv({ ...activeConv, theme: themeValue });
        await refreshConversations();
        onClose();
      } else {
        alert(res?.error || 'Không thể đổi giao diện cuộc trò chuyện!');
      }
    } catch (e: any) {
      alert(e.message || 'Không thể đổi giao diện lúc này. Vui lòng thử lại sau!');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 select-none animate-in fade-in duration-150"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md bg-white dark:bg-[#17212b] border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl flex flex-col overflow-hidden max-h-[90vh] animate-in zoom-in-95 duration-150"
      >
        {/* Header */}
        <div className="h-14 px-5 border-b border-slate-200 dark:border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-[#2481cc]" />
            <h3 className="font-bold text-base text-slate-800 dark:text-slate-100">
              {rawImageSrc ? 'Căn chỉnh ảnh nền chat' : 'Đổi giao diện đoạn chat'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 flex-1 overflow-y-auto space-y-4 text-xs">
          {rawImageSrc ? (
            /* Interactive Cropper & Pan-Zoom View */
            <div className="space-y-4">
              <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
                <span className="flex items-center space-x-1.5">
                  <Move className="w-3.5 h-3.5 text-[#2481cc]" />
                  <span>Kéo rê chuột để chỉnh góc ảnh mong muốn</span>
                </span>
                <span className="text-[11px] text-blue-500 font-medium">Tỉ lệ khung chat chuẩn</span>
              </div>

              {/* Viewport Box (Aspect ratio 16:9) */}
              <div
                className="w-full h-52 bg-slate-900 rounded-2xl overflow-hidden relative border-2 border-[#2481cc] shadow-inner cursor-grab active:cursor-grabbing flex items-center justify-center select-none"
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
              >
                <img
                  ref={imageRef}
                  src={rawImageSrc}
                  alt="Crop preview"
                  draggable={false}
                  className="pointer-events-none transition-transform duration-75 max-w-none"
                  style={{
                    transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                    maxHeight: '100%',
                  }}
                />
                <div className="absolute inset-0 pointer-events-none border border-white/20 rounded-2xl flex items-center justify-center">
                  <div className="w-full h-full border-dashed border border-white/30 grid grid-cols-3 grid-rows-3 opacity-40">
                    <div className="border-r border-b border-white/20"></div>
                    <div className="border-r border-b border-white/20"></div>
                    <div className="border-b border-white/20"></div>
                    <div className="border-r border-b border-white/20"></div>
                    <div className="border-r border-b border-white/20"></div>
                    <div className="border-b border-white/20"></div>
                    <div className="border-r border-white/20"></div>
                    <div className="border-r border-white/20"></div>
                    <div></div>
                  </div>
                </div>
              </div>

              {/* Zoom Controls */}
              <div className="flex items-center space-x-3 bg-slate-50 dark:bg-slate-800/50 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
                <ZoomOut className="w-4 h-4 text-slate-400" />
                <input
                  type="range"
                  min="1"
                  max="3"
                  step="0.05"
                  value={zoom}
                  onChange={(e) => setZoom(parseFloat(e.target.value))}
                  className="flex-1 accent-[#2481cc] cursor-pointer"
                />
                <ZoomIn className="w-4 h-4 text-[#2481cc]" />
                <span className="text-slate-600 dark:text-slate-300 font-mono w-10 text-right">
                  {Math.round(zoom * 100)}%
                </span>
              </div>

              {/* Action buttons for Crop */}
              <div className="flex items-center space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setRawImageSrc(null)}
                  className="flex-1 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-semibold transition-colors"
                >
                  Hủy chỉnh sửa
                </button>
                <button
                  type="button"
                  onClick={handleApplyCroppedImage}
                  className="flex-1 py-2 rounded-xl bg-[#2481cc] hover:bg-[#1b6ca8] text-white font-bold transition-all shadow-md shadow-blue-500/20"
                >
                  Xác nhận vùng chọn
                </button>
              </div>
            </div>
          ) : (
            /* Standard Theme & Wallpaper Selection */
            <>
              <p className="text-slate-500 dark:text-slate-400 text-xs">
                Chọn chủ đề màu sắc hoặc hình nền riêng cho cuộc trò chuyện này (áp dụng độc lập cho cuộc trò chuyện đang mở):
              </p>

              {/* Grid preset themes */}
              <div className="grid grid-cols-2 gap-3">
                {PRESET_THEMES.map((th) => {
                  const isSelected = selectedTheme === th.id;
                  return (
                    <div
                      key={th.id}
                      onClick={() => handleSelectTheme(th.id)}
                      className={`p-3 rounded-2xl border cursor-pointer transition-all flex flex-col space-y-2.5 relative group ${
                        isSelected
                          ? 'border-[#2481cc] ring-2 ring-blue-500/20 bg-blue-500/5'
                          : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                      }`}
                    >
                      <div
                        className="w-full h-14 rounded-xl shadow-inner flex items-center justify-center relative overflow-hidden"
                        style={{ background: th.preview }}
                      >
                        {isSelected && (
                          <div className="w-6 h-6 rounded-full bg-[#2481cc] text-white flex items-center justify-center shadow-md">
                            <Check className="w-3.5 h-3.5 stroke-[3]" />
                          </div>
                        )}
                      </div>
                      <span className="font-semibold text-slate-800 dark:text-slate-200 text-center truncate">
                        {th.name}
                      </span>
                    </div>
                  );
                })}
              </div>

              {/* Custom Background Image Upload */}
              <div className="pt-2 border-t border-slate-200/60 dark:border-slate-800/80">
                <input
                  type="file"
                  ref={fileInputRef}
                  accept="image/*"
                  onChange={handleCustomImageUpload}
                  className="hidden"
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full py-2.5 px-3 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 hover:border-[#2481cc] dark:hover:border-[#2481cc] text-slate-600 dark:text-slate-300 flex items-center justify-center space-x-2 transition-colors cursor-pointer"
                >
                  <Upload className="w-4 h-4 text-[#2481cc]" />
                  <span>
                    {customBgUrl
                      ? 'Chọn ảnh khác hoặc căn chỉnh lại'
                      : 'Tải ảnh nền riêng từ máy tính (Có thể kéo, phóng to/thu nhỏ)'}
                  </span>
                </button>

                {customBgUrl && (
                  <div className="mt-2.5 flex items-center space-x-2">
                    <div
                      onClick={() => setSelectedTheme('custom')}
                      className={`flex-1 h-16 rounded-xl overflow-hidden border relative cursor-pointer ${
                        selectedTheme === 'custom'
                          ? 'border-[#2481cc] ring-2 ring-blue-500/20'
                          : 'border-slate-300 dark:border-slate-700'
                      }`}
                    >
                      <img src={customBgUrl} alt="Custom Theme" className="w-full h-full object-cover" />
                      <span className="absolute bottom-1 right-2 px-1.5 py-0.5 rounded text-[9px] bg-black/60 text-white font-semibold">
                        Ảnh nền đã căn chỉnh
                      </span>
                      {selectedTheme === 'custom' && (
                        <div className="absolute top-1 left-1 w-5 h-5 rounded-full bg-[#2481cc] text-white flex items-center justify-center">
                          <Check className="w-3 h-3 stroke-[3]" />
                        </div>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={handleRemoveCustomBg}
                      title="Xóa ảnh nền tùy chỉnh"
                      className="p-2.5 rounded-xl border border-rose-200 dark:border-rose-900/40 text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/20 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        {!rawImageSrc && (
          <div className="p-4 border-t border-slate-200 dark:border-slate-800/80 bg-slate-50 dark:bg-[#1a232e] flex items-center space-x-2.5">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-xl bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 font-semibold text-xs transition-colors cursor-pointer"
            >
              Hủy bỏ
            </button>
            <button
              type="button"
              disabled={isSaving}
              onClick={handleSaveTheme}
              className="flex-1 py-2.5 rounded-xl bg-[#2481cc] hover:bg-[#1b6ca8] text-white font-bold text-xs transition-all active:scale-95 disabled:opacity-50 shadow-md shadow-blue-500/20 cursor-pointer"
            >
              {isSaving ? 'Đang lưu...' : 'Áp Dụng Giao Diện'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
