import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import time
import os
import sys
import json
import subprocess
import urllib.request
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
        self.friends = []
        self.pending_requests = []
        self.active_conv_id: Optional[int] = None
        self.active_conv_data: Optional[dict] = None
        self.conv_widgets = {}
        self.friend_widgets = {}
        self.last_typing_time = 0
        self.current_sidebar_tab = "chats"
        self.rendered_msg_ids = set()
        self._update_prompted = False
        self._latest_remote_sha = ""
        
        # Grid layout
        self.grid_columnconfigure(0, weight=0, minsize=320) # Sidebar
        self.grid_columnconfigure(1, weight=1)              # Chat Area
        self.grid_rowconfigure(0, weight=0)                 # Top Bar
        self.grid_rowconfigure(1, weight=1)                 # Main Content
        
        # 1. Đăng ký nhận sự kiện thời gian thực từ NetworkClient
        self.net.register_callback("new_message", self._on_new_message_received)
        self.net.register_callback("user_status_changed", self._on_user_status_changed)
        self.net.register_callback("user_typing", self._on_user_typing)
        self.net.register_callback("refresh_conversations", lambda pkt: self.master.after(0, self.refresh_all_data))
        self.net.register_callback("forced_logout", self._on_forced_logout)
        self.net.register_callback("new_friend_request", self._on_new_friend_request)
        self.net.register_callback("refresh_friends", lambda pkt: self.master.after(0, self.load_friends))
        self.net.register_callback("on_reconnected", lambda pkt: self.master.after(0, self._on_reconnected))
        self.net.register_callback("connection_lost", lambda pkt: self.master.after(0, self._on_connection_lost))

        self._build_top_bar()
        self._build_sidebar()
        self._build_chat_area()
        
        # Load danh sách cuộc hội thoại & danh bạ ban đầu
        self.load_conversations()
        self.load_friends()

        # Bắt đầu tự động đồng bộ tin nhắn mới nhất cả hai bên
        self._start_periodic_sync()

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

        # Nút Cập nhật phiên bản mới (Ẩn mặc định, chỉ hiện nhấp nháy cam khi có update trên GitHub)
        self.btn_update = ctk.CTkButton(
            actions_frame,
            text="🚀 Có Bản Cập Nhật Mới! (Cập nhật ngay)",
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#F59E0B",
            hover_color="#D97706",
            text_color="black",
            corner_radius=8,
            command=self.perform_one_click_update
        )

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
            command=self.refresh_all_data
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

        # Bắt đầu luồng kiểm tra bản cập nhật mới trên GitHub định kỳ (mỗi 60s)
        self.project_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
        self._start_background_update_checker()

    def _start_background_update_checker(self):
        def _check():
            try:
                # 1. Kiểm tra Git pull dry-run hoặc kiểm tra SHA commit từ GitHub API
                has_update = False
                git_dir = os.path.join(self.project_dir, ".git")
                if os.path.exists(git_dir):
                    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    res = subprocess.run(
                        ["git", "ls-remote", "origin", "main"],
                        cwd=self.project_dir,
                        capture_output=True,
                        text=True,
                        timeout=5,
                        creationflags=flags
                    )
                    if res.returncode == 0 and res.stdout.strip():
                        remote_sha = res.stdout.strip().split()[0]
                        res_local = subprocess.run(
                            ["git", "rev-parse", "HEAD"],
                            cwd=self.project_dir,
                            capture_output=True,
                            text=True,
                            timeout=3,
                            creationflags=flags
                        )
                        local_sha = res_local.stdout.strip()
                        if remote_sha and local_sha and remote_sha != local_sha:
                            has_update = True
                else:
                    # Kiểm tra qua GitHub Commits API
                    api_url = "https://api.github.com/repos/Son3333/chat-online-/commits/main"
                    req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        remote_sha = data.get("sha", "")
                    
                    version_file = os.path.join(self.project_dir, ".version")
                    current_ver = ""
                    if os.path.exists(version_file):
                        with open(version_file, "r", encoding="utf-8") as f:
                            current_ver = f.read().strip()
                    if remote_sha and current_ver and remote_sha != current_ver:
                        has_update = True
                    elif remote_sha and not current_ver:
                        has_update = True

                if has_update:
                    self._latest_remote_sha = remote_sha
                    def _show_btn():
                        self.btn_update.pack(side="left", padx=8)
                        self._start_update_button_pulse()
                    self.master.after(0, _show_btn)
            except Exception:
                pass
            finally:
                # Kiểm tra lại sau mỗi 60 giây
                try:
                    self.master.after(60000, lambda: threading.Thread(target=_check, daemon=True).start())
                except Exception:
                    pass

        # Lần kiểm tra đầu tiên sau 5 giây mở app
        self.master.after(5000, lambda: threading.Thread(target=_check, daemon=True).start())

    def _start_update_button_pulse(self):
        if getattr(self, "_pulsing_update", False):
            return
        self._pulsing_update = True
        self._pulse_state = 0
        def _pulse():
            if not getattr(self, "_pulsing_update", False):
                return
            try:
                if self.btn_update.winfo_exists():
                    colors = ["#F59E0B", "#D97706", "#F59E0B", "#EA580C"]
                    self._pulse_state = (self._pulse_state + 1) % len(colors)
                    self.btn_update.configure(fg_color=colors[self._pulse_state])
                    self.master.after(800, _pulse)
            except Exception:
                pass
        _pulse()

    def perform_one_click_update(self, force=True):
        self._pulsing_update = False
        self.btn_update.configure(state="disabled", text="⏳ Đang tải bản cập nhật...", fg_color="#D97706")
        self.update_idletasks()

        def _do_update():
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            git_dir = os.path.join(self.project_dir, ".git")
            success = False

            if os.path.exists(git_dir):
                try:
                    # Dùng git fetch + reset --hard để đồng bộ 100%, không bị lỗi xung đột file cục bộ
                    r1 = subprocess.run(["git", "fetch", "origin", "main"], cwd=self.project_dir, timeout=15, creationflags=flags)
                    if r1.returncode == 0:
                        r2 = subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=self.project_dir, timeout=10, creationflags=flags)
                        if r2.returncode == 0:
                            success = True
                except Exception:
                    success = False

            if not success:
                # Tải zip về giải nén
                try:
                    import zipfile, io, shutil
                    zip_url = "https://github.com/Son3333/chat-online-/archive/refs/heads/main.zip"
                    req = urllib.request.Request(zip_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        zip_bytes = resp.read()
                    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
                        root_prefix = "chat-online--main/"
                        for member in z.namelist():
                            if member.startswith(root_prefix) and member != root_prefix:
                                rel_path = member[len(root_prefix):]
                                if not rel_path or rel_path.endswith("/"):
                                    continue
                                if rel_path in ["src/server/chat_database.db", "user_credentials.json", "server_config.json"]:
                                    continue
                                target_path = os.path.join(self.project_dir, rel_path)
                                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                                with z.open(member) as src, open(target_path, "wb") as dst:
                                    shutil.copyfileobj(src, dst)
                    success = True
                except Exception as e:
                    self.master.after(0, lambda: self.btn_update.configure(state="normal", text="🚀 Có Bản Cập Nhật Mới!", fg_color="#F59E0B"))
                    return

            if success and self._latest_remote_sha:
                try:
                    with open(os.path.join(self.project_dir, ".version"), "w", encoding="utf-8") as f:
                        f.write(self._latest_remote_sha)
                except Exception:
                    pass

            # Khởi động lại ứng dụng mượt mà không cần popup cản trở
            def _restart():
                self.btn_update.configure(text="✅ Đã tải xong! Đang mở lại...")
                launcher = os.path.join(self.project_dir, "launch.pyw")
                if not os.path.exists(launcher):
                    launcher = os.path.join(self.project_dir, "run_client.py")
                
                subprocess.Popen([sys.executable, launcher], cwd=self.project_dir)
                self.master.destroy()

            self.master.after(400, _restart)

        threading.Thread(target=_do_update, daemon=True).start()

    def refresh_all_data(self):
        self.load_conversations()
        self.load_friends()

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

    # --- SIDEBAR (TELEGRAM STYLE: CHATS & CONTACTS TABS) ---
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=0, fg_color=("gray95", "#0F172A"))
        self.sidebar.grid(row=1, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(3, weight=1)

        # 1. Search bar
        search_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        
        self.search_entry = ctk.CTkEntry(
            search_frame, 
            placeholder_text="🔍 Tìm @username hoặc ID (vd: #1)...", 
            height=36, 
            corner_radius=8
        )
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        # Search results popup list container
        self.search_results_frame = ctk.CTkScrollableFrame(self.sidebar, height=140, fg_color=("white", "#1E293B"))
        # (Được grid khi có kết quả tìm kiếm)

        # 2. Telegram Tab Switcher: [💬 Tin Nhắn]  [👥 Danh Bạ]
        tab_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        tab_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(4, 6))

        self.tab_selector = ctk.CTkSegmentedButton(
            tab_frame,
            values=["💬 Tin Nhắn", "👥 Danh Bạ"],
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            selected_color="#2563EB",
            selected_hover_color="#1D4ED8",
            command=self._on_sidebar_tab_changed
        )
        self.tab_selector.set("💬 Tin Nhắn")
        self.tab_selector.pack(fill="x")

        # 3. Action row (thay đổi theo tab: "➕ Tạo Nhóm Chat" hoặc "➕ Thêm Bạn Bè")
        self.action_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.action_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(2, 6))

        self.btn_sidebar_action = ctk.CTkButton(
            self.action_frame, 
            text="➕ Tạo Nhóm Chat Mới", 
            height=34, 
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=self.open_create_group_dialog
        )
        self.btn_sidebar_action.pack(fill="x")

        # 4. Container chứa nội dung tab (row=3)
        # Tab A: Danh sách cuộc trò chuyện
        self.conv_scroll = ctk.CTkScrollableFrame(self.sidebar, corner_radius=0, fg_color="transparent")
        self.conv_scroll.grid(row=3, column=0, sticky="nsew", padx=6, pady=(0, 6))
        self.conv_scroll.grid_columnconfigure(0, weight=1)

        # Tab B: Danh sách danh bạ bạn bè (ẩn ban đầu)
        self.friends_scroll = ctk.CTkScrollableFrame(self.sidebar, corner_radius=0, fg_color="transparent")
        self.friends_scroll.grid_columnconfigure(0, weight=1)

    def _on_sidebar_tab_changed(self, selected_value: str):
        if "Tin Nhắn" in selected_value:
            self.current_sidebar_tab = "chats"
            self.friends_scroll.grid_forget()
            self.conv_scroll.grid(row=3, column=0, sticky="nsew", padx=6, pady=(0, 6))
            self.btn_sidebar_action.configure(
                text="➕ Tạo Nhóm Chat Mới",
                fg_color="#0284C7",
                hover_color="#0369A1",
                command=self.open_create_group_dialog
            )
            self.load_conversations()
        else:
            self.current_sidebar_tab = "contacts"
            self.conv_scroll.grid_forget()
            self.friends_scroll.grid(row=3, column=0, sticky="nsew", padx=6, pady=(0, 6))
            self.btn_sidebar_action.configure(
                text="➕ Thêm Bạn Bè Mới (ID/User)",
                fg_color="#10B981",
                hover_color="#059669",
                command=self._focus_search_for_add
            )
            self.load_friends()

    def _focus_search_for_add(self):
        self.search_entry.focus_set()

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

        # Right header actions frame (Add friend button + Typing label)
        right_header = ctk.CTkFrame(self.chat_header, fg_color="transparent")
        right_header.pack(side="right", padx=16, pady=8)

        # Typing notification label
        self.lbl_typing = ctk.CTkLabel(
            right_header, 
            text="", 
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="#38BDF8"
        )
        self.lbl_typing.pack(side="left", padx=(0, 12))

        # Nút hành động bạn bè kiểu Telegram (Thêm vào danh bạ / Bạn bè)
        self.btn_contact_action = ctk.CTkButton(
            right_header,
            text="➕ Thêm Bạn Bè",
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            corner_radius=6,
            command=self.toggle_contact_friend
        )

        # 2. Scrollable Messages View
        self.messages_scroll = ctk.CTkScrollableFrame(self.chat_active_frame, fg_color="transparent")
        self.messages_scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)
        self.messages_scroll.grid_columnconfigure(0, weight=1)

        # 3. Bottom Input Bar
        self.input_bar = ctk.CTkFrame(self.chat_active_frame, height=65, corner_radius=0, fg_color=("white", "#1E293B"))
        self.input_bar.grid(row=2, column=0, sticky="ew")
        
        # Emoji bar buttons + Nút mở bảng Emoji đầy đủ (😊+)
        self.emoji_bar = ctk.CTkFrame(self.input_bar, fg_color="transparent")
        self.emoji_bar.pack(fill="x", padx=14, pady=(6, 2))
        
        # Nút mở bảng chọn tất cả Emoji (Picker Popup phong cách Telegram)
        self.btn_all_emojis = ctk.CTkButton(
            self.emoji_bar,
            text="😃 Bảng Emoji",
            width=92,
            height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("#E0E7FF", "#1E293B"),
            text_color=("#4338CA", "#818CF8"),
            hover_color=("#C7D2FE", "#334155"),
            corner_radius=6,
            command=self.toggle_emoji_picker
        )
        self.btn_all_emojis.pack(side="left", padx=(0, 6))

        # Dải Emoji nhanh phong phú (Cảm xúc, Hành động, Biểu tượng)
        quick_emojis = [
            "😀", "😂", "🥰", "😎", "🥳", "🤔", "😭", "😡", 
            "👍", "👎", "👏", "🙏", "❤️", "🔥", "🎉", "✨", 
            "🚀", "💯", "🤝", "💪", "⭐", "☕", "🍕", "🎯"
        ]
        for em in quick_emojis:
            b = ctk.CTkButton(
                self.emoji_bar, 
                text=em, 
                width=26, 
                height=24, 
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                hover_color=("gray85", "#334155"),
                command=lambda e=em: self.insert_emoji(e)
            )
            b.pack(side="left", padx=1)

        # Popup Frame Bảng Emoji Đầy Đủ (Ẩn mặc định, hiển thị nổi khi bấm 😃 Bảng Emoji)
        self.emoji_picker_popup = None

        # Toast banner màu cam nhấp nháy/hiển thị nhẹ nhàng khi mạng chập chờn (không bật popup cản trở)
        self.toast_banner = ctk.CTkFrame(self.input_bar, fg_color=("#FEF3C7", "#78350F"), corner_radius=6)
        self.toast_label = ctk.CTkLabel(
            self.toast_banner, 
            text="", 
            font=ctk.CTkFont(size=11, weight="bold"), 
            text_color=("#B45309", "#FDE68A")
        )
        self.toast_label.pack(side="left", padx=10, pady=3)

        # Input row
        self.input_row = ctk.CTkFrame(self.input_bar, fg_color="transparent")
        self.input_row.pack(fill="x", padx=14, pady=(0, 8))
        input_row = self.input_row

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

    def toggle_emoji_picker(self):
        """Mở hoặc đóng cửa sổ bảng chọn Emoji phân loại đa dạng (Chuẩn Unicode Telegram)."""
        if self.emoji_picker_popup and self.emoji_picker_popup.winfo_exists():
            self.emoji_picker_popup.destroy()
            self.emoji_picker_popup = None
            return

        self.emoji_picker_popup = ctk.CTkToplevel(self.master)
        self.emoji_picker_popup.title("Kho Biểu Tượng Cảm Xúc (Emoji Picker)")
        self.emoji_picker_popup.geometry("380x360")
        self.emoji_picker_popup.resizable(False, False)
        self.emoji_picker_popup.attributes("-topmost", True)

        # Đặt vị trí gần góc dưới phải màn hình
        try:
            x = self.btn_all_emojis.winfo_rootx()
            y = self.btn_all_emojis.winfo_rooty() - 370
            self.emoji_picker_popup.geometry(f"+{x}+{y}")
        except Exception:
            pass

        # Tabview phân loại
        tabs = ctk.CTkTabview(self.emoji_picker_popup, width=360, height=330, corner_radius=10)
        tabs.pack(fill="both", expand=True, padx=8, pady=8)

        categories = {
            "😃 Mặt cười": [
                "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "🥲", "🥹", "😊", "😇",
                "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😋", "😛", "😜", "🤪",
                "😎", "🤓", "🧐", "🥳", "😏", "😒", "😞", "😔", "😟", "😕", "🙁", "😣",
                "😖", "😫", "😩", "🥺", "😢", "😭", "😮‍💨", "😤", "😠", "😡", "🤬", "🤯",
                "😳", "🥵", "🥶", "😱", "😨", "😰", "😥", "😓", "🤗", "🫡", "🤫", "🫠"
            ],
            "👍 Bàn tay": [
                "👍", "👎", "👊", "✊", "🤛", "🤜", "👏", "🙌", "👐", "🤲", "🤝", "🙏",
                "✍️", "💅", "🤳", "💪", "👈", "👉", "👆", "👇", "☝️", "✌️", "🤞", "🫰",
                "🤟", "🤘", "🤙", "👋", "🤚", "🖐️", "✋", "🖖", "👌", "🤌", "🤏", "🫳"
            ],
            "❤️ Trái tim & Đồ vật": [
                "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔", "❤️‍🔥", "❤️‍🩹",
                "💖", "💗", "💓", "💞", "💕", "💌", "💘", "💝", "🎉", "🎊", "🎈", "🎂",
                "🔥", "✨", "🌟", "💫", "💥", "💯", "🚀", "🏆", "🥇", "🎯", "⭐", "🔔"
            ],
            "🍔 Ẩm thực & Thú cưng": [
                "☕", "🧋", "🍵", "🍺", "🍻", "🍕", "🍔", "🍟", "🌭", "🍿", "🍜", "🍣",
                "🍰", "🍦", "🍩", "🍪", "🍎", "🍉", "🍇", "🍓", "🐶", "🐱", "🐭", "🐹",
                "🐰", "🦊", "🐻", "🐼", "🐨", "🐯", "🦁", "🐮", "🐷", "🐸", "🐵", "🐔"
            ]
        }

        for cat_name, emoji_list in categories.items():
            tab_frame = tabs.add(cat_name)
            scroll = ctk.CTkScrollableFrame(tab_frame, fg_color="transparent")
            scroll.pack(fill="both", expand=True)

            # Lưới Emoji (6 cột)
            cols = 6
            for idx, em in enumerate(emoji_list):
                r = idx // cols
                c = idx % cols
                btn = ctk.CTkButton(
                    scroll,
                    text=em,
                    width=42,
                    height=38,
                    font=ctk.CTkFont(size=18),
                    fg_color="transparent",
                    hover_color=("gray85", "#334155"),
                    command=lambda e=em: self.insert_emoji(e)
                )
                btn.grid(row=r, column=c, padx=3, pady=3)

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
            self.btn_contact_action.pack_forget()
        else:
            is_on = conv.get("is_online", 0)
            status_text = "🟢 Trực tuyến" if is_on else "⚪ Ngoại tuyến"
            self.lbl_chat_subtitle.configure(text=status_text)
            
            # Kiểm tra trạng thái bạn bè để hiện nút Telegram Style
            partner_id = conv.get("partner_id")
            if partner_id:
                self.btn_contact_action.pack(side="right")
                self._update_header_friend_status(partner_id)
            else:
                self.btn_contact_action.pack_forget()

        # Highlight lại list
        self._render_conversation_list()

        # Tải tin nhắn
        self.load_messages_for_active_conv()
        self.msg_entry.focus_set()

    def _update_header_friend_status(self, partner_id: int):
        def _check():
            res = self.net.check_friend(self.current_user["id"], partner_id)
            st = res.get("friendship_status", "none") if res else "none"
            def _apply():
                if st == "friends":
                    self.btn_contact_action.configure(
                        text="⭐ Bạn Bè (Xóa khỏi danh bạ)",
                        fg_color=("#E2E8F0", "#334155"),
                        text_color=("#0F172A", "#F8FAFC"),
                        hover_color=("#CBD5E1", "#475569"),
                        state="normal"
                    )
                elif st == "sent_pending":
                    self.btn_contact_action.configure(
                        text="⏳ Đã gửi lời mời (Chờ duyệt)",
                        fg_color="#F59E0B",
                        text_color="black",
                        hover_color="#D97706",
                        state="disabled"
                    )
                elif st == "received_pending":
                    self.btn_contact_action.configure(
                        text="✅ Đồng ý kết bạn",
                        fg_color="#10B981",
                        text_color="white",
                        hover_color="#059669",
                        state="normal"
                    )
                else:
                    self.btn_contact_action.configure(
                        text="➕ Kết Bạn (Gửi lời mời)",
                        fg_color="#10B981",
                        text_color="white",
                        hover_color="#059669",
                        state="normal"
                    )
            self.master.after(0, _apply)
        threading.Thread(target=_check, daemon=True).start()

    def toggle_contact_friend(self):
        if not self.active_conv_data or self.active_conv_data.get("type") != "direct":
            return
        partner_id = self.active_conv_data.get("partner_id")
        if not partner_id:
            return

        def _do():
            check = self.net.check_friend(self.current_user["id"], partner_id)
            st = check.get("friendship_status", "none") if check else "none"
            if st == "friends":
                if messagebox.askyesno("Hủy kết bạn", "Bạn có chắc chắn muốn xóa người này khỏi Danh bạ bạn bè?"):
                    res = self.net.remove_friend(self.current_user["id"], partner_id)
                    msg = res.get("message", "Đã xóa khỏi danh bạ!") if res else "Không thể kết nối máy chủ!"
                else:
                    return
            elif st == "received_pending":
                res = self.net.accept_friend(self.current_user["id"], partner_id)
                msg = res.get("message", "Đã đồng ý kết bạn thành công!") if res else "Không thể kết nối máy chủ!"
            else:
                res = self.net.add_friend(self.current_user["id"], partner_id)
                msg = res.get("message", "Đã gửi lời mời kết bạn! Đang chờ đối phương chấp nhận.") if res else "Không thể gửi lời mời kết bạn do máy chủ gián đoạn!"
            
            def _done():
                self._update_header_friend_status(partner_id)
                self.load_friends()
                self._show_toast(msg)
            self.master.after(0, _done)
        threading.Thread(target=_do, daemon=True).start()

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
        self.rendered_msg_ids = set()
            
        for msg in messages:
            if "id" in msg:
                self.rendered_msg_ids.add(msg["id"])
            bubble = ChatBubble(self.messages_scroll, msg, self.current_user["id"], self.net)
            bubble.pack(fill="x")
        
        self.master.after(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        try:
            self.update_idletasks()
            self.messages_scroll._parent_canvas.yview_moveto(1.0)
            self.master.after(20, self._safe_scroll)
            self.master.after(80, self._safe_scroll)
            self.master.after(160, self._safe_scroll)
        except Exception:
            pass

    def _safe_scroll(self):
        try:
            self.messages_scroll._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    # --- GỬI TIN NHẮN & TỆP TIN ---
    def _show_toast(self, text: str, duration_ms=4000):
        try:
            self.toast_label.configure(text=text)
            self.toast_banner.pack(fill="x", padx=14, pady=(0, 4), before=self.input_row)
            def _hide():
                try:
                    self.toast_banner.pack_forget()
                except Exception:
                    pass
            self.master.after(duration_ms, _hide)
        except Exception:
            pass

    def send_text_message(self):
        if not self.active_conv_id:
            return
        content = self.msg_entry.get().strip()
        if not content:
            return
        
        self.msg_entry.delete(0, "end")
        
        def _send():
            ok = self.net.send_message(self.active_conv_id, self.current_user["id"], content, msg_type="text")
            if not ok:
                def _restore():
                    cur = self.msg_entry.get().strip()
                    if not cur:
                        self.msg_entry.insert(0, content)
                    self._show_toast("⚠️ Máy chủ đang cập nhật/kết nối lại... Tin nhắn đã được giữ lại trong ô nhập!")
                self.master.after(0, _restore)
        threading.Thread(target=_send, daemon=True).start()

    def pick_and_send_file(self):
        if not self.active_conv_id:
            self._show_toast("⚠️ Vui lòng chọn một cuộc trò chuyện trước!")
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
                    self._show_toast(f"❌ {res.get('message', 'Gửi tệp thất bại!') if res else 'Không thể gửi tệp do mất kết nối!'}")
            self.master.after(0, _done)
            
        threading.Thread(target=_upload, daemon=True).start()

    # --- XỬ LÝ SỰ KIỆN TỪ SERVER ---
    def _on_reconnected(self):
        """Xử lý khi máy chủ kết nối lại thành công sau khi khởi động hoặc rớt mạng."""
        self.refresh_all_data()
        if self.active_conv_id:
            self.load_messages_for_active_conv()

    def _on_connection_lost(self):
        """Xử lý khi mất kết nối tới máy chủ."""
        if self.active_conv_data and self.active_conv_data.get("type") == "direct":
            self.lbl_chat_subtitle.configure(text="🟡 Đang kết nối lại...")

    def _on_new_message_received(self, packet: dict):
        conv_id = packet.get("conversation_id")
        msg = packet.get("message")
        if not msg:
            return
        
        # Nếu đang mở cuộc hội thoại này -> render thêm bong bóng chat (tránh trùng lặp)
        if self.active_conv_id == conv_id:
            msg_id = msg.get("id")
            if msg_id and msg_id in self.rendered_msg_ids:
                return
            if msg_id:
                self.rendered_msg_ids.add(msg_id)
                
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

    def _on_forced_logout(self, packet: dict):
        """Xử lý khi tài khoản được đăng nhập trên một thiết bị khác (Cơ chế Facebook)."""
        msg = packet.get("message", "Tài khoản của bạn vừa đăng nhập trên thiết bị khác!")
        def _handle():
            # Xóa mật khẩu đã lưu để buộc người dùng phải nhập lại mật khẩu
            auth_cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "user_credentials.json")
            if os.path.exists(auth_cache_file):
                try:
                    os.remove(auth_cache_file)
                except Exception:
                    pass

            messagebox.showwarning("Cảnh báo bảo mật đăng nhập", msg)
            self.on_logout()
        self.master.after(0, _handle)

    # --- TÌM KIẾM NGƯỜI DÙNG & TẠO CHAT 1-1 ---
    def _on_search_key(self, event):
        kw = self.search_entry.get().strip()
        if not kw:
            self.search_results_frame.grid_forget()
            return
            
        search_kw = kw.lstrip("@#").strip()
        if not search_kw:
            self.search_results_frame.grid_forget()
            return
            
        def _search():
            res = self.net.search_users(search_kw, self.current_user["id"])
            if res is None:
                self.master.after(0, lambda: self._show_search_error("Mất kết nối máy chủ! Đang thử lại..."))
                return
            users = res.get("users", [])
            self.master.after(0, lambda: self._show_search_results(users))
        threading.Thread(target=_search, daemon=True).start()

    def _show_search_error(self, message: str):
        for w in self.search_results_frame.winfo_children():
            w.destroy()
        self.search_results_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 4))
        ctk.CTkLabel(self.search_results_frame, text=message, font=ctk.CTkFont(size=11), text_color="#EF4444").pack(pady=8)

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
            
            ctk.CTkLabel(row, text=f"{u['full_name']} (@{u['username']} • #{u['id']})", font=ctk.CTkFont(size=11)).pack(side="left", padx=4)
            
            btn_box = ctk.CTkFrame(row, fg_color="transparent")
            btn_box.pack(side="right", padx=2)

            ctk.CTkButton(
                btn_box, 
                text="💬 Nhắn", 
                width=55, 
                height=24, 
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#0284C7",
                hover_color="#0369A1",
                command=lambda uid=u["id"]: self.start_direct_chat_with(uid)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                btn_box, 
                text="➕ Thêm", 
                width=55, 
                height=24, 
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#10B981",
                hover_color="#059669",
                command=lambda uid=u["id"]: self.quick_add_contact(uid)
            ).pack(side="left", padx=2)

    def quick_add_contact(self, friend_id: int):
        self.search_entry.delete(0, "end")
        self.search_results_frame.grid_forget()
        
        def _add():
            res = self.net.add_friend(self.current_user["id"], friend_id)
            msg = res.get("message", "Đã thêm vào danh bạ!") if res else "Lỗi thêm bạn bè"
            self.master.after(0, lambda: messagebox.showinfo("Danh bạ", msg))
            self.master.after(0, self.load_friends)
        threading.Thread(target=_add, daemon=True).start()

    def start_direct_chat_with(self, partner_id: int):
        self.search_entry.delete(0, "end")
        self.search_results_frame.grid_forget()
        
        def _call():
            res = self.net.start_direct_chat(self.current_user["id"], partner_id)
            if res and "conversation_id" in res:
                conv_id = res["conversation_id"]
                self.conversations = res.get("conversations", [])
                
                # Switch to chats tab
                def _open():
                    self.tab_selector.set("💬 Tin Nhắn")
                    self._on_sidebar_tab_changed("💬 Tin Nhắn")
                    target_conv = next((c for c in self.conversations if c["id"] == conv_id), None)
                    if target_conv:
                        self.select_conversation(target_conv)
                    else:
                        self.load_conversations()
                self.master.after(0, _open)
        threading.Thread(target=_call, daemon=True).start()

    # --- DANH BẠ BẠN BÈ & DUYỆT KẾT BẠN (FRIEND REQUEST & APPROVAL) ---
    def load_friends(self):
        def _fetch():
            res = self.net.get_friends(self.current_user["id"])
            if res:
                self.friends = res.get("friends", [])
                self.pending_requests = res.get("pending_requests", [])
                self.master.after(0, self._render_friends_list)
        threading.Thread(target=_fetch, daemon=True).start()

    def _render_friends_list(self):
        for widget in self.friends_scroll.winfo_children():
            widget.destroy()
        self.friend_widgets.clear()

        # 1. Hiển thị Lời mời kết bạn đang chờ bạn duyệt (nếu có)
        if self.pending_requests:
            req_banner = ctk.CTkFrame(self.friends_scroll, fg_color=("#FEF3C7", "#78350F"), corner_radius=8)
            req_banner.pack(fill="x", padx=6, pady=(4, 6))
            ctk.CTkLabel(
                req_banner,
                text=f"🔔 LỜI MỜI KẾT BẠN CHỜ DUYỆT ({len(self.pending_requests)})",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=("#92400E", "#FDE68A")
            ).pack(padx=8, pady=4, anchor="w")

            for req in self.pending_requests:
                r_id = req["id"]
                card = ctk.CTkFrame(self.friends_scroll, corner_radius=10, fg_color=("white", "#1E293B"))
                card.pack(fill="x", pady=3, padx=2)

                row_f = ctk.CTkFrame(card, fg_color="transparent")
                row_f.pack(fill="x", padx=10, pady=8)

                av_btn = ctk.CTkButton(
                    row_f,
                    text=req["full_name"][:1].upper(),
                    width=36,
                    height=36,
                    corner_radius=18,
                    fg_color=req.get("avatar_color", "#F59E0B"),
                    font=ctk.CTkFont(size=13, weight="bold"),
                    state="disabled"
                )
                av_btn.pack(side="left", padx=(0, 8))

                info_col = ctk.CTkFrame(row_f, fg_color="transparent")
                info_col.pack(side="left", fill="x", expand=True)

                ctk.CTkLabel(
                    info_col,
                    text=req["full_name"],
                    font=ctk.CTkFont(size=12, weight="bold"),
                    anchor="w"
                ).pack(anchor="w")

                ctk.CTkLabel(
                    info_col,
                    text=f"@{req['username']}",
                    font=ctk.CTkFont(size=11),
                    text_color="gray50",
                    anchor="w"
                ).pack(anchor="w")

                btn_box = ctk.CTkFrame(row_f, fg_color="transparent")
                btn_box.pack(side="right")

                ctk.CTkButton(
                    btn_box,
                    text="✅ Đồng ý",
                    width=65,
                    height=28,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    fg_color="#10B981",
                    hover_color="#059669",
                    command=lambda u=r_id: self._accept_friend_request(u)
                ).pack(side="left", padx=2)

                ctk.CTkButton(
                    btn_box,
                    text="✕",
                    width=28,
                    height=28,
                    font=ctk.CTkFont(size=11),
                    fg_color=("#FEE2E2", "#450A0A"),
                    text_color=("#DC2626", "#F87171"),
                    hover_color=("#FECACA", "#7F1D1D"),
                    command=lambda u=r_id: self._reject_friend_request(u)
                ).pack(side="left", padx=2)

        # 2. Danh sách bạn bè chính thức
        if not self.friends:
            if not self.pending_requests:
                empty_box = ctk.CTkFrame(self.friends_scroll, fg_color="transparent")
                empty_box.pack(pady=30, padx=10)
                ctk.CTkLabel(empty_box, text="👥", font=ctk.CTkFont(size=36)).pack(pady=(0, 6))
                ctk.CTkLabel(
                    empty_box, 
                    text="Danh bạ trống!\nTìm @username hoặc #ID ở trên\nđể gửi lời mời kết bạn.", 
                    font=ctk.CTkFont(size=12), 
                    text_color="gray60",
                    justify="center"
                ).pack()
            return

        ctk.CTkLabel(
            self.friends_scroll, 
            text=f"DANH SÁCH BẠN BÈ ({len(self.friends)})", 
            font=ctk.CTkFont(size=11, weight="bold"), 
            text_color="gray50"
        ).pack(anchor="w", padx=10, pady=(6, 4))

        for fr in self.friends:
            f_id = fr["id"]
            card = ctk.CTkFrame(self.friends_scroll, corner_radius=10, fg_color=("white", "#1E293B"), cursor="hand2")
            card.pack(fill="x", pady=3, padx=2)
            self.friend_widgets[f_id] = card

            row_f = ctk.CTkFrame(card, fg_color="transparent")
            row_f.pack(fill="x", padx=10, pady=8)

            av_col = fr.get("avatar_color", "#10B981")
            av_btn = ctk.CTkButton(
                row_f, 
                text=fr["full_name"][:1].upper(), 
                width=38, 
                height=38, 
                corner_radius=19,
                fg_color=av_col,
                font=ctk.CTkFont(size=14, weight="bold"),
                state="disabled"
            )
            av_btn.pack(side="left", padx=(0, 10))

            text_box = ctk.CTkFrame(row_f, fg_color="transparent")
            text_box.pack(side="left", fill="x", expand=True)

            title_row = ctk.CTkFrame(text_box, fg_color="transparent")
            title_row.pack(fill="x")

            lbl_name = ctk.CTkLabel(
                title_row, 
                text=fr["full_name"], 
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w"
            )
            lbl_name.pack(side="left")

            if fr.get("is_online"):
                dot = ctk.CTkLabel(title_row, text=" 🟢", font=ctk.CTkFont(size=9))
                dot.pack(side="left")

            lbl_sub = ctk.CTkLabel(
                text_box, 
                text=f"@{fr['username']}  •  ID: #{fr['id']}", 
                font=ctk.CTkFont(size=11), 
                text_color="gray50",
                anchor="w"
            )
            lbl_sub.pack(fill="x", pady=(1, 0))

            btn_action = ctk.CTkFrame(row_f, fg_color="transparent")
            btn_action.pack(side="right")

            ctk.CTkButton(
                btn_action,
                text="💬",
                width=32,
                height=32,
                corner_radius=16,
                font=ctk.CTkFont(size=13),
                fg_color="#0284C7",
                hover_color="#0369A1",
                command=lambda uid=f_id: self.start_direct_chat_with(uid)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                btn_action,
                text="✕",
                width=32,
                height=32,
                corner_radius=16,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=("#FEE2E2", "#450A0A"),
                text_color=("#DC2626", "#F87171"),
                hover_color=("#FECACA", "#7F1D1D"),
                command=lambda uid=f_id: self._confirm_remove_friend(uid)
            ).pack(side="left", padx=2)

    def _accept_friend_request(self, requester_id: int):
        def _do():
            res = self.net.accept_friend(self.current_user["id"], requester_id)
            self.master.after(0, self.load_friends)
            if self.active_conv_data and self.active_conv_data.get("partner_id") == requester_id:
                self.master.after(0, lambda: self._update_header_friend_status(requester_id))
            msg = res.get("message", "Đã đồng ý kết bạn!") if res else "Đã chấp nhận!"
            self.master.after(0, lambda: messagebox.showinfo("Kết bạn thành công", msg))
        threading.Thread(target=_do, daemon=True).start()

    def _reject_friend_request(self, requester_id: int):
        def _do():
            self.net.reject_friend(self.current_user["id"], requester_id)
            self.master.after(0, self.load_friends)
        threading.Thread(target=_do, daemon=True).start()

    def _on_new_friend_request(self, packet: dict):
        self.master.after(0, self.load_friends)

    def _confirm_remove_friend(self, friend_id: int):
        if messagebox.askyesno("Xóa khỏi danh bạ", "Bạn có chắc muốn xóa người này khỏi Danh bạ bạn bè?"):
            def _remove():
                res = self.net.remove_friend(self.current_user["id"], friend_id)
                self.master.after(0, self.load_friends)
                if self.active_conv_data and self.active_conv_data.get("partner_id") == friend_id:
                    self.master.after(0, lambda: self._update_header_friend_status(friend_id))
            threading.Thread(target=_remove, daemon=True).start()

    def _start_periodic_sync(self):
        """Tự động đồng bộ tin nhắn mới nhất cả hai bên định kỳ (mỗi 2.5 giây)."""
        def _sync_loop():
            try:
                # 1. Nếu đang mở cuộc trò chuyện, kiểm tra xem có tin nhắn mới không
                if self.active_conv_id:
                    conv_id = self.active_conv_id
                    res = self.net.get_messages(conv_id)
                    if res and res.get("conversation_id") == conv_id:
                        new_msgs = res.get("messages", [])
                        missing_msgs = [m for m in new_msgs if m.get("id") and m.get("id") not in self.rendered_msg_ids]
                        if missing_msgs:
                            def _append_missing(msgs=missing_msgs):
                                for m in msgs:
                                    if m.get("id"):
                                        self.rendered_msg_ids.add(m["id"])
                                    bubble = ChatBubble(self.messages_scroll, m, self.current_user["id"], self.net)
                                    bubble.pack(fill="x")
                                self._scroll_to_bottom()
                            self.master.after(0, _append_missing)
                # 2. Cập nhật danh sách hội thoại ngầm
                res_conv = self.net.get_conversations(self.current_user["id"])
                if res_conv and "conversations" in res_conv:
                    new_convs = res_conv["conversations"]
                    if len(new_convs) != len(self.conversations) or any(
                        new_convs[i].get("last_message") != self.conversations[i].get("last_message") 
                        for i in range(min(len(new_convs), len(self.conversations)))
                    ):
                        self.conversations = new_convs
                        self.master.after(0, self._render_conversation_list)
            except Exception:
                pass
            finally:
                try:
                    self.master.after(2500, lambda: threading.Thread(target=_sync_loop, daemon=True).start())
                except Exception:
                    pass

        self.master.after(2500, lambda: threading.Thread(target=_sync_loop, daemon=True).start())

    def open_create_group_dialog(self):
        CreateGroupDialog(self.master, self.current_user, self.net, on_group_created=self._on_group_created)

    def _on_group_created(self, conv_id):
        self.load_conversations()

