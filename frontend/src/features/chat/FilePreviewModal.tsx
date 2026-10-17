import React, { useState, useEffect } from 'react';
import { X, Download, FileText, FolderArchive, Music, Video, Image as ImageIcon, Copy, Check, Loader2 } from 'lucide-react';
import { apiService } from '../../services/api';
import { formatFileSize } from '../../lib/utils';

interface FilePreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  fileId: string | number;
  fileName: string;
  fileSize?: number;
  fileType?: string;
}

export const FilePreviewModal: React.FC<FilePreviewModalProps> = ({
  isOpen,
  onClose,
  fileId,
  fileName,
  fileSize,
  fileType,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [textContent, setTextContent] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [rawBase64, setRawBase64] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !fileId) return;

    setLoading(true);
    setError(null);
    setBlobUrl(null);
    setTextContent(null);
    setRawBase64(null);

    let active = true;

    apiService
      .downloadFile(fileId)
      .then((res) => {
        if (!active) return;
        if (res && res.file_data) {
          setRawBase64(res.file_data);
          const ext = fileName.split('.').pop()?.toLowerCase() || '';

          // 1. Detect MIME type
          let mime = fileType || res.file_type || 'application/octet-stream';
          if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'].includes(ext)) {
            mime = ext === 'svg' ? 'image/svg+xml' : `image/${ext === 'jpg' ? 'jpeg' : ext}`;
          } else if (ext === 'pdf') {
            mime = 'application/pdf';
          } else if (['mp4', 'webm', 'mov', 'mkv'].includes(ext)) {
            mime = `video/${ext === 'mov' ? 'mp4' : ext}`;
          } else if (['mp3', 'wav', 'ogg', 'm4a', 'aac'].includes(ext)) {
            mime = `audio/${ext}`;
          } else if (['txt', 'json', 'csv', 'md', 'log', 'xml', 'js', 'ts', 'html', 'css', 'py'].includes(ext)) {
            mime = 'text/plain;charset=utf-8';
          }

          try {
            // Convert Base64 to byte array
            const binaryString = atob(res.file_data);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
              bytes[i] = binaryString.charCodeAt(i);
            }

            // Check if it's text/code
            if (['txt', 'json', 'csv', 'md', 'log', 'xml', 'js', 'ts', 'html', 'css', 'py'].includes(ext)) {
              const decoder = new TextDecoder('utf-8');
              const text = decoder.decode(bytes);
              setTextContent(text);
            }

            const blob = new Blob([bytes], { type: mime });
            const url = URL.createObjectURL(blob);
            setBlobUrl(url);
          } catch (e: any) {
            console.warn('[FilePreview] Error creating blob:', e);
          }
          setLoading(false);
        } else {
          setError(res?.message || 'Không thể tải dữ liệu tệp tin.');
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!active) return;
        setError(err?.message || 'Lỗi kết nối khi tải tệp.');
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [isOpen, fileId, fileName]);

  // Clean up blob URL on unmount or close
  useEffect(() => {
    return () => {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [blobUrl]);

  if (!isOpen) return null;

  const ext = fileName.split('.').pop()?.toLowerCase() || '';
  const isImage = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'].includes(ext);
  const isPdf = ext === 'pdf';
  const isVideo = ['mp4', 'webm', 'mov', 'mkv'].includes(ext);
  const isAudio = ['mp3', 'wav', 'ogg', 'm4a', 'aac'].includes(ext);
  const isText = ['txt', 'json', 'csv', 'md', 'log', 'xml', 'js', 'ts', 'html', 'css', 'py'].includes(ext);
  const isZip = ['zip', 'rar', '7z', 'tar', 'gz', 'bz2'].includes(ext);
  const isOffice = ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'].includes(ext);

  const handleDownload = async () => {
    if (!rawBase64) {
      if (fileId) {
        const res = await apiService.downloadFile(fileId);
        if (res && res.file_data) {
          await apiService.saveDownloadedFile(fileName, res.file_data);
        }
      }
      return;
    }
    await apiService.saveDownloadedFile(fileName, rawBase64);
  };

  const handleCopyText = () => {
    if (textContent) {
      navigator.clipboard.writeText(textContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-150 select-none"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative w-full max-w-4xl max-h-[90vh] bg-white dark:bg-[#182533] border border-slate-200 dark:border-slate-700/80 rounded-3xl shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-150"
      >
        {/* Header Bar */}
        <div className="h-14 px-5 border-b border-slate-200 dark:border-slate-700/80 flex items-center justify-between bg-slate-50 dark:bg-[#131d27]">
          <div className="flex items-center space-x-3 min-w-0 pr-4">
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm ${
                isImage
                  ? 'bg-sky-500/15 text-[#2481cc]'
                  : isVideo
                  ? 'bg-emerald-500/15 text-emerald-500'
                  : isAudio
                  ? 'bg-violet-500/15 text-violet-500'
                  : isPdf
                  ? 'bg-rose-500/15 text-rose-500'
                  : isZip
                  ? 'bg-amber-500/15 text-amber-500'
                  : 'bg-indigo-500/15 text-indigo-500'
              }`}
            >
              {isImage ? (
                <ImageIcon className="w-5 h-5" />
              ) : isVideo ? (
                <Video className="w-5 h-5" />
              ) : isAudio ? (
                <Music className="w-5 h-5" />
              ) : isZip ? (
                <FolderArchive className="w-5 h-5" />
              ) : (
                <FileText className="w-5 h-5" />
              )}
            </div>
            <div className="flex flex-col min-w-0">
              <span className="font-bold text-sm text-slate-800 dark:text-slate-100 truncate block">
                {fileName}
              </span>
              <span className="text-[11px] text-slate-400">
                {formatFileSize(fileSize)} {ext ? `• Định dạng .${ext.toUpperCase()}` : ''}
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleDownload}
              title="Tải tệp tin về máy tính"
              className="px-3.5 py-1.5 rounded-xl bg-[#2481cc] hover:bg-[#1d73b8] active:scale-95 text-white font-semibold text-xs flex items-center space-x-1.5 shadow-sm transition-all cursor-pointer"
            >
              <Download className="w-4 h-4" />
              <span>Tải về</span>
            </button>

            <button
              onClick={onClose}
              title="Đóng cửa sổ"
              className="p-2 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700/60 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Preview Content Area */}
        <div className="flex-1 overflow-auto p-4 flex flex-col items-center justify-center min-h-[350px] max-h-[78vh] bg-slate-100 dark:bg-[#0e1621]">
          {loading ? (
            <div className="flex flex-col items-center justify-center p-12 text-slate-400">
              <Loader2 className="w-10 h-10 animate-spin text-[#2481cc] mb-3" />
              <span className="text-xs font-medium">Đang tải và chuẩn bị xem trước...</span>
            </div>
          ) : error ? (
            <div className="text-center p-8 text-rose-500 dark:text-rose-400 max-w-md">
              <p className="text-sm font-semibold mb-2">{error}</p>
              <p className="text-xs opacity-80 mb-4">Bạn có thể bấm Tải về để lưu trực tiếp về máy tính.</p>
              <button
                onClick={handleDownload}
                className="px-4 py-2 rounded-xl bg-[#2481cc] text-white text-xs font-semibold shadow-md"
              >
                Tải tệp tin về máy
              </button>
            </div>
          ) : isImage && blobUrl ? (
            <div className="max-h-full max-w-full flex items-center justify-center p-2">
              <img
                src={blobUrl}
                alt={fileName}
                className="max-h-[72vh] w-auto max-w-full rounded-2xl shadow-xl object-contain border border-slate-200 dark:border-slate-700/60"
              />
            </div>
          ) : isPdf && blobUrl ? (
            <div className="w-full h-[72vh] rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-700/60 shadow-lg bg-white">
              <iframe src={blobUrl} title={fileName} className="w-full h-full border-none" />
            </div>
          ) : isVideo && blobUrl ? (
            <div className="max-w-3xl w-full flex items-center justify-center">
              <video
                controls
                autoPlay
                src={blobUrl}
                className="max-h-[72vh] w-full rounded-2xl shadow-xl bg-black"
              />
            </div>
          ) : isAudio && blobUrl ? (
            <div className="w-full max-w-md p-8 bg-white dark:bg-[#1a2532] rounded-3xl border border-slate-200 dark:border-slate-700/80 shadow-xl flex flex-col items-center">
              <div className="w-20 h-20 rounded-full bg-violet-500/15 text-violet-500 flex items-center justify-center mb-4 shadow-inner">
                <Music className="w-10 h-10" />
              </div>
              <h4 className="font-bold text-sm text-slate-800 dark:text-slate-100 mb-1 text-center truncate max-w-full">
                {fileName}
              </h4>
              <span className="text-xs text-slate-400 mb-6">{formatFileSize(fileSize)}</span>
              <audio controls autoPlay src={blobUrl} className="w-full" />
            </div>
          ) : isText && textContent !== null ? (
            <div className="w-full h-[70vh] flex flex-col bg-white dark:bg-[#131d27] rounded-2xl border border-slate-200 dark:border-slate-700/80 shadow-md overflow-hidden">
              <div className="px-4 py-2 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-[#1a2532] text-xs">
                <span className="text-slate-500 dark:text-slate-400">
                  {textContent.split('\n').length} dòng văn bản
                </span>
                <button
                  onClick={handleCopyText}
                  className="px-2.5 py-1 rounded-lg bg-slate-200 dark:bg-slate-700/80 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 flex items-center space-x-1 font-medium transition-colors"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Đã sao chép' : 'Sao chép'}</span>
                </button>
              </div>
              <pre className="flex-1 p-4 font-mono text-xs text-slate-800 dark:text-slate-200 overflow-auto whitespace-pre-wrap select-text leading-relaxed">
                {textContent}
              </pre>
            </div>
          ) : (
            /* Fallback for binary formats (Office, Zip, Exe, etc.) */
            <div className="w-full max-w-md p-8 bg-white dark:bg-[#1a2532] rounded-3xl border border-slate-200 dark:border-slate-700/80 shadow-xl flex flex-col items-center text-center">
              <div
                className={`w-20 h-20 rounded-3xl flex items-center justify-center mb-4 shadow-sm ${
                  isZip
                    ? 'bg-amber-500/15 text-amber-500'
                    : isOffice
                    ? 'bg-blue-500/15 text-blue-500'
                    : 'bg-indigo-500/15 text-indigo-500'
                }`}
              >
                {isZip ? <FolderArchive className="w-10 h-10" /> : <FileText className="w-10 h-10" />}
              </div>
              <h4 className="font-bold text-base text-slate-800 dark:text-slate-100 mb-1 max-w-full truncate">
                {fileName}
              </h4>
              <span className="text-xs text-slate-400 mb-4">{formatFileSize(fileSize)}</span>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-6 leading-relaxed">
                Tệp tin dạng <span className="font-semibold text-slate-700 dark:text-slate-300">.{ext.toUpperCase()}</span> cần tải về máy tính để mở bằng phần mềm chuyên dụng (Word, Excel, WinRAR...).
              </p>
              <button
                onClick={handleDownload}
                className="w-full py-2.5 px-4 rounded-2xl bg-[#2481cc] hover:bg-[#1d73b8] active:scale-95 text-white font-bold text-xs flex items-center justify-center space-x-2 shadow-lg shadow-[#2481cc]/25 transition-all cursor-pointer"
              >
                <Download className="w-4 h-4" />
                <span>Tải tệp tin về máy tính</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
