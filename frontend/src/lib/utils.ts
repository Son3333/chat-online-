import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Parse server timestamp (which SQLite stores as UTC "YYYY-MM-DD HH:MM:SS")
 * and converts it into a valid Date object in local device timezone (Vietnam UTC+7).
 */
export function parseServerDate(isoString?: string): Date | null {
  if (!isoString) return null;
  try {
    let str = isoString.trim();
    // If SQLite string without timezone suffix (e.g. "2026-11-25 15:58:00"), treat as UTC
    if (!str.endsWith('Z') && !str.includes('+') && !/T.*[+-]\d{2}:\d{2}$/.test(str)) {
      str = str.replace(' ', 'T') + 'Z';
    }
    const d = new Date(str);
    return isNaN(d.getTime()) ? null : d;
  } catch {
    return null;
  }
}

export function formatTime(isoString?: string): string {
  const d = parseServerDate(isoString);
  if (!d) return '';
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
}

export function formatDate(isoString?: string): string {
  const d = parseServerDate(isoString);
  if (!d) return '';
  const now = new Date();
  const isToday = d.toDateString() === now.toDateString();
  if (isToday) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
  }
  return d.toLocaleDateString([], { day: '2-digit', month: '2-digit' });
}

export function formatFileSize(bytes?: number): string {
  if (!bytes || bytes <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

export function getInitials(name?: string): string {
  if (!name) return 'U';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
}
