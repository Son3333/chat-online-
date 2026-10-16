"""
Module Cửa Sổ Chat Độc Lập (Pop-out Chat Window)
- Tách một cuộc trò chuyện ra một cửa sổ riêng biệt để làm việc đa nhiệm.
- Đầy đủ tính năng: Nhắn tin thời gian thực, Reply/Quote, Reaction, Pin, Đính kèm file/ảnh, Always on Top.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading

from src.client.ui.chat_bubble import ChatBubble

class PopoutChatWindow(ctk.CTkToplevel):
    def __init__(self, master, current_user: dict, network_client, conversation_id: int, conv_data: dict):
        super().__init__(master)
        self.current_user = current_user
        self.net = network_client
        self.conv_id = conversation_id
        self.conv_data = conv_data or {}

        title = self.conv_data.get("title", f"Hội thoại #{self.conv_id}")
        self.title(f"💬 {title} - Cửa sổ riêng")
        self.geometry("620x680")
        self.minsize(450, 480)

        self.rendered_msg_ids = set()
        self.msg_bubbles = {}
        self.reply_target_message = None
        self.is_topmost = False

        self._build_ui()
        self._load_messages()

        # Đăng ký nhận tin nhắn mới cho riêng cửa sổ này
        self.net.register_callback(f"popout_msg_{self.conv_id}", self._on_new_message)

    def _build_ui(self):
        # 1. Header
        header = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=("white", "#1E293B"))
        header.pack(fill="x")

        title = self.conv_data.get("title", f"Hội thoại #{self.conv_id}")
        lbl_title = ctk.CTkLabel(header, text=title, font=ctk.CTkFont(size=14, weight="bold"))
        lbl_title.pack(side="left", padx=14, pady=10)

        # Nút Ghim Always on Top
        self.btn_pin = ctk.CTkButton(
            header, text="📌 Ghim nổi", width=80, height=28,
            font=ctk.CTkFont(size=11),
            fg_color=("#F1F5F9", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            command=self._toggle_topmost
        )
        self.btn_pin.pack(side="right", padx=10, pady=10)

        # 2. Vùng cuộn tin nhắn
        self.messages_scroll = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color=("gray95", "#0B1120"))
        self.messages_scroll.pack(fill="both", expand=True)

        # 3. Thanh Reply Bar
        self.reply_bar = ctk.CTkFrame(self, height=36, corner_radius=0, fg_color=("#E0E7FF", "#1E293B"))
        self.lbl_reply_info = ctk.CTkLabel(self.reply_bar, text="", font=ctk.CTkFont(size=11))
        self.lbl_reply_info.pack(side="left", padx=10)
        btn_cancel_reply = ctk.CTkButton(self.reply_bar, text="✕", width=24, height=24,
                                         fg_color="transparent", text_color="#EF4444",
                                         command=self._cancel_reply)
        btn_cancel_reply.pack(side="right", padx=8)

        # 4. Thanh nhập liệu ở đáy
        input_bar = ctk.CTkFrame(self, height=55, corner_radius=0, fg_color=("white", "#1E293B"))
        input_bar.pack(fill="x")

        btn_file = ctk.CTkButton(input_bar, text="📎", width=36, height=36, font=ctk.CTkFont(size=16),
                                 fg_color="transparent", hover_color=("gray85", "#334155"), command=self._send_file)
        btn_file.pack(side="left", padx=(10, 4), pady=8)

        self.entry = ctk.CTkEntry(input_bar, placeholder_text="Nhập tin nhắn...", font=ctk.CTkFont(size=13), height=38)
        self.entry.pack(side="left", fill="x", expand=True, padx=4, pady=8)
        self.entry.bind("<Return>", lambda e: self._send_text())

        btn_send = ctk.CTkButton(input_bar, text="Gửi", width=60, height=38, font=ctk.CTkFont(size=13, weight="bold"),
                                 fg_color="#2563EB", hover_color="#1D4ED8", command=self._send_text)
        btn_send.pack(side="right", padx=(4, 10), pady=8)

    def _toggle_topmost(self):
        self.is_topmost = not self.is_topmost
        self.attributes("-topmost", self.is_topmost)
        if self.is_topmost:
            self.btn_pin.configure(text="📌 Đã ghim", fg_color="#3B82F6", text_color="white")
        else:
            self.btn_pin.configure(text="📌 Ghim nổi", fg_color=("#F1F5F9", "#334155"), text_color=("#0F172A", "#F8FAFC"))

    def _load_messages(self):
        def _fetch():
            res = self.net.get_messages(self.conv_id)
            if res and "messages" in res:
                msgs = res["messages"]
                self.after(0, lambda: self._render_messages(msgs))
        threading.Thread(target=_fetch, daemon=True).start()

    def _render_messages(self, messages):
        for widget in self.messages_scroll.winfo_children():
            widget.destroy()
        self.rendered_msg_ids.clear()
        self.msg_bubbles.clear()

        for m in messages:
            msg_id = m.get("id")
            if msg_id:
                self.rendered_msg_ids.add(msg_id)
            bubble = ChatBubble(
                self.messages_scroll,
                m,
                self.current_user["id"],
                self.net,
                on_recall_callback=self._recall_msg,
                on_reply_callback=self._set_reply,
                on_reaction_callback=self._react_msg,
                on_pin_callback=None
            )
            bubble.pack(fill="x")
            if msg_id:
                self.msg_bubbles[msg_id] = bubble
        self._scroll_bottom()

    def _send_text(self):
        txt = self.entry.get().strip()
        if not txt:
            return
        self.entry.delete(0, tk.END)

        reply_id = self.reply_target_message.get("id") if self.reply_target_message else None
        self._cancel_reply()

        def _do():
            self.net.send_message(self.conv_id, self.current_user["id"], txt, reply_to_id=reply_id)
            self._load_messages()
        threading.Thread(target=_do, daemon=True).start()

    def _send_file(self):
        path = filedialog.askopenfilename(title="Chọn tệp tin gửi")
        if not path:
            return
        def _do():
            self.net.send_file(self.conv_id, self.current_user["id"], path)
            self._load_messages()
        threading.Thread(target=_do, daemon=True).start()

    def _set_reply(self, target_msg):
        self.reply_target_message = target_msg
        sender = target_msg.get("sender_name", "tin nhắn")
        preview = target_msg.get("content", "")[:35]
        self.lbl_reply_info.configure(text=f"↩️ Đang trả lời {sender}: '{preview}...'")
        self.reply_bar.pack(fill="x", before=self.entry.master)
        self.entry.focus_set()

    def _cancel_reply(self):
        self.reply_target_message = None
        self.reply_bar.pack_forget()

    def _recall_msg(self, msg_id):
        def _do():
            res = self.net.recall_message(msg_id, self.current_user["id"])
            if res and res.get("success"):
                self.after(0, self._load_messages)
        threading.Thread(target=_do, daemon=True).start()

    def _react_msg(self, msg_id, reaction):
        def _do():
            res = self.net.toggle_reaction(self.conv_id, msg_id, self.current_user["id"], reaction)
            if res and res.get("success"):
                self.after(0, self._load_messages)
        threading.Thread(target=_do, daemon=True).start()

    def _on_new_message(self, packet):
        self.after(0, self._load_messages)

    def _scroll_bottom(self):
        try:
            self.messages_scroll._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass


class PopoutInfoWindow(ctk.CTkToplevel):
    """Cửa sổ thông tin cuộc hội thoại độc lập (Pop-out Info Window)."""
    def __init__(self, master, current_user: dict, network_client, conversation_id: int, conv_data: dict, pinned_message=None, subtitle=""):
        super().__init__(master)
        self.current_user = current_user
        self.net = network_client
        self.conv_id = conversation_id
        self.conv_data = conv_data or {}
        self.pinned_message = pinned_message
        self.subtitle = subtitle
        self.is_topmost = False

        title = self.conv_data.get("title", f"Hội thoại #{self.conv_id}")
        self.title(f"ℹ️ Thông tin - {title}")
        self.geometry("380x640")
        self.minsize(340, 480)

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # 1. Header Bar
        header = ctk.CTkFrame(self, height=45, corner_radius=0, fg_color=("white", "#1E293B"))
        header.pack(fill="x")

        lbl_hdr = ctk.CTkLabel(header, text="Thông tin hội thoại", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_hdr.pack(side="left", padx=12, pady=10)

        self.btn_pin = ctk.CTkButton(
            header, text="📌 Ghim", width=70, height=28,
            font=ctk.CTkFont(size=11),
            fg_color=("#F1F5F9", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            command=self._toggle_topmost
        )
        self.btn_pin.pack(side="right", padx=10, pady=8)

        # 2. Main Scrollable Container
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=8)

        conv = self.conv_data
        title = conv.get("title", "Hội thoại")
        avatar_col = conv.get("avatar_color", "#2563EB")

        # Avatar circle
        av_btn = ctk.CTkButton(
            scroll,
            text=title[:1].upper(),
            width=76, height=76,
            corner_radius=38,
            fg_color=avatar_col,
            text_color="white",
            font=ctk.CTkFont(size=28, weight="bold"),
            state="disabled"
        )
        av_btn.pack(pady=(12, 6))

        ctk.CTkLabel(scroll, text=title, font=ctk.CTkFont(size=16, weight="bold")).pack()
        if self.subtitle:
            ctk.CTkLabel(scroll, text=self.subtitle, font=ctk.CTkFont(size=11), text_color="gray60").pack(pady=(2, 10))

        # Tabs for Media, Files & Pinned
        self.tabs = ctk.CTkTabview(scroll, height=380)
        self.tabs.pack(fill="both", expand=True, pady=6)

        self.tab_media = self.tabs.add("🖼️ Ảnh")
        self.tab_files = self.tabs.add("📁 Tệp tin")
        self.tab_pinned = self.tabs.add("📌 Ghim")

    def _toggle_topmost(self):
        self.is_topmost = not self.is_topmost
        self.attributes("-topmost", self.is_topmost)
        if self.is_topmost:
            self.btn_pin.configure(fg_color="#3B82F6", text_color="white", text="📌 Đã ghim")
        else:
            self.btn_pin.configure(fg_color=("#F1F5F9", "#334155"), text_color=("#0F172A", "#F8FAFC"), text="📌 Ghim")

    def _load_data(self):
        def _task():
            res = self.net.get_messages(self.conv_id)
            if not res or "messages" not in res:
                return
            msgs = res["messages"]
            img_msgs = [m for m in msgs if m.get("message_type") == "image"]
            file_msgs = [m for m in msgs if m.get("message_type") == "file"]

            def _render():
                # 1. Render Media
                if img_msgs:
                    m_scroll = ctk.CTkScrollableFrame(self.tab_media, fg_color="transparent")
                    m_scroll.pack(fill="both", expand=True)
                    for im in reversed(img_msgs):
                        orig_name = im.get("original_name", "Ảnh")
                        row = ctk.CTkFrame(m_scroll, fg_color=("#F8FAFC", "#0F172A"), corner_radius=6)
                        row.pack(fill="x", pady=2, padx=2)
                        ctk.CTkLabel(row, text="🖼️", font=ctk.CTkFont(size=14)).pack(side="left", padx=6)
                        ctk.CTkLabel(row, text=orig_name[:20], font=ctk.CTkFont(size=11)).pack(side="left", fill="x", expand=True)
                        ctk.CTkButton(row, text="Tải", width=40, height=24, font=ctk.CTkFont(size=10),
                                      command=lambda fid=im.get("file_id"), fn=orig_name: self._download_file(fid, fn)).pack(side="right", padx=4)
                else:
                    ctk.CTkLabel(self.tab_media, text="Chưa có hình ảnh nào", font=ctk.CTkFont(size=11), text_color="gray60").pack(pady=20)

                # 2. Render Files
                if file_msgs:
                    f_scroll = ctk.CTkScrollableFrame(self.tab_files, fg_color="transparent")
                    f_scroll.pack(fill="both", expand=True)
                    for fm in reversed(file_msgs):
                        orig_name = fm.get("original_name", "Tài liệu")
                        row = ctk.CTkFrame(f_scroll, fg_color=("#F8FAFC", "#0F172A"), corner_radius=6)
                        row.pack(fill="x", pady=2, padx=2)
                        ctk.CTkLabel(row, text="📄", font=ctk.CTkFont(size=14)).pack(side="left", padx=6)
                        ctk.CTkLabel(row, text=orig_name[:18], font=ctk.CTkFont(size=11)).pack(side="left", fill="x", expand=True)
                        ctk.CTkButton(row, text="Tải", width=40, height=24, font=ctk.CTkFont(size=10),
                                      command=lambda fid=fm.get("file_id"), fn=orig_name: self._download_file(fid, fn)).pack(side="right", padx=4)
                else:
                    ctk.CTkLabel(self.tab_files, text="Chưa có tệp tin nào", font=ctk.CTkFont(size=11), text_color="gray60").pack(pady=20)

                # 3. Render Pinned
                if self.pinned_message:
                    pin_box = ctk.CTkFrame(self.tab_pinned, fg_color=("#F0FDF4", "#064E3B"), corner_radius=8)
                    pin_box.pack(fill="x", padx=4, pady=8)
                    ctk.CTkLabel(pin_box, text=f"📌 {self.pinned_message.get('sender_name', 'Người dùng')}:",
                                 font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=8, pady=(6, 2))
                    ctk.CTkLabel(pin_box, text=self.pinned_message.get("content", ""),
                                 font=ctk.CTkFont(size=11), wraplength=260, justify="left").pack(anchor="w", padx=8, pady=(0, 6))
                else:
                    ctk.CTkLabel(self.tab_pinned, text="Chưa có tin nhắn nào được ghim", font=ctk.CTkFont(size=11), text_color="gray60").pack(pady=20)

            self.after(0, _render)
        threading.Thread(target=_task, daemon=True).start()

    def _download_file(self, file_id: int, default_name: str):
        if not file_id:
            return
        save_path = filedialog.asksaveasfilename(initialfile=default_name, title="Lưu tệp tin", defaultextension=".*")
        if not save_path:
            return
        def _dl():
            res = self.net.download_file(file_id)
            if res and res.get("success"):
                import base64
                data = base64.b64decode(res.get("file_data", ""))
                with open(save_path, "wb") as f:
                    f.write(data)
                from tkinter import messagebox
                self.after(0, lambda: messagebox.showinfo("Thành công", f"Đã lưu tệp tại:\n{save_path}"))
            else:
                from tkinter import messagebox
                self.after(0, lambda: messagebox.showerror("Lỗi", "Không thể tải tệp tin!"))
        threading.Thread(target=_dl, daemon=True).start()


