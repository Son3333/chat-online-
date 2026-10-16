"""
Module Thông báo Toast Desktop (Desktop Toast Notification)
- Hiển thị pop-up thông báo hiện đại ở góc dưới bên phải màn hình khi có tin nhắn mới.
- Tự động đóng sau 4 giây hoặc click để mở ngay cuộc trò chuyện.
"""

import tkinter as tk
from typing import Optional, Callable

class ToastNotification:
    _active_toasts = []

    def __init__(self, parent: tk.Tk, title: str, message: str, avatar_color="#2563EB", 
                 on_click: Optional[Callable] = None, duration_ms=4500):
        self.parent = parent
        self.title = title
        self.message = message
        self.avatar_color = avatar_color
        self.on_click = on_click
        self.duration_ms = duration_ms

        self.win = None
        self._show()

    def _show(self):
        try:
            self.win = tk.Toplevel(self.parent)
            self.win.overrideredirect(True)
            self.win.attributes("-topmost", True)
            self.win.configure(bg="#1E293B")

            # Tính toán vị trí góc dưới bên phải màn hình
            sw = self.win.winfo_screenwidth()
            sh = self.win.winfo_screenheight()
            w = 340
            h = 85
            margin_right = 24
            margin_bottom = 50 + (len(ToastNotification._active_toasts) * 95)

            x = sw - w - margin_right
            y = sh - h - margin_bottom
            self.win.geometry(f"{w}x{h}+{x}+{y}")

            ToastNotification._active_toasts.append(self)

            # Container
            card = tk.Frame(self.win, bg="#1E293B", highlightthickness=1, highlightbackground="#334155")
            card.pack(fill=tk.BOTH, expand=True)

            # Click handler
            def _handle_click(e=None):
                if self.on_click:
                    self.on_click()
                self._close()

            card.bind("<Button-1>", _handle_click)

            # Cột trái: Avatar tròn nhỏ
            avatar_lbl = tk.Label(card, text=self.title[:1].upper() if self.title else "💬", 
                                  font=("Segoe UI", 12, "bold"), fg="white", bg=self.avatar_color, 
                                  width=3, height=1)
            avatar_lbl.pack(side=tk.LEFT, padx=(12, 10), pady=12)
            avatar_lbl.bind("<Button-1>", _handle_click)

            # Cột giữa: Tiêu đề & nội dung
            text_frame = tk.Frame(card, bg="#1E293B")
            text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=10)
            text_frame.bind("<Button-1>", _handle_click)

            title_lbl = tk.Label(text_frame, text=self.title, font=("Segoe UI", 10, "bold"), 
                                 fg="#F8FAFC", bg="#1E293B", anchor="w")
            title_lbl.pack(fill=tk.X)
            title_lbl.bind("<Button-1>", _handle_click)

            preview = self.message.replace("\n", " ")
            if len(preview) > 42:
                preview = preview[:40] + "..."
            msg_lbl = tk.Label(text_frame, text=preview, font=("Segoe UI", 9), 
                               fg="#94A3B8", bg="#1E293B", anchor="w")
            msg_lbl.pack(fill=tk.X, pady=(2, 0))
            msg_lbl.bind("<Button-1>", _handle_click)

            # Cột phải: Nút tắt [×]
            close_btn = tk.Label(card, text="✕", font=("Segoe UI", 9), fg="#64748B", bg="#1E293B", cursor="hand2")
            close_btn.pack(side=tk.RIGHT, padx=10, pady=10, anchor="ne")
            close_btn.bind("<Button-1>", lambda e: self._close())
            close_btn.bind("<Enter>", lambda e: close_btn.configure(fg="#EF4444"))
            close_btn.bind("<Leave>", lambda e: close_btn.configure(fg="#64748B"))

            # Tự động hủy sau duration_ms
            self.win.after(self.duration_ms, self._close)
        except Exception as e:
            print(f"[Toast] Lỗi hiển thị: {e}")

    def _close(self):
        try:
            if self in ToastNotification._active_toasts:
                ToastNotification._active_toasts.remove(self)
            if self.win and self.win.winfo_exists():
                self.win.destroy()
        except Exception:
            pass
