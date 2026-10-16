"""
Module Cửa Sổ Chat Độc Lập (Pop-out Chat Window)
- Tách một cuộc trò chuyện ra một cửa sổ riêng biệt để làm việc đa nhiệm.
- Đầy đủ tính năng: Nhắn tin thời gian thực, Reply/Quote, Reaction, Pin, Đính kèm file/ảnh, Always on Top.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import os
from typing import Optional

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

