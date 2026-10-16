"""
Module Khóa Ứng Dụng Nhanh (Quick Lock - Ctrl + L)
- Khóa toàn bộ giao diện màn hình ứng dụng ngay lập tức khi người dùng rời máy tính.
- Yêu cầu mật khẩu tài khoản hoặc mã PIN để mở khóa trở lại.
"""

import tkinter as tk
from typing import Callable

class QuickLockOverlay:
    def __init__(self, parent: tk.Tk, username: str, unlock_validator: Callable[[str], bool]):
        self.parent = parent
        self.username = username
        self.unlock_validator = unlock_validator
        self.overlay = None
        self.is_locked = False

    def lock(self):
        if self.is_locked:
            return
        self.is_locked = True

        self.overlay = tk.Frame(self.parent, bg="#0B132B")
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        center_card = tk.Frame(self.overlay, bg="#1C2541", padx=30, pady=30,
                               highlightthickness=1, highlightbackground="#3A506B")
        center_card.place(relx=0.5, rely=0.5, anchor="center")

        # Icon khóa
        lock_icon = tk.Label(center_card, text="🔒", font=("Segoe UI", 48), bg="#1C2541", fg="#48CAE4")
        lock_icon.pack(pady=(0, 10))

        title = tk.Label(center_card, text="ỨNG DỤNG ĐÃ BỊ KHÓA", font=("Segoe UI", 16, "bold"),
                         fg="#F8FAFC", bg="#1C2541")
        title.pack()

        sub = tk.Label(center_card, text=f"Tài khoản: {self.username}\nNhập mật khẩu để tiếp tục sử dụng",
                       font=("Segoe UI", 10), fg="#94A3B8", bg="#1C2541", justify="center")
        sub.pack(pady=(5, 20))

        # Input mật khẩu
        self.pwd_entry = tk.Entry(center_card, font=("Segoe UI", 12), show="●",
                                  bg="#0B132B", fg="white", insertbackground="white",
                                  relief=tk.FLAT, highlightthickness=1, highlightbackground="#48CAE4", width=24)
        self.pwd_entry.pack(pady=(0, 15), ipady=5)
        self.pwd_entry.focus_set()

        # Nút mở khóa
        unlock_btn = tk.Button(center_card, text="Mở khóa ngay", font=("Segoe UI", 11, "bold"),
                               bg="#0077B6", fg="white", activebackground="#023E8A", activeforeground="white",
                               relief=tk.FLAT, padx=20, pady=8, cursor="hand2", command=self._try_unlock)
        unlock_btn.pack(fill=tk.X)

        self.err_lbl = tk.Label(center_card, text="", font=("Segoe UI", 9), fg="#EF4444", bg="#1C2541")
        self.err_lbl.pack(pady=(8, 0))

        self.pwd_entry.bind("<Return>", lambda e: self._try_unlock())

    def _try_unlock(self):
        pwd = self.pwd_entry.get()
        if not pwd:
            self.err_lbl.config(text="Vui lòng nhập mật khẩu!")
            return

        if self.unlock_validator(pwd):
            self.unlock()
        else:
            self.err_lbl.config(text="Mật khẩu không chính xác!")
            self.pwd_entry.delete(0, tk.END)

    def unlock(self):
        self.is_locked = False
        if self.overlay and self.overlay.winfo_exists():
            self.overlay.destroy()
            self.overlay = None

