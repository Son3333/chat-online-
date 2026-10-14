import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import time
from typing import Optional

from src.client.ui.chat_bubble import ChatBubble
from src.client.ui.create_group_dialog import CreateGroupDialog

class MainWindow(ctk.CTkFrame):
    def __init__(self, master, current_user: dict, network_client, on_logout):
        super().__init__(master, fg_color="transparent")
        self.current_user = current_user
        self.net = network_client
        self.on_logout = on_logout
        
        self.conversations = []
        self.active_conv_id: Optional[int] = None
        self.active_conv_data: Optional[dict] = None
        self.conv_widgets = {}
        self.last_typing_time = 0
        
        # Grid layout
        self.grid_columnconfigure(0, weight=0, minsize=320) # Sidebar
        self.grid_columnconfigure(1, weight=1)              # Chat Area
        self.grid_rowconfigure(0, weight=0)                 # Top Bar
        self.grid_rowconfigure(1, weight=1)                 # Main Content
        
        # 1. Đăng ký nhận sự kiện thời gian thực từ NetworkClient
        self.net.register_callback("new_message", self._on_new_message_received)
        self.net.register_callback("user_status_changed", self._on_user_status_changed)
        self.net.register_callback("user_typing", self._on_user_typing)
        self.net.register_callback("refresh_conversations", lambda pkt: self.master.after(0, self.load_conversations))

        self._build_top_bar()
        self._build_sidebar()
        self._build_chat_area()
        
        # Load danh sách cuộc hội thoại ban đầu
        self.load_conversations()

    # --- TOP BAR ---
    def _build_top_bar(self):
        self.top_bar = ctk.CTkFrame(self, height=55, corner_radius=0, fg_color=("white", "#1E293B"))
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        # User profile badge
        user_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        user_frame.pack(side="left", padx=16, pady=8)
        
        avatar_col = self.current_user.get("avatar_color", "#2563EB")
        self.avatar_circle = ctk.CTkButton(
            user_frame, 
            text=self.current_user["full_name"][:1].upper(),
            width=36, 
            height=36, 
            corner_radius=18,
            fg_color=avatar_col,
            text_color="white",
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled"
        )
        self.avatar_circle.pack(side="left", padx=(0, 10))
        
        name_box = ctk.CTkFrame(user_frame, fg_color="transparent")
        name_box.pack(side="left")
        
        ctk.CTkLabel(
            name_box, 
            text=self.current_user["full_name"], 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        
        status_box = ctk.CTkFrame(name_box, fg_color="transparent")
        status_box.pack(anchor="w")
        ctk.CTkLabel(status_box, text=f"🟢 Trực tuyến  •  @{self.current_user['username']}  •  ID: #{self.current_user['id']}", font=ctk.CTkFont(size=11), text_color="#10B981").pack(side="left")

        # Right actions
        actions_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        actions_frame.pack(side="right", padx=16, pady=8)
        
        # Nút hiển thị & sao chép địa chỉ Máy chủ Online
        server_info_text = f"🌐 {self.net.host}:{self.net.port}"
        self.btn_copy_server = ctk.CTkButton(
            actions_frame, 
            text=f"{server_info_text} 📋", 
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("gray90", "#0F172A"),
            hover_color=("gray80", "#1E293B"),
            text_color=("#0284C7", "#38BDF8"),
            command=self.copy_server_info
        )
        self.btn_copy_server.pack(side="left", padx=8)

        # Nút chuyển chế độ Sáng / Tối
        self.theme_switch = ctk.CTkSwitch(
            actions_frame, 
            text="Giao diện Tối", 
            command=self.toggle_theme,
            font=ctk.CTkFont(size=12)
        )
        if ctk.get_appearance_mode() == "Dark":
            self.theme_switch.select()
        self.theme_switch.pack(side="left", padx=12)
        
        # Nút Làm mới
        ctk.CTkButton(
            actions_frame, 
            text="🔄 Làm mới", 
            width=80, 
            height=32, 
            font=ctk.CTkFont(size=12),
            fg_color=("gray80", "#334155"),
            text_color=("black", "white"),
            command=self.load_conversations
        ).pack(side="left", padx=6)

        # Nút Đăng xuất
        ctk.CTkButton(
            actions_frame, 
            text="🚪 Đăng xuất", 
            width=90, 
            height=32, 
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#EF4444",
            hover_color="#DC2626",
            command=self.on_logout
        ).pack(side="left", padx=6)

    def copy_server_info(self):
        info = f"{self.net.host}:{self.net.port}"
        try:
            self.master.clipboard_clear()
            self.master.clipboard_append(info)
            self.btn_copy_server.configure(text="Đã sao chép! ✓")
            self.master.after(2000, lambda: self.btn_copy_server.configure(text=f"🌐 {self.net.host}:{self.net.port} 📋"))
        except Exception:
            pass

    def toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("Dark")
            self.theme_switch.configure(text="Giao diện Tối")
        else:
            ctk.set_appearance_mode("Light")
            self.theme_switch.configure(text="Giao diện Sáng")

    # --- SIDEBAR ---
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=0, fg_color=("gray95", "#0F172A"))
        self.sidebar.grid(row=1, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(2, weight=1)

        # Search bar
        search_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        
        self.search_entry = ctk.CTkEntry(
            search_frame, 
            placeholder_text="🔍 Nhập Username hoặc ID (vd: #1)...", 
            height=36, 
            corner_radius=8
        )
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        # Search results popup list container (ẩn khi không search)
        self.search_results_frame = ctk.CTkScrollableFrame(self.sidebar, height=140, fg_color=("white", "#1E293B"))
        # (Sẽ pack khi có kết quả tìm kiếm)

        # Action bar: Tạo nhóm mới
        btn_action_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        btn_action_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(4, 8))
        
        self.btn_create_group = ctk.CTkButton(
            btn_action_frame, 
            text="➕ Tạo Nhóm Chat Mới", 
            height=34, 
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=self.open_create_group_dialog
        )
        self.btn_create_group.pack(fill="x")

        # Danh sách cuộc trò chuyện
        self.conv_scroll = ctk.CTkScrollableFrame(self.sidebar, corner_radius=0, fg_color="transparent")
        self.conv_scroll.grid(row=2, column=0, sticky="nsew", padx=6, pady=(0, 6))
        self.conv_scroll.grid_columnconfigure(0, weight=1)

    # --- CHAT AREA ---
    def _build_chat_area(self):
        self.chat_container = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray90", "#0B1120"))
        self.chat_container.grid(row=1, column=1, sticky="nsew")
        self.chat_container.grid_columnconfigure(0, weight=1)
        self.chat_container.grid_rowconfigure(1, weight=1)

        # Empty state (khi chưa chọn cuộc hội thoại)
        self.empty_state = ctk.CTkFrame(self.chat_container, fg_color="transparent")
        self.empty_state.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(self.empty_state, text="💬", font=ctk.CTkFont(size=64)).pack(pady=(0, 10))
        ctk.CTkLabel(
            self.empty_state, 
            text="Chào mừng đến với Ứng dụng Nhắn tin!", 
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            self.empty_state, 
            text="Hãy chọn một cuộc trò chuyện ở danh sách bên trái hoặc tạo nhóm mới để bắt đầu.", 
            font=ctk.CTkFont(size=13),
            text_color="gray60"
        ).pack()

        # Chat Active Views (sẽ hiển thị khi chọn hội thoại)
        self.chat_active_frame = ctk.CTkFrame(self.chat_container, fg_color="transparent")
        self.chat_active_frame.grid_columnconfigure(0, weight=1)
        self.chat_active_frame.grid_rowconfigure(1, weight=1)

        # 1. Chat Header
        self.chat_header = ctk.CTkFrame(self.chat_active_frame, height=55, corner_radius=0, fg_color=("white", "#1E293B"))
        self.chat_header.grid(row=0, column=0, sticky="ew")
        
        header_info = ctk.CTkFrame(self.chat_header, fg_color="transparent")
        header_info.pack(side="left", padx=16, pady=8)
        
        self.lbl_chat_title = ctk.CTkLabel(header_info, text="Tiêu đề cuộc trò chuyện", font=ctk.CTkFont(size=15, weight="bold"))
        self.lbl_chat_title.pack(anchor="w")
        
        self.lbl_chat_subtitle = ctk.CTkLabel(header_info, text="Trạng thái...", font=ctk.CTkFont(size=11), text_color="gray60")
        self.lbl_chat_subtitle.pack(anchor="w")

        # Typing notification label
        self.lbl_typing = ctk.CTkLabel(
            self.chat_header, 
            text="", 
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="#38BDF8"
        )
        self.lbl_typing.pack(side="right", padx=20)

        # 2. Scrollable Messages View
        self.messages_scroll = ctk.CTkScrollableFrame(self.chat_active_frame, fg_color="transparent")
        self.messages_scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)
        self.messages_scroll.grid_columnconfigure(0, weight=1)

        # 3. Bottom Input Bar
        self.input_bar = ctk.CTkFrame(self.chat_active_frame, height=65, corner_radius=0, fg_color=("white", "#1E293B"))
        self.input_bar.grid(row=2, column=0, sticky="ew")
        
        # Emoji bar buttons
        self.emoji_bar = ctk.CTkFrame(self.input_bar, fg_color="transparent")
        self.emoji_bar.pack(fill="x", padx=14, pady=(6, 2))
        
        emojis = ["😊", "👍", "❤️", "🎉", "🔥", "😂", "👏", "🚀", "💯", "🤝"]
        for em in emojis:
            b = ctk.CTkButton(
                self.emoji_bar, 
                text=em, 
                width=28, 
                height=24, 
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                hover_color=("gray85", "#334155"),
                command=lambda e=em: self.insert_emoji(e)
            )
            b.pack(side="left", padx=2)

        # Input row
        input_row = ctk.CTkFrame(self.input_bar, fg_color="transparent")
        input_row.pack(fill="x", padx=14, pady=(0, 8))

        # Nút Đính kèm tệp / ảnh
        self.btn_attach = ctk.CTkButton(
            input_row, 
            text="📎 Đính Kèm", 
            width=90, 
            height=38, 
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("gray80", "#334155"),
            hover_color=("gray70", "#475569"),
            text_color=("black", "white"),
            command=self.pick_and_send_file
        )
        self.btn_attach.pack(side="left", padx=(0, 8))

        # Entry soạn tin nhắn
        self.msg_entry = ctk.CTkEntry(
            input_row, 
            placeholder_text="Nhập tin nhắn... (Nhấn Enter để gửi)", 
            height=38, 
            corner_radius=8
        )
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.msg_entry.bind("<Return>", lambda e: self.send_text_message())
        self.msg_entry.bind("<Key>", self._on_key_typing)

        # Nút Gửi
        self.btn_send = ctk.CTkButton(
            input_row, 
            text="Gửi ➤", 
            width=80, 
            height=38, 
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.send_text_message
        )
        self.btn_send.pack(side="right")

    def insert_emoji(self, emoji_char: str):
        self.msg_entry.insert("insert", emoji_char)
        self.msg_entry.focus_set()

    def _on_key_typing(self, event):
        now = time.time()
        if now - self.last_typing_time > 2.5 and self.active_conv_id:
            self.last_typing_time = now
            self.net.send_typing(self.active_conv_id, self.current_user["id"], self.current_user["full_name"])

    # --- LOGIC CUỘC TRÒ CHUYỆN ---
    def load_conversations(self):
        def _fetch():
            res = self.net.get_conversations(self.current_user["id"])
            if res and "conversations" in res:
                self.conversations = res["conversations"]
                self.master.after(0, self._render_conversation_list)
        threading.Thread(target=_fetch, daemon=True).start()

    def _render_conversation_list(self):
        # Xóa các widget cũ
        for widget in self.conv_scroll.winfo_children():
            widget.destroy()
        self.conv_widgets.clear()

        if not self.conversations:
            ctk.CTkLabel(self.conv_scroll, text="Chưa có cuộc trò chuyện nào.\nHãy tìm bạn bè để bắt đầu!", font=ctk.CTkFont(size=12), text_color="gray60").pack(pady=30)
            return

        for conv in self.conversations:
            conv_id = conv["id"]
            is_active = (conv_id == self.active_conv_id)
            
            # Card hội thoại
            bg_col = ("#DBEAFE", "#1E3A8A") if is_active else ("white", "#1E293B")
            card = ctk.CTkFrame(self.conv_scroll, corner_radius=10, fg_color=bg_col, cursor="hand2")
            card.pack(fill="x", pady=3)
            self.conv_widgets[conv_id] = card
            
            # Click event
            card.bind("<Button-1>", lambda e, c=conv: self.select_conversation(c))

            row_f = ctk.CTkFrame(card, fg_color="transparent")
            row_f.pack(fill="x", padx=10, pady=8)
            row_f.bind("<Button-1>", lambda e, c=conv: self.select_conversation(c))

            # Avatar
            if conv["type"] == "group":
                av_text = "👥"
                av_col = "#0284C7"
            else:
                av_text = conv["title"][:1].upper()
                av_col = conv.get("avatar_color", "#2563EB")
            
            av_btn = ctk.CTkButton(
                row_f, 
                text=av_text, 
                width=38, 
                height=38, 
                corner_radius=19,
                fg_color=av_col,
                font=ctk.CTkFont(size=14, weight="bold"),
                state="disabled"
            )
            av_btn.pack(side="left", padx=(0, 10))

            # Info text
            text_box = ctk.CTkFrame(row_f, fg_color="transparent")
            text_box.pack(side="left", fill="x", expand=True)
            text_box.bind("<Button-1>", lambda e, c=conv: self.select_conversation(c))

            title_row = ctk.CTkFrame(text_box, fg_color="transparent")
            title_row.pack(fill="x")
            title_row.bind("<Button-1>", lambda e, c=conv: self.select_conversation(c))

            # Tên hội thoại
            lbl_title = ctk.CTkLabel(
                title_row, 
                text=conv["title"], 
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w"
            )
            lbl_title.pack(side="left")
            lbl_title.bind("<Button-1>", lambda e, c=conv: self.select_conversation(c))

            # Chấm online nếu là 1-1
            if conv["type"] == "direct" and conv.get("is_online"):
                dot = ctk.CTkLabel(title_row, text=" 🟢", font=ctk.CTkFont(size=9))
                dot.pack(side="left")
                dot.bind("<Button-1>", lambda e, c=conv: self.select_conversation(c))

            # Tin nhắn cuối cùng
            last_msg = conv.get("last_message")
            if last_msg:
                snippet = f"{last_msg.get('sender_name', '')}: {last_msg.get('content', '')}"
                if len(snippet) > 28:
                    snippet = snippet[:28] + "..."
            else:
                snippet = "Chưa có tin nhắn..."
            
            lbl_snip = ctk.CTkLabel(
                text_box, 
                text=snippet, 
                font=ctk.CTkFont(size=11), 
                text_color=("gray50", "gray40"),
                anchor="w"
            )
            lbl_snip.pack(fill="x", pady=(2, 0))
            lbl_snip.bind("<Button-1>", lambda e, c=conv: self.select_conversation(c))

    def select_conversation(self, conv: dict):
        self.active_conv_id = conv["id"]
        self.active_conv_data = conv
        
        # Ẩn empty state, hiện chat active frame
        self.empty_state.place_forget()
        self.chat_active_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")

        # Cập nhật Header
        self.lbl_chat_title.configure(text=conv["title"])
        if conv["type"] == "group":
            count = conv.get("member_count", 2)
            self.lbl_chat_subtitle.configure(text=f"👥 Nhóm trò chuyện  •  {count} thành viên")
        else:
            is_on = conv.get("is_online", 0)
            status_text = "🟢 Trực tuyến" if is_on else "⚪ Ngoại tuyến"
            self.lbl_chat_subtitle.configure(text=status_text)

        # Highlight lại list
        self._render_conversation_list()

        # Tải tin nhắn
        self.load_messages_for_active_conv()
        self.msg_entry.focus_set()

    def load_messages_for_active_conv(self):
        if not self.active_conv_id:
            return
        
        conv_id = self.active_conv_id
        def _fetch():
            res = self.net.get_messages(conv_id)
            if res and res.get("conversation_id") == conv_id:
                msgs = res.get("messages", [])
                self.master.after(0, lambda: self._render_messages(msgs))
        threading.Thread(target=_fetch, daemon=True).start()

    def _render_messages(self, messages: list):
        for w in self.messages_scroll.winfo_children():
            w.destroy()
            
        for msg in messages:
            bubble = ChatBubble(self.messages_scroll, msg, self.current_user["id"], self.net)
            bubble.pack(fill="x")
        
        self.master.after(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        try:
            self.messages_scroll._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    # --- GỬI TIN NHẮN & TỆP TIN ---
    def send_text_message(self):
        if not self.active_conv_id:
            return
        content = self.msg_entry.get().strip()
        if not content:
            return
        
        self.msg_entry.delete(0, "end")
        self.net.send_message(self.active_conv_id, self.current_user["id"], content, msg_type="text")

    def pick_and_send_file(self):
        if not self.active_conv_id:
            messagebox.showwarning("Thông báo", "Vui lòng chọn một cuộc trò chuyện trước!")
            return
        
        filepath = filedialog.askopenfilename(
            title="Chọn tệp tin hoặc hình ảnh để gửi",
            filetypes=[
                ("Tất cả tệp hợp lệ", "*.png;*.jpg;*.jpeg;*.gif;*.pdf;*.docx;*.xlsx;*.zip;*.txt"),
                ("Hình ảnh", "*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp"),
                ("Tài liệu & Tệp nén", "*.pdf;*.docx;*.xlsx;*.pptx;*.zip;*.rar;*.txt"),
                ("Tất cả", "*.*")
            ]
        )
        if not filepath:
            return
        
        # Báo gửi tệp
        self.btn_attach.configure(state="disabled", text="Đang gửi...")
        self.update_idletasks()
        
        def _upload():
            res = self.net.upload_file(self.active_conv_id, self.current_user["id"], filepath)
            def _done():
                self.btn_attach.configure(state="normal", text="📎 Đính Kèm")
                if not res or not res.get("success"):
                    messagebox.showerror("Lỗi gửi tệp", res.get("message", "Gửi tệp thất bại!"))
            self.master.after(0, _done)
            
        threading.Thread(target=_upload, daemon=True).start()

    # --- XỬ LÝ SỰ KIỆN TỪ SERVER ---
    def _on_new_message_received(self, packet: dict):
        conv_id = packet.get("conversation_id")
        msg = packet.get("message")
        
        # Nếu đang mở cuộc hội thoại này -> render thêm bong bóng chat
        if self.active_conv_id == conv_id:
            def _add():
                bubble = ChatBubble(self.messages_scroll, msg, self.current_user["id"], self.net)
                bubble.pack(fill="x")
                self._scroll_to_bottom()
            self.master.after(0, _add)
        
        # Tải lại danh sách bên trái để cập nhật snippet và vị trí
        self.master.after(0, self.load_conversations)

    def _on_user_status_changed(self, packet: dict):
        # Có người dùng online hoặc offline -> cập nhật danh sách
        self.master.after(0, self.load_conversations)
        
        # Cập nhật subtitle nếu đang chat với người này
        if self.active_conv_data and self.active_conv_data.get("type") == "direct":
            if self.active_conv_data.get("partner_id") == packet.get("user_id"):
                status_text = "🟢 Trực tuyến" if packet.get("is_online") else "⚪ Ngoại tuyến"
                self.master.after(0, lambda: self.lbl_chat_subtitle.configure(text=status_text))

    def _on_user_typing(self, packet: dict):
        if self.active_conv_id == packet.get("conversation_id"):
            name = packet.get("sender_name", "")
            def _show():
                self.lbl_typing.configure(text=f"💬 {name} đang soạn tin...")
                # Xóa sau 3 giây
                self.master.after(3000, lambda: self.lbl_typing.configure(text=""))
            self.master.after(0, _show)

    # --- TÌM KIẾM NGƯỜI DÙNG & TẠO CHAT 1-1 ---
    def _on_search_key(self, event):
        kw = self.search_entry.get().strip()
        if not kw:
            self.search_results_frame.grid_forget()
            return
            
        def _search():
            res = self.net.search_users(kw, self.current_user["id"])
            users = res.get("users", []) if res else []
            self.master.after(0, lambda: self._show_search_results(users))
        threading.Thread(target=_search, daemon=True).start()

    def _show_search_results(self, users: list):
        for w in self.search_results_frame.winfo_children():
            w.destroy()
            
        self.search_results_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 4))
        
        if not users:
            ctk.CTkLabel(self.search_results_frame, text="Không tìm thấy người dùng.", font=ctk.CTkFont(size=11), text_color="gray60").pack(pady=8)
            return

        for u in users:
            row = ctk.CTkFrame(self.search_results_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=f"{u['full_name']} (@{u['username']} • ID: #{u['id']})", font=ctk.CTkFont(size=12)).pack(side="left", padx=4)
            
            ctk.CTkButton(
                row, 
                text="Nhắn tin", 
                width=65, 
                height=24, 
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#10B981",
                hover_color="#059669",
                command=lambda uid=u["id"]: self.start_direct_chat_with(uid)
            ).pack(side="right", padx=4)

    def start_direct_chat_with(self, partner_id: int):
        self.search_entry.delete(0, "end")
        self.search_results_frame.grid_forget()
        
        def _call():
            res = self.net.start_direct_chat(self.current_user["id"], partner_id)
            if res and "conversation_id" in res:
                conv_id = res["conversation_id"]
                self.conversations = res.get("conversations", [])
                
                # Tìm conv vừa tạo/lấy
                target_conv = next((c for c in self.conversations if c["id"] == conv_id), None)
                if target_conv:
                    self.master.after(0, lambda: self.select_conversation(target_conv))
                else:
                    self.master.after(0, self.load_conversations)
        threading.Thread(target=_call, daemon=True).start()

    def open_create_group_dialog(self):
        CreateGroupDialog(self.master, self.current_user, self.net, on_group_created=self._on_group_created)

    def _on_group_created(self, conv_id):
        self.load_conversations()

