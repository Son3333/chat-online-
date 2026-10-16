"""
Module Quick Switcher / Command Palette (Ctrl + K)
- Bấm Ctrl + K để mở nhanh hộp thoại tìm kiếm và chuyển đổi cuộc hội thoại.
- Tìm kiếm nhanh người dùng, nhóm trò chuyện và thực thi các hành động nhanh (Chụp màn hình, Khóa máy, Cloud của tôi...).
"""

import tkinter as tk
from typing import List, Dict, Callable, Optional

class QuickSwitcher:
    def __init__(self, parent: tk.Tk,
                 conversations_provider: Callable[[], List[Dict]],
                 on_select_conversation: Callable[[int], None],
                 action_handlers: Optional[Dict[str, Callable]] = None):
        self.parent = parent
        self.conversations_provider = conversations_provider
        self.on_select_conversation = on_select_conversation
        self.action_handlers = action_handlers or {}
        self.win = None
        self.selected_index = 0
        self.filtered_items = []

    def show(self):
        if self.win and self.win.winfo_exists():
            self.win.lift()
            return

        self.win = tk.Toplevel(self.parent)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg="#0F172A")

        # Căn giữa phía trên màn hình
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        w = 540
        h = 380
        x = (sw - w) // 2
        y = (sh - h) // 4
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        # Khung viền
        border = tk.Frame(self.win, bg="#0F172A", highlightthickness=2, highlightbackground="#38BDF8")
        border.pack(fill=tk.BOTH, expand=True)

        # Ô tìm kiếm
        search_frame = tk.Frame(border, bg="#1E293B", padx=14, pady=10)
        search_frame.pack(fill=tk.X)

        icon_lbl = tk.Label(search_frame, text="🔍", font=("Segoe UI", 12), fg="#94A3B8", bg="#1E293B")
        icon_lbl.pack(side=tk.LEFT, padx=(0, 8))

        self.entry_var = tk.StringVar()
        self.entry_var.trace_add("write", self._on_search_change)
        self.entry = tk.Entry(search_frame, textvariable=self.entry_var, font=("Segoe UI", 12),
                              bg="#1E293B", fg="white", insertbackground="white", bd=0, relief=tk.FLAT)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        esc_hint = tk.Label(search_frame, text="ESC để đóng", font=("Segoe UI", 8), fg="#64748B", bg="#1E293B")
        esc_hint.pack(side=tk.RIGHT)

        # Danh sách kết quả
        self.list_frame = tk.Frame(border, bg="#0F172A", pady=6)
        self.list_frame.pack(fill=tk.BOTH, expand=True)

        # Binds
        self.win.bind("<Escape>", lambda e: self.close())
        self.entry.bind("<Down>", self._on_arrow_down)
        self.entry.bind("<Up>", self._on_arrow_up)
        self.entry.bind("<Return>", self._on_enter)
        self.win.bind("<FocusOut>", self._on_focus_out)

        self.entry.focus_set()
        self._refresh_list()

    def _on_focus_out(self, event):
        # Đóng khi click ra ngoài
        self.parent.after(100, self._check_focus)

    def _check_focus(self):
        try:
            if self.win and self.win.winfo_exists():
                focused = self.win.focus_get()
                if focused is None or str(focused).split(".")[1] != str(self.win).split(".")[1]:
                    self.close()
        except Exception:
            pass

    def _refresh_list(self):
        query = self.entry_var.get().strip().lower()
        self.filtered_items.clear()

        # 1. Thêm các hành động hệ thống
        quick_actions = [
            {"type": "action", "key": "screenshot", "title": "📷 Chụp màn hình (Ctrl+Alt+A)", "sub": "Công cụ chụp và vẽ chú thích"},
            {"type": "action", "key": "saved", "title": "☁️ Cloud của tôi (Saved Messages)", "sub": "Lưu trữ tin nhắn & tệp cá nhân"},
            {"type": "action", "key": "lock", "title": "🔒 Khóa màn hình (Ctrl+L)", "sub": "Bảo vệ riêng tư nhanh"},
            {"type": "action", "key": "topmost", "title": "📌 Ghim cửa sổ nổi trên cùng", "sub": "Bật/Tắt Always-on-Top"}
        ]
        for act in quick_actions:
            if not query or query in act["title"].lower() or query in act["sub"].lower():
                self.filtered_items.append(act)

        # 2. Thêm các cuộc trò chuyện
        convs = self.conversations_provider() or []
        for c in convs:
            title = c.get("title", "")
            if not query or query in title.lower():
                self.filtered_items.append({"type": "conv", "data": c, "title": title, "sub": "Cuộc trò chuyện"})

        self.selected_index = 0
        self._render_items()

    def _on_search_change(self, *args):
        self._refresh_list()

    def _render_items(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        display_items = self.filtered_items[:7] # Hiển thị tối đa 7 mục
        if not display_items:
            empty_lbl = tk.Label(self.list_frame, text="Không tìm thấy kết quả phù hợp",
                                 font=("Segoe UI", 10), fg="#64748B", bg="#0F172A", pady=20)
            empty_lbl.pack()
            return

        for idx, item in enumerate(display_items):
            is_selected = (idx == self.selected_index)
            bg_col = "#1E293B" if is_selected else "#0F172A"
            fg_col = "#38BDF8" if is_selected else "#F8FAFC"

            row = tk.Frame(self.list_frame, bg=bg_col, padx=14, pady=6, cursor="hand2")
            row.pack(fill=tk.X)

            t_lbl = tk.Label(row, text=item["title"], font=("Segoe UI", 10, "bold" if is_selected else "normal"),
                             fg=fg_col, bg=bg_col, anchor="w")
            t_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            s_lbl = tk.Label(row, text=item["sub"], font=("Segoe UI", 8), fg="#64748B", bg=bg_col)
            s_lbl.pack(side=tk.RIGHT)

            def _click(e=None, i=idx):
                self.selected_index = i
                self._execute_selected()

            row.bind("<Button-1>", _click)
            t_lbl.bind("<Button-1>", _click)
            s_lbl.bind("<Button-1>", _click)

    def _on_arrow_down(self, event):
        count = min(7, len(self.filtered_items))
        if count > 0:
            self.selected_index = (self.selected_index + 1) % count
            self._render_items()
        return "break"

    def _on_arrow_up(self, event):
        count = min(7, len(self.filtered_items))
        if count > 0:
            self.selected_index = (self.selected_index - 1 + count) % count
            self._render_items()
        return "break"

    def _on_enter(self, event):
        self._execute_selected()
        return "break"

    def _execute_selected(self):
        display_items = self.filtered_items[:7]
        if 0 <= self.selected_index < len(display_items):
            item = display_items[self.selected_index]
            self.close()
            if item["type"] == "conv":
                self.on_select_conversation(item["data"]["id"])
            elif item["type"] == "action":
                key = item["key"]
                if key in self.action_handlers:
                    self.action_handlers[key]()

    def close(self):
        try:
            if self.win and self.win.winfo_exists():
                self.win.destroy()
        except Exception:
            pass

