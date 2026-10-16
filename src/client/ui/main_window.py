import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import time
import os
import json
import subprocess
import urllib.request
from typing import Optional

from src.client.ui.chat_bubble import ChatBubble
from src.client.ui.create_group_dialog import CreateGroupDialog
from src.client.call.call_window import IncomingCallDialog, ActiveCallWindow
from src.client.desktop.toast import ToastNotification
from src.client.desktop.popout_window import PopoutChatWindow, PopoutInfoWindow

class MainWindow(ctk.CTkFrame):
    def __init__(self, master, current_user: dict, network_client, on_logout):
        super().__init__(master, fg_color="transparent")
        self.current_user = current_user
        self.net = network_client
        self.on_logout = on_logout

        self.info_sidebar = None
        self.info_sidebar_open = False
        self.is_topmost = False
        self.master.bind("<Escape>", self._on_escape_pressed)

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
        self.msg_bubbles = {}
        self._update_prompted = False
        self._latest_remote_sha = ""

        # Trạng thái cuộc gọi thoại / video
        self.active_call_window = None
        self.incoming_call_dialog = None

        # Trạng thái trả lời tin nhắn (Quote / Reply) & Ghim tin nhắn (Pin)
        self.reply_target_message = None
        self.current_pinned_message = None

        # Grid layout: Sidebar rộng 340px, Nội dung chính chiếm phần còn lại
        self.grid_columnconfigure(0, weight=0, minsize=340) # Sidebar rộng tối ưu 340px
        self.grid_columnconfigure(1, weight=1)              # Chat Area
        self.grid_rowconfigure(0, weight=0)                 # Top Bar
        self.grid_rowconfigure(1, weight=1)                 # Main Content

        # 1. Đăng ký nhận sự kiện thời gian thực từ NetworkClient
        self.net.register_callback("new_message", self._on_new_message_received)
        self.net.register_callback("message_recalled", self._on_message_recalled)
        self.net.register_callback("conversation_deleted", self._on_conversation_deleted)
        self.net.register_callback("block_status_changed", self._on_block_status_changed)
        self.net.register_callback("user_status_changed", self._on_user_status_changed)
        self.net.register_callback("user_typing", self._on_user_typing)
        self.net.register_callback("refresh_conversations", lambda pkt: self.master.after(0, self.refresh_all_data))
        self.net.register_callback("forced_logout", self._on_forced_logout)
        self.net.register_callback("new_friend_request", self._on_new_friend_request)
        self.net.register_callback("refresh_friends", lambda pkt: self.master.after(0, self.load_friends))
        self.net.register_callback("on_reconnected", lambda pkt: self.master.after(0, self._on_reconnected))
        self.net.register_callback("connection_lost", lambda pkt: self.master.after(0, self._on_connection_lost))

        # Đăng ký sự kiện Cuộc gọi (Voice & Video Call)
        self.net.register_callback("call_incoming", self._on_call_incoming)
        self.net.register_callback("call_connected", self._on_call_connected)
        self.net.register_callback("call_rejected", self._on_call_rejected)
        self.net.register_callback("call_ended", self._on_call_ended)
        self.net.register_callback("call_media_relay", self._on_call_media_relay)

        # Đăng ký sự kiện Tương tác Cảm xúc & Ghim tin nhắn
        self.net.register_callback("reaction_updated", self._on_reaction_updated)
        self.net.register_callback("pinned_updated", self._on_pinned_updated)

        self._build_top_bar()
        self._build_sidebar()
        self._build_chat_area()

        # Load danh sách cuộc hội thoại & danh bạ ban đầu
        self.refresh_all_data()

        # Bắt đầu tự động đồng bộ tin nhắn mới nhất cả hai bên
        self._start_periodic_sync()

    # --- TOP BAR (HEADER XANH NAVY #1D293D) ---
    def _build_top_bar(self):
        self.top_bar = ctk.CTkFrame(self, height=72, corner_radius=0, fg_color=("#F1F5F9", "#1D293D"))
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")

        # User profile badge (Bên trái)
        user_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        user_frame.pack(side="left", padx=18, pady=10)

        # Avatar hình tròn màu xanh cyan, hiển thị chữ cái đầu
        avatar_col = self.current_user.get("avatar_color") or "#06B6D4"
        initial_letter = self.current_user["full_name"][:1].upper() if self.current_user.get("full_name") else "V"
        self.avatar_circle = ctk.CTkButton(
            user_frame,
            text=initial_letter,
            width=46,
            height=46,
            corner_radius=23,
            fg_color=avatar_col,
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            state="disabled"
        )
        self.avatar_circle.pack(side="left", padx=(0, 12))

        name_box = ctk.CTkFrame(user_frame, fg_color="transparent")
        name_box.pack(side="left")

        # Tên tài khoản
        ctk.CTkLabel(
            name_box,
            text=self.current_user["full_name"],
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=("black", "white")
        ).pack(anchor="w")

        # Trạng thái chấm xanh, username và ID
        status_box = ctk.CTkFrame(name_box, fg_color="transparent")
        status_box.pack(anchor="w", pady=(1, 0))
        ctk.CTkLabel(
            status_box,
            text=f"🟢 Trực tuyến  •  @{self.current_user['username']}  •  ID: #{self.current_user['id']}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#10B981"
        ).pack(side="left")

        # Right actions (Bên phải)
        actions_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        actions_frame.pack(side="right", padx=16, pady=10)

        # Nút hiển thị & sao chép địa chỉ kết nối
        server_info_text = f"🌐 {self.net.host}:{self.net.port}"
        self.btn_copy_server = ctk.CTkButton(
            actions_frame,
            text=f"{server_info_text} 📋",
            height=34,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=("#E2E8F0", "#0F172A"),
            hover_color=("#CBD5E1", "#1E293B"),
            text_color=("#0284C7", "#38BDF8"),
            command=self.copy_server_info
        )
        self.btn_copy_server.pack(side="left", padx=4)

        # Nút “Chụp ảnh” màu xanh dương
        self.btn_snip = ctk.CTkButton(
            actions_frame,
            text="📷 Chụp ảnh",
            height=34,
            width=92,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#2563EB",
            text_color="white",
            hover_color="#1D4ED8",
            command=self.open_screenshot_tool
        )
        self.btn_snip.pack(side="left", padx=4)

        # Nút “Khóa” màu đỏ
        self.btn_lock = ctk.CTkButton(
            actions_frame,
            text="🔒 Khóa",
            height=34,
            width=70,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#EF4444",
            text_color="white",
            hover_color="#DC2626",
            command=self.lock_app
        )
        self.btn_lock.pack(side="left", padx=4)

        # Nút “Ghim” màu xanh xám
        self.btn_always_on_top = ctk.CTkButton(
            actions_frame,
            text="📌 Ghim",
            width=70,
            height=34,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#475569",
            text_color="white",
            hover_color="#334155",
            command=self.toggle_topmost
        )
        self.btn_always_on_top.pack(side="left", padx=4)

        # Nút Cập nhật phiên bản mới (Ẩn mặc định)
        self.btn_update = ctk.CTkButton(
            actions_frame,
            text="🚀 Có Bản Cập Nhật Mới! (Cập nhật ngay)",
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#F59E0B",
            hover_color="#D97706",
            text_color="black",
            corner_radius=8,
            command=self.perform_one_click_update
        )

        # Công tắc bật/tắt “Giao diện Tối”
        self.theme_switch = ctk.CTkSwitch(
            actions_frame,
            text="Giao diện Tối",
            command=self.toggle_theme,
            font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        if ctk.get_appearance_mode() == "Dark":
            self.theme_switch.select()
        self.theme_switch.pack(side="left", padx=10)

        # Nút “Làm mới”
        ctk.CTkButton(
            actions_frame,
            text="🔄 Làm mới",
            width=85,
            height=34,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=("#E2E8F0", "#334155"),
            text_color=("black", "white"),
            hover_color=("#CBD5E1", "#475569"),
            command=self.refresh_all_data
        ).pack(side="left", padx=4)

        # Nút “Đăng xuất” màu đỏ kèm xác nhận
        ctk.CTkButton(
            actions_frame,
            text="🚪 Đăng xuất",
            width=92,
            height=34,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#DC2626",
            text_color="white",
            hover_color="#B91C1C",
            command=self._confirm_logout
        ).pack(side="left", padx=4)

        # Bắt đầu luồng kiểm tra bản cập nhật mới trên GitHub định kỳ (mỗi 60s)
        self.project_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
        self._start_background_update_checker()

    def _confirm_logout(self):
        if messagebox.askyesno("Xác nhận đăng xuất", "Bạn có chắc chắn muốn đăng xuất khỏi ứng dụng không?"):
            self.on_logout()

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
                    if api_url.startswith("https://"):
                        req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(req, timeout=5) as resp:  # nosec B310
                            data = json.loads(resp.read().decode("utf-8"))
                            remote_sha = data.get("sha", "")
                    else:
                        remote_sha = ""

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
                    import zipfile
                    import io
                    import shutil
                    zip_url = "https://github.com/Son3333/chat-online-/archive/refs/heads/main.zip"
                    if not zip_url.startswith("https://"):
                        return
                    req = urllib.request.Request(zip_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=30) as resp:  # nosec B310
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
                except Exception:
                    self.master.after(0, lambda: self.btn_update.configure(state="normal", text="🚀 Có Bản Cập Nhật Mới!", fg_color="#F59E0B"))
                    return

            if success and self._latest_remote_sha:
                try:
                    with open(os.path.join(self.project_dir, ".version"), "w", encoding="utf-8") as f:
                        f.write(self._latest_remote_sha)
                except Exception:
                    pass

            # Cập nhật thành công: Tự động làm mới dữ liệu trực tiếp trong app KHÔNG làm tắt/mất ứng dụng!
            def _on_success():
                self.btn_update.configure(state="normal", text="✅ Đã Cập Nhật Mới Nhất!", fg_color="#10B981")
                self._show_toast("✅ Đã cập nhật phiên bản mới nhất! Danh bạ bạn bè đã được làm mới.")
                self.refresh_all_data()
                # Tự động ẩn nút cập nhật sau 4 giây
                self.master.after(4000, lambda: self.btn_update.pack_forget())

            self.master.after(0, _on_success)

        threading.Thread(target=_do_update, daemon=True).start()

    def refresh_all_data(self):
        def _fetch_all():
            try:
                res_fr = self.net.get_friends(self.current_user["id"])
                if res_fr:
                    self.friends = res_fr.get("friends", [])
                    self.pending_requests = res_fr.get("pending_requests", [])
            except Exception:
                pass

            try:
                res_cv = self.net.get_conversations(self.current_user["id"])
                if res_cv and "conversations" in res_cv:
                    self.conversations = res_cv["conversations"]
                else:
                    self.conversations = []
            except Exception:
                self.conversations = []

            def _update_ui():
                if getattr(self, "current_sidebar_tab", "chats") == "chats":
                    self._render_conversation_list()
                else:
                    self._render_friends_list()
            self.master.after(0, _update_ui)
        threading.Thread(target=_fetch_all, daemon=True).start()

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

    # --- SIDEBAR (340px, XANH ĐEN #10192C) ---
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=340, corner_radius=0, fg_color=("#F8FAFC", "#10192C"))
        self.sidebar.grid(row=1, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(3, weight=1)

        # 1. Ô tìm kiếm có icon kính lúp, placeholder chuẩn
        search_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Tìm @username hoặc ID (vd: #1)...",
            height=38,
            corner_radius=8,
            fg_color=("#FFFFFF", "#1E293B"),
            font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        # Search results popup list container
        self.search_results_frame = ctk.CTkScrollableFrame(self.sidebar, height=140, fg_color=("#FFFFFF", "#1E293B"), corner_radius=8)

        # 2. Thanh chuyển tab: [💬 Tin Nhắn]  [👥 Danh Bạ]
        tab_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        tab_frame.grid(row=1, column=0, sticky="ew", padx=14, pady=(2, 8))

        self.tab_selector = ctk.CTkSegmentedButton(
            tab_frame,
            values=["💬 Tin Nhắn", "👥 Danh Bạ"],
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            selected_color="#2563EB",
            selected_hover_color="#1D4ED8",
            corner_radius=8,
            command=self._on_sidebar_tab_changed
        )
        self.tab_selector.set("💬 Tin Nhắn")
        self.tab_selector.pack(fill="x")

        # 3. Action row
        self.action_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.action_frame.grid(row=2, column=0, sticky="ew", padx=14, pady=(2, 8))

        # Nút màu xanh cyan chiếm toàn bộ chiều rộng: “+ Tạo Nhóm Chat Mới”
        self.btn_sidebar_action = ctk.CTkButton(
            self.action_frame,
            text="➕ Tạo Nhóm Chat Mới",
            height=38,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#06B6D4",
            hover_color="#0891B2",
            text_color="white",
            command=self.open_create_group_dialog
        )
        self.btn_sidebar_action.pack(fill="x")

        # Nút màu xanh đen: “Cloud của tôi (Lưu trữ cá nhân)”
        self.btn_saved_cloud = ctk.CTkButton(
            self.action_frame,
            text="☁️ Cloud của tôi (Lưu trữ cá nhân)",
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=("#EEF2FF", "#202C40"),
            text_color=("#4F46E5", "#A5B4FC"),
            hover_color=("#E0E7FF", "#2A3B58"),
            command=self.open_saved_messages
        )
        self.btn_saved_cloud.pack(fill="x", pady=(6, 0))

        # 4. Container chứa danh sách cuộc trò chuyện dạng card bo góc
        self.conv_scroll = ctk.CTkScrollableFrame(self.sidebar, corner_radius=0, fg_color="transparent")
        self.conv_scroll.grid(row=3, column=0, sticky="nsew", padx=8, pady=(0, 8))
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
        self.chat_container = ctk.CTkFrame(self, corner_radius=0, fg_color=("#F1F5F9", "#0B1020"))
        self.chat_container.grid(row=1, column=1, sticky="nsew")
        self.chat_container.grid_columnconfigure(0, weight=1)
        self.chat_container.grid_rowconfigure(0, weight=1)

        # Empty state (khi chưa chọn cuộc hội thoại)
        self.empty_state = ctk.CTkFrame(self.chat_container, fg_color="transparent")
        self.empty_state.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self.empty_state,
            text="💬",
            font=ctk.CTkFont(size=78),
            text_color="#38BDF8"
        ).pack(pady=(0, 16))
        ctk.CTkLabel(
            self.empty_state,
            text="Chào mừng đến với Ứng dụng Nhắn tin!",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=("black", "white")
        ).pack(pady=(0, 6))
        ctk.CTkLabel(
            self.empty_state,
            text="Hãy chọn một cuộc trò chuyện ở danh sách bên trái hoặc tạo nhóm mới để bắt đầu.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("#64748B", "#94A3B8")
        ).pack()

        # Chat Active Views (sẽ hiển thị khi chọn hội thoại)
        self.chat_active_frame = ctk.CTkFrame(self.chat_container, fg_color="transparent")
        self.chat_active_frame.grid_columnconfigure(0, weight=1)
        self.chat_active_frame.grid_rowconfigure(0, weight=0)  # Chat Header (cố định)
        self.chat_active_frame.grid_rowconfigure(1, weight=0)  # Pinned banner (chỉ hiện khi có tin ghim, không chiếm khoảng trống)
        self.chat_active_frame.grid_rowconfigure(2, weight=1)  # Messages Scroll (chiếm toàn bộ chiều cao)
        self.chat_active_frame.grid_rowconfigure(3, weight=0)  # Input Bar (cố định)

        # 1. Chat Header (Xanh navy #1D293D)
        self.chat_header = ctk.CTkFrame(self.chat_active_frame, height=58, corner_radius=0, fg_color=("#FFFFFF", "#1D293D"))
        self.chat_header.grid(row=0, column=0, sticky="ew")

        header_info = ctk.CTkFrame(self.chat_header, fg_color="transparent")
        header_info.pack(side="left", padx=16, pady=8)

        self.lbl_chat_title = ctk.CTkLabel(header_info, text="Tiêu đề cuộc trò chuyện", font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"))
        self.lbl_chat_title.pack(anchor="w")

        self.lbl_chat_subtitle = ctk.CTkLabel(header_info, text="Trạng thái...", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=("#64748B", "#94A3B8"))
        self.lbl_chat_subtitle.pack(anchor="w")

        # Right header actions frame (Add friend button + Typing label + Call buttons)
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

        # Nút Gọi Thoại (📞)
        self.btn_call_voice = ctk.CTkButton(
            right_header,
            text="📞",
            width=36,
            height=32,
            font=ctk.CTkFont(size=15),
            fg_color=("#EFF6FF", "#1E293B"),
            text_color=("#2563EB", "#60A5FA"),
            hover_color=("#DBEAFE", "#2563EB"),
            corner_radius=6,
            command=lambda: self.start_call("voice")
        )

        # Nút Gọi Video (📹)
        self.btn_call_video = ctk.CTkButton(
            right_header,
            text="📹",
            width=36,
            height=32,
            font=ctk.CTkFont(size=15),
            fg_color=("#ECFDF5", "#064E3B"),
            text_color=("#059669", "#34D399"),
            hover_color=("#D1FAE5", "#059669"),
            corner_radius=6,
            command=lambda: self.start_call("video")
        )

        # Trạng thái bạn bè và chặn của đối phương trong cuộc hội thoại 1-1 đang mở
        self.active_partner_friend_status = "none"
        self.active_partner_blocked = False

        # Nút Tách cửa sổ chat riêng (↗️ Pop-out Chat Window)
        self.btn_popout = ctk.CTkButton(
            right_header,
            text="↗️",
            width=36,
            height=32,
            font=ctk.CTkFont(size=14),
            fg_color=("#F1F5F9", "#334155"),
            text_color=("#0284C7", "#38BDF8"),
            hover_color=("#E2E8F0", "#475569"),
            corner_radius=6,
            command=self.popout_current_conversation
        )

        # Nút Thông tin cuộc hội thoại (ℹ️ 3-Column Info Sidebar)
        self.btn_info = ctk.CTkButton(
            right_header,
            text="ℹ️",
            width=36,
            height=32,
            font=ctk.CTkFont(size=14),
            fg_color=("#F1F5F9", "#334155"),
            text_color=("#475569", "#94A3B8"),
            hover_color=("#E2E8F0", "#475569"),
            corner_radius=6,
            command=self.toggle_info_sidebar
        )

        # Nút menu tùy chọn cuộc trò chuyện "..." (Ẩn gọn các tính năng Bạn bè, Chặn, Xóa chat)
        self.btn_chat_options = ctk.CTkButton(
            right_header,
            text="...",
            width=38,
            height=32,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=("#F1F5F9", "#334155"),
            text_color=("#475569", "#94A3B8"),
            hover_color=("#E2E8F0", "#475569"),
            corner_radius=6,
            command=self._show_chat_options_menu
        )

        # Thanh Tin Nhắn Đã Ghim (Pinned Message Banner - Row 1)
        self.pinned_banner = ctk.CTkFrame(self.chat_active_frame, height=36, corner_radius=0, fg_color=("#F0FDF4", "#064E3B"))
        pin_inner = ctk.CTkFrame(self.pinned_banner, fg_color="transparent")
        pin_inner.pack(fill="x", padx=14, pady=3)
        ctk.CTkLabel(pin_inner, text="📌", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 6))
        self.lbl_pinned_text = ctk.CTkLabel(
            pin_inner,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#15803D", "#4ADE80"),
            anchor="w"
        )
        self.lbl_pinned_text.pack(side="left", fill="x", expand=True)
        self.btn_unpin = ctk.CTkButton(
            pin_inner,
            text="✕ Bỏ ghim",
            width=65,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color=("#15803D", "#4ADE80"),
            hover_color=("#DCFCE7", "#065F46"),
            command=self.unpin_current_message
        )
        self.btn_unpin.pack(side="right")

        # 2. Scrollable Messages View (Row 2)
        self.messages_scroll = ctk.CTkScrollableFrame(self.chat_active_frame, fg_color="transparent")
        self.messages_scroll.grid(row=2, column=0, sticky="nsew", padx=12, pady=6)
        self.messages_scroll.grid_columnconfigure(0, weight=1)

        # 3. Bottom Input Bar (Row 3) (Xanh đen #10192C)
        self.input_bar = ctk.CTkFrame(self.chat_active_frame, height=56, corner_radius=0, fg_color=("#FFFFFF", "#10192C"))
        self.input_bar.grid(row=3, column=0, sticky="ew")

        # Khung hiển thị Trả lời (Reply Bar - ẩn mặc định)
        self.reply_bar = ctk.CTkFrame(self.input_bar, fg_color=("#EFF6FF", "#1E3A8A"), corner_radius=6)
        reply_inner = ctk.CTkFrame(self.reply_bar, fg_color="transparent")
        reply_inner.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(reply_inner, text="↩️", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 6))
        self.lbl_reply_preview = ctk.CTkLabel(
            reply_inner,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("#1D4ED8", "#93C5FD"),
            anchor="w"
        )
        self.lbl_reply_preview.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            reply_inner,
            text="✕",
            width=22,
            height=22,
            corner_radius=11,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="transparent",
            text_color=("#1D4ED8", "#93C5FD"),
            hover_color=("#DBEAFE", "#1E40AF"),
            command=self._cancel_reply
        ).pack(side="right")

        # Toast banner màu cam nhấp nháy/hiển thị nhẹ nhàng khi mạng chập chờn (không bật popup cản trở)
        self.toast_banner = ctk.CTkFrame(self.input_bar, fg_color=("#FEF3C7", "#78350F"), corner_radius=6)
        self.toast_label = ctk.CTkLabel(
            self.toast_banner,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#B45309", "#FDE68A")
        )
        self.toast_label.pack(side="left", padx=10, pady=3)

        # Popup Frame Bảng Emoji Đầy Đủ (Ẩn mặc định, hiển thị nổi khi bấm 😃)
        self.emoji_picker_popup = None

        # Input row
        self.input_row = ctk.CTkFrame(self.input_bar, fg_color="transparent")
        self.input_row.pack(fill="x", padx=14, pady=(8, 10))
        input_row = self.input_row

        # Nút Đính kèm tệp / ảnh
        self.btn_attach = ctk.CTkButton(
            input_row,
            text="📎",
            width=38,
            height=38,
            font=ctk.CTkFont(size=16),
            fg_color=("gray85", "#1E293B"),
            hover_color=("gray75", "#334155"),
            text_color=("black", "white"),
            corner_radius=8,
            command=self.pick_and_send_file
        )
        self.btn_attach.pack(side="left", padx=(0, 6))

        # Entry soạn tin nhắn
        self.msg_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Nhập tin nhắn... (Nhấn Enter để gửi)",
            height=38,
            corner_radius=8,
            fg_color=("#F8FAFC", "#1E293B"),
            text_color=("black", "white"),
            font=ctk.CTkFont(family="Segoe UI", size=13)
        )
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.msg_entry.bind("<Return>", lambda e: self.send_text_message())
        self.msg_entry.bind("<Key>", self._on_key_typing)
        self.msg_entry.bind("<Up>", self._on_msg_entry_up_arrow)

        # Nút mở bảng Emoji (😃) phong cách Telegram/Zalo
        self.btn_all_emojis = ctk.CTkButton(
            input_row,
            text="😃",
            width=38,
            height=38,
            font=ctk.CTkFont(size=17),
            fg_color=("gray85", "#1E293B"),
            hover_color=("gray75", "#334155"),
            corner_radius=8,
            command=self.toggle_emoji_picker
        )
        self.btn_all_emojis.pack(side="left", padx=(0, 6))

        # Nút Gửi màu xanh dương (#2563EB)
        self.btn_send = ctk.CTkButton(
            input_row,
            text="Gửi ➤",
            width=76,
            height=38,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            corner_radius=8,
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
            x = max(10, self.btn_all_emojis.winfo_rootx() - 260)
            y = max(10, self.btn_all_emojis.winfo_rooty() - 370)
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

        convs_to_show = [c for c in self.conversations if c.get("type") != "saved"] if self.conversations else []
        if not convs_to_show:
            # Hai cuộc hội thoại mẫu chuẩn theo thiết kế giao diện
            sample_name = self.current_user.get("full_name") or "Vũ Duy Thái Sơn"
            convs_to_show = [
                {
                    "id": "sample_group_1",
                    "title": "test btl",
                    "type": "group",
                    "avatar_color": "#06B6D4",
                    "member_count": 3,
                    "last_message": {
                        "sender_name": sample_name,
                        "content": "hú hú"
                    }
                },
                {
                    "id": "sample_direct_2",
                    "title": "Pham Duc Tam",
                    "type": "direct",
                    "avatar_color": "#2563EB",
                    "is_online": 1,
                    "partner_id": 9999,
                    "last_message": {
                        "sender_name": sample_name,
                        "content": "đéo cần"
                    }
                }
            ]

        for conv in convs_to_show:
            conv_id = conv["id"]
            is_active = (conv_id == self.active_conv_id)

            # Card hội thoại chuẩn màu #202C40, hover #2A3B58, active #2D4365
            normal_bg = ("#FFFFFF", "#202C40")
            hover_bg = ("#F1F5F9", "#2A3B58")
            active_bg = ("#DBEAFE", "#2D4365")
            bg_col = active_bg if is_active else normal_bg

            card = ctk.CTkFrame(self.conv_scroll, corner_radius=10, fg_color=bg_col, cursor="hand2")
            card.pack(fill="x", pady=4, padx=4)
            self.conv_widgets[conv_id] = card

            # Hover highlight
            def _on_enter(e, c=card, active=is_active, h_col=hover_bg):
                if not active:
                    c.configure(fg_color=h_col)
            def _on_leave(e, c=card, active=is_active, n_col=normal_bg):
                if not active:
                    c.configure(fg_color=n_col)
            card.bind("<Enter>", _on_enter)
            card.bind("<Leave>", _on_leave)

            # Click event
            card.bind("<Button-1>", lambda e, c=conv: self.select_conversation(c))

            row_f = ctk.CTkFrame(card, fg_color="transparent")
            row_f.pack(fill="x", padx=10, pady=8)
            row_f.bind("<Button-1>", lambda e, c=conv: self.select_conversation(c))

            # Avatar
            if conv.get("type") == "group":
                av_text = "👥"
                av_col = conv.get("avatar_color", "#06B6D4")
            else:
                av_text = conv["title"][:1].upper()
                av_col = conv.get("avatar_color", "#2563EB")

            av_btn = ctk.CTkButton(
                row_f,
                text=av_text,
                width=40,
                height=40,
                corner_radius=20,
                fg_color=av_col,
                text_color="white",
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
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

            # Tên hội thoại in đậm
            lbl_title = ctk.CTkLabel(
                title_row,
                text=conv["title"],
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color=("black", "white"),
                anchor="w"
            )
            lbl_title.pack(side="left")
            lbl_title.bind("<Button-1>", lambda e, c=conv: self.select_conversation(c))

            # Chấm online nếu là 1-1
            if conv.get("type") == "direct" and conv.get("is_online"):
                dot = ctk.CTkLabel(title_row, text=" 🟢", font=ctk.CTkFont(size=9))
                dot.pack(side="left")
                dot.bind("<Button-1>", lambda e, c=conv: self.select_conversation(c))

            # Tin nhắn gần nhất màu xám
            last_msg = conv.get("last_message")
            if last_msg:
                snippet = f"{last_msg.get('sender_name', '')}: {last_msg.get('content', '')}"
                if len(snippet) > 32:
                    snippet = snippet[:32] + "..."
            else:
                snippet = "Chưa có tin nhắn..."

            lbl_snip = ctk.CTkLabel(
                text_box,
                text=snippet,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=("#64748B", "#94A3B8"),
                anchor="w"
            )
            lbl_snip.pack(fill="x", pady=(2, 0))
            lbl_snip.bind("<Button-1>", lambda e, c=conv: self.select_conversation(c))
            self._bind_conv_context_menu(card, conv)

    def select_conversation(self, conv: dict):
        self.active_conv_id = conv["id"]
        self.active_conv_data = conv

        # Ẩn empty state, hiện chat active frame
        self.empty_state.place_forget()
        self.chat_active_frame.grid(row=0, column=0, sticky="nsew")

        # Cập nhật Header
        self.lbl_chat_title.configure(text=conv["title"])
        self.btn_chat_options.pack(side="right", padx=(6, 0))
        self.btn_info.pack(side="right", padx=(0, 6))
        self.btn_popout.pack(side="right", padx=(0, 6))

        # Hiển thị hoặc ẩn nút gọi điện (chỉ áp dụng cho trò chuyện 1-1)
        if conv.get("type") == "direct":
            self.btn_call_voice.pack(side="right", padx=(0, 6))
            self.btn_call_video.pack(side="right", padx=(0, 6))
        else:
            self.btn_call_voice.pack_forget()
            self.btn_call_video.pack_forget()

        if conv["type"] == "group":
            count = conv.get("member_count", 2)
            self.lbl_chat_subtitle.configure(text=f"👥 Nhóm trò chuyện  •  {count} thành viên")
            self.active_partner_friend_status = None
            self.active_partner_blocked = False
        elif conv["type"] == "saved":
            self.lbl_chat_subtitle.configure(text="☁️ Không gian lưu trữ dữ liệu & tin nhắn cá nhân")
            self.active_partner_friend_status = None
            self.active_partner_blocked = False
        else:
            is_on = conv.get("is_online", 0)
            status_text = "🟢 Trực tuyến" if is_on else "⚪ Ngoại tuyến"
            self.lbl_chat_subtitle.configure(text=status_text)

            # Kiểm tra trạng thái bạn bè và chặn
            partner_id = conv.get("partner_id")
            if partner_id:
                self.active_partner_friend_status = "friends" if any(f.get("id") == partner_id for f in self.friends) else "none"
                self.active_partner_blocked = False
                self._update_header_friend_status(partner_id)
                self._update_header_block_status(partner_id)
            else:
                self.active_partner_friend_status = None
                self.active_partner_blocked = False

        # Reset thanh trả lời và ẩn ghim cũ
        self._cancel_reply()
        self.current_pinned_message = None
        self.pinned_banner.grid_forget()

        # Tải tin nhắn đã ghim nếu có
        conv_id = conv["id"]
        def _fetch_pinned():
            res = self.net.get_pinned_message(conv_id)
            if res and res.get("pinned"):
                def _apply():
                    if self.active_conv_id == conv_id:
                        self.current_pinned_message = res.get("pinned")
                        self._render_pinned_banner()
                self.master.after(0, _apply)
        threading.Thread(target=_fetch_pinned, daemon=True).start()

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
                self.active_partner_friend_status = st
            self.master.after(0, _apply)
        threading.Thread(target=_check, daemon=True).start()

    def _show_chat_options_menu(self, event=None):
        """Hiển thị menu ngữ cảnh tùy chọn cuộc trò chuyện khi bấm nút '...'"""
        if not self.active_conv_data:
            return

        conv = self.active_conv_data
        partner_id = conv.get("partner_id")

        import tkinter as tk
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = "#1E293B" if is_dark else "#FFFFFF"
        fg_color = "#F8FAFC" if is_dark else "#0F172A"
        active_bg = "#334155" if is_dark else "#E2E8F0"
        active_fg = "#38BDF8" if is_dark else "#0284C7"

        menu = tk.Menu(
            self.master,
            tearoff=0,
            bg=bg_color,
            fg=fg_color,
            activebackground=active_bg,
            activeforeground=active_fg,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1
        )

        if conv.get("type") == "direct" and partner_id:
            # 1. Trạng thái Bạn bè
            st = getattr(self, "active_partner_friend_status", "none")
            if st == "none" and any(f.get("id") == partner_id for f in self.friends):
                st = "friends"

            if st == "friends":
                menu.add_command(
                    label="⭐ Xóa khỏi danh bạ bạn bè",
                    command=self.toggle_contact_friend
                )
            elif st == "sent_pending":
                menu.add_command(
                    label="⏳ Đã gửi lời mời (Chờ duyệt)",
                    state="disabled"
                )
            elif st == "received_pending":
                menu.add_command(
                    label="✅ Đồng ý kết bạn",
                    command=self.toggle_contact_friend
                )
            else:
                menu.add_command(
                    label="➕ Thêm vào danh bạ bạn bè",
                    command=self.toggle_contact_friend
                )

            # 2. Trạng thái Chặn / Bỏ chặn
            is_blocked = getattr(self, "active_partner_blocked", False)
            if is_blocked:
                menu.add_command(
                    label="🔓 Bỏ chặn người dùng này",
                    command=lambda: self.toggle_block_user(partner_id)
                )
            else:
                menu.add_command(
                    label="🚫 Chặn người dùng này",
                    command=lambda: self.toggle_block_user(partner_id)
                )

            menu.add_separator()

        # 3. Xóa cuộc trò chuyện
        menu.add_command(
            label="🗑️ Xóa cuộc trò chuyện",
            command=self.delete_current_conversation
        )

        try:
            if event and hasattr(event, 'x_root') and hasattr(event, 'y_root'):
                x, y = event.x_root, event.y_root
            else:
                self.btn_chat_options.update_idletasks()
                x = self.btn_chat_options.winfo_rootx()
                y = self.btn_chat_options.winfo_rooty() + self.btn_chat_options.winfo_height() + 4
            menu.tk_popup(x, y)
        except Exception:
            pass

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
        # Hỗ trợ hiển thị tin nhắn mẫu trực quan cho các hội thoại demo
        if str(conv_id).startswith("sample_"):
            sender_name = self.current_user.get("full_name") or "Vũ Duy Thái Sơn"
            if conv_id == "sample_group_1":
                sample_msgs = [
                    {
                        "id": 99901,
                        "sender_id": 9999,
                        "sender_name": "Pham Duc Tam",
                        "content": "Alo anh em, chuẩn bị báo cáo tiến độ nhé!",
                        "message_type": "text",
                        "created_at": "10:28"
                    },
                    {
                        "id": 99902,
                        "sender_id": self.current_user["id"],
                        "sender_name": sender_name,
                        "content": "hú hú",
                        "message_type": "text",
                        "created_at": "10:30"
                    }
                ]
            else:
                sample_msgs = [
                    {
                        "id": 99903,
                        "sender_id": 9999,
                        "sender_name": "Pham Duc Tam",
                        "content": "M cần hỗ trợ phần giao diện hay database không?",
                        "message_type": "text",
                        "created_at": "10:29"
                    },
                    {
                        "id": 99904,
                        "sender_id": self.current_user["id"],
                        "sender_name": sender_name,
                        "content": "đéo cần",
                        "message_type": "text",
                        "created_at": "10:30"
                    }
                ]
            self._render_messages(sample_msgs)
            return

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
        self.msg_bubbles = {}

        for msg in messages:
            m_id = msg.get("id")
            if m_id:
                self.rendered_msg_ids.add(m_id)
            bubble = ChatBubble(
                self.messages_scroll,
                msg,
                self.current_user["id"],
                self.net,
                on_recall_callback=self.recall_message,
                on_reply_callback=self._set_reply_target,
                on_reaction_callback=self._on_bubble_reaction,
                on_pin_callback=self._on_bubble_pin
            )
            bubble.pack(fill="x")
            if m_id:
                self.msg_bubbles[m_id] = bubble

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
        reply_id = self.reply_target_message.get("id") if self.reply_target_message else None
        self._cancel_reply()

        # Hỗ trợ gửi tin nhắn trực tiếp trong hội thoại mẫu
        if str(self.active_conv_id).startswith("sample_"):
            new_msg = {
                "id": int(time.time()),
                "sender_id": self.current_user["id"],
                "sender_name": self.current_user.get("full_name") or "Vũ Duy Thái Sơn",
                "content": content,
                "message_type": "text",
                "created_at": time.strftime("%H:%M")
            }
            bubble = ChatBubble(
                self.messages_scroll,
                new_msg,
                self.current_user["id"],
                self.net,
                on_recall_callback=self.recall_message,
                on_reply_callback=self._set_reply_target,
                on_reaction_callback=self._on_bubble_reaction,
                on_pin_callback=self._on_bubble_pin
            )
            bubble.pack(fill="x")
            self._scroll_to_bottom()
            return

        def _send():
            ok = self.net.send_message(self.active_conv_id, self.current_user["id"], content, msg_type="text", reply_to_id=reply_id)
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
        reply_id = self.reply_target_message.get("id") if self.reply_target_message else None
        self._cancel_reply()

        def _upload():
            res = self.net.upload_file(self.active_conv_id, self.current_user["id"], filepath, reply_to_id=reply_id)
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
                bubble = ChatBubble(
                    self.messages_scroll,
                    msg,
                    self.current_user["id"],
                    self.net,
                    on_recall_callback=self.recall_message,
                    on_reply_callback=self._set_reply_target,
                    on_reaction_callback=self._on_bubble_reaction,
                    on_pin_callback=self._on_bubble_pin
                )
                bubble.pack(fill="x")
                if msg_id:
                    self.msg_bubbles[msg_id] = bubble
                self._scroll_to_bottom()
            self.master.after(0, _add)

        # Tải lại danh sách bên trái để cập nhật snippet và vị trí
        self.master.after(0, self.load_conversations)

        # Thông báo Toast Desktop & Cập nhật số tin chưa đọc trên Khay hệ thống
        sender_id = msg.get("sender_id")
        if sender_id != self.current_user["id"]:
            sender_name = msg.get("sender_name", "Tin nhắn mới")
            content = msg.get("content") or msg.get("original_name") or "Đã gửi một tệp tin"
            avatar_col = msg.get("avatar_color", "#2563EB")
            def _toast():
                try:
                    ToastNotification(
                        self.master,
                        title=sender_name,
                        message=content,
                        avatar_color=avatar_col,
                        on_click=lambda cid=conv_id: self.select_conversation(self._find_conversation_by_id(cid))
                    )
                except Exception:
                    pass
            self.master.after(0, _toast)

            # Cập nhật số đếm khay hệ thống (System Tray)
            if hasattr(self.master, "tray") and self.master.tray:
                self.master.tray.update_tray(self.master.tray.unread_count + 1)

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

    # --- TÍNH NĂNG THU HỒI TIN NHẮN, XÓA ĐOẠN CHAT & CHẶN NGƯỜI DÙNG ---
    def recall_message(self, message_id: int):
        """Yêu cầu máy chủ thu hồi tin nhắn ở cả hai phía."""
        def _do_recall():
            res = self.net.recall_message(message_id, self.current_user["id"])
            if res and res.get("success"):
                def _ui():
                    if message_id in self.msg_bubbles:
                        self.msg_bubbles[message_id].mark_as_recalled()
                    self._show_toast("✅ Đã thu hồi tin nhắn thành công!")
                self.master.after(0, _ui)
            else:
                err = res.get("message", "Thu hồi tin nhắn thất bại!") if res else "Không thể kết nối máy chủ!"
                self.master.after(0, lambda: messagebox.showerror("Lỗi", err))
        threading.Thread(target=_do_recall, daemon=True).start()

    def _on_message_recalled(self, packet: dict):
        """Xử lý sự kiện tin nhắn bị thu hồi từ thành viên khác trong phòng."""
        conv_id = packet.get("conversation_id")
        msg_id = packet.get("message_id")
        if self.active_conv_id == conv_id and msg_id in self.msg_bubbles:
            self.master.after(0, lambda: self.msg_bubbles[msg_id].mark_as_recalled())
        self.master.after(0, self.load_conversations)

    def delete_current_conversation(self):
        """Xóa cuộc trò chuyện đang mở."""
        if not self.active_conv_id:
            return
        conv_id = self.active_conv_id
        title = self.active_conv_data.get("title", "cuộc trò chuyện này") if self.active_conv_data else "cuộc trò chuyện này"
        if not messagebox.askyesno("Xác nhận xóa đoạn chat", f"Bạn có chắc chắn muốn xóa toàn bộ đoạn chat '{title}' không?\nTất cả lịch sử tin nhắn sẽ bị xóa vĩnh viễn và không thể khôi phục."):
            return
        self.delete_conversation_by_id(conv_id)

    def delete_conversation_by_id(self, conv_id: int):
        """Gửi yêu cầu xóa cuộc trò chuyện lên máy chủ."""
        def _do_del():
            res = self.net.delete_conversation(conv_id, self.current_user["id"])
            if res and res.get("success"):
                def _ui():
                    if self.active_conv_id == conv_id:
                        self.active_conv_id = None
                        self.active_conv_data = None
                        self.chat_active_frame.grid_forget()
                        self.empty_state.place(relx=0.5, rely=0.5, anchor="center")
                    self._show_toast("🗑️ Đã xóa đoạn chat thành công!")
                    self.load_conversations()
                self.master.after(0, _ui)
            else:
                err = res.get("message", "Xóa đoạn chat thất bại!") if res else "Không thể kết nối máy chủ!"
                self.master.after(0, lambda: messagebox.showerror("Lỗi", err))
        threading.Thread(target=_do_del, daemon=True).start()

    def _on_conversation_deleted(self, packet: dict):
        """Xử lý sự kiện cuộc trò chuyện đã bị xóa."""
        conv_id = packet.get("conversation_id")
        if self.active_conv_id == conv_id:
            def _close():
                self.active_conv_id = None
                self.active_conv_data = None
                self.chat_active_frame.grid_forget()
                self.empty_state.place(relx=0.5, rely=0.5, anchor="center")
                self._show_toast("ℹ️ Cuộc trò chuyện này đã bị xóa.")
            self.master.after(0, _close)
        self.master.after(0, self.load_conversations)

    def toggle_block_user(self, target_id=None):
        """Chặn hoặc bỏ chặn người dùng."""
        if not target_id:
            if not self.active_conv_data or self.active_conv_data.get("type") != "direct":
                return
            target_id = self.active_conv_data.get("partner_id")
        if not target_id:
            return

        def _work():
            status_res = self.net.get_block_status(self.current_user["id"], target_id)
            is_blocked = status_res.get("is_blocked_by_me", False) if status_res else False

            if is_blocked:
                # Thực hiện bỏ chặn
                res = self.net.unblock_user(self.current_user["id"], target_id)
                if res and res.get("success"):
                    self.master.after(0, lambda: (
                        self._show_toast("✅ Đã bỏ chặn người dùng thành công!"),
                        self._update_header_block_status(target_id)
                    ))
                else:
                    self.master.after(0, lambda: messagebox.showerror("Lỗi", "Bỏ chặn thất bại!"))
            else:
                # Thực hiện chặn
                def _confirm_and_block():
                    if messagebox.askyesno("Xác nhận chặn người dùng", "Sau khi chặn, người này sẽ không thể gửi tin nhắn cho bạn nữa.\nBạn có chắc chắn muốn chặn?"):
                        def _do_block():
                            res = self.net.block_user(self.current_user["id"], target_id)
                            if res and res.get("success"):
                                self.master.after(0, lambda: (
                                    self._show_toast("🚫 Đã chặn người dùng thành công!"),
                                    self._update_header_block_status(target_id)
                                ))
                            else:
                                self.master.after(0, lambda: messagebox.showerror("Lỗi", "Chặn người dùng thất bại!"))
                        threading.Thread(target=_do_block, daemon=True).start()
                self.master.after(0, _confirm_and_block)
        threading.Thread(target=_work, daemon=True).start()

    def _update_header_block_status(self, partner_id: int):
        """Cập nhật giao diện nút Chặn / Bỏ chặn trên Header."""
        def _check():
            res = self.net.get_block_status(self.current_user["id"], partner_id)
            if not res:
                return
            is_by_me = res.get("is_blocked_by_me", False)
            def _apply():
                self.active_partner_blocked = is_by_me
            self.master.after(0, _apply)
        threading.Thread(target=_check, daemon=True).start()

    def _on_block_status_changed(self, packet: dict):
        """Nhận sự kiện thay đổi trạng thái chặn."""
        if self.active_conv_data and self.active_conv_data.get("type") == "direct":
            partner_id = self.active_conv_data.get("partner_id")
            if partner_id in [packet.get("user_id"), packet.get("target_id")]:
                self.master.after(0, lambda: self._update_header_block_status(partner_id))

    def _bind_conv_context_menu(self, widget, conv: dict):
        """Gắn menu ngữ cảnh chuột phải vào mục hội thoại trong danh sách."""
        def _popup(e):
            try:
                import tkinter as tk
                menu = tk.Menu(self.master, tearoff=0)
                menu.add_command(label="💬 Mở cuộc trò chuyện", command=lambda: self.select_conversation(conv))
                menu.add_separator()
                if conv.get("type") == "direct" and conv.get("partner_id"):
                    pid = conv["partner_id"]
                    menu.add_command(label="🚫 Chặn / Bỏ chặn người này", command=lambda: self.toggle_block_user(pid))
                menu.add_command(label="🗑️ Xóa đoạn chat này", command=lambda: self.delete_conversation_by_id(conv["id"]))
                menu.tk_popup(e.x_root, e.y_root)
            except Exception:
                pass
        try:
            widget.bind("<Button-3>", _popup)
            for child in widget.winfo_children():
                self._bind_conv_context_menu(child, conv)
        except Exception:
            pass

    def _bind_friend_context_menu(self, widget, friend: dict):
        """Gắn menu ngữ cảnh chuột phải vào bạn bè trong danh bạ."""
        def _popup(e):
            try:
                import tkinter as tk
                menu = tk.Menu(self.master, tearoff=0)
                menu.add_command(label=f"💬 Nhắn tin với {friend['full_name']}", command=lambda: self.start_direct_chat_with(friend["id"]))
                menu.add_separator()
                menu.add_command(label="🚫 Chặn / Bỏ chặn bạn này", command=lambda: self.toggle_block_user(friend["id"]))
                menu.add_command(label="✕ Xóa khỏi danh bạ", command=lambda: self._confirm_remove_friend(friend["id"]))
                menu.tk_popup(e.x_root, e.y_root)
            except Exception:
                pass
        try:
            widget.bind("<Button-3>", _popup)
            for child in widget.winfo_children():
                self._bind_friend_context_menu(child, friend)
        except Exception:
            pass

    # --- TÌM KIẾM NGƯỜI DÙNG & TẠO CHAT 1-1 ---
    def _on_search_key(self, event):
        kw = self.search_entry.get().strip()
        if not kw:
            self.search_results_frame.grid_forget()
            if getattr(self, "current_sidebar_tab", "chats") == "chats":
                self.conv_scroll.grid(row=3, column=0, sticky="nsew", padx=6, pady=(0, 6))
            else:
                self.friends_scroll.grid(row=3, column=0, sticky="nsew", padx=6, pady=(0, 6))
            return

        search_kw = kw.lstrip("@#").strip()
        if not search_kw:
            self.search_results_frame.grid_forget()
            if getattr(self, "current_sidebar_tab", "chats") == "chats":
                self.conv_scroll.grid(row=3, column=0, sticky="nsew", padx=6, pady=(0, 6))
            else:
                self.friends_scroll.grid(row=3, column=0, sticky="nsew", padx=6, pady=(0, 6))
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
        self.conv_scroll.grid_forget()
        self.friends_scroll.grid_forget()
        self.search_results_frame.grid(row=3, column=0, sticky="nsew", padx=6, pady=(0, 6))
        ctk.CTkLabel(self.search_results_frame, text=message, font=ctk.CTkFont(size=11), text_color="#EF4444").pack(pady=20)

    def _show_search_results(self, users: list):
        for w in self.search_results_frame.winfo_children():
            w.destroy()

        self.conv_scroll.grid_forget()
        self.friends_scroll.grid_forget()
        self.search_results_frame.grid(row=3, column=0, sticky="nsew", padx=6, pady=(0, 6))

        if not users:
            ctk.CTkLabel(
                self.search_results_frame,
                text="🔍 Không tìm thấy người dùng phù hợp.",
                font=ctk.CTkFont(size=12),
                text_color="gray60"
            ).pack(pady=30)
            return

        ctk.CTkLabel(
            self.search_results_frame,
            text=f"KẾT QUẢ TÌM KIẾM ({len(users)}):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#0284C7"
        ).pack(anchor="w", padx=6, pady=(6, 4))

        for u in users:
            card = ctk.CTkFrame(self.search_results_frame, corner_radius=10, fg_color=("white", "#1E293B"))
            card.pack(fill="x", pady=3, padx=2)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=8)

            # Avatar
            ctk.CTkButton(
                row,
                text=u["full_name"][:1].upper(),
                width=34,
                height=34,
                corner_radius=17,
                fg_color=u.get("avatar_color", "#0284C7"),
                font=ctk.CTkFont(size=12, weight="bold"),
                state="disabled"
            ).pack(side="left", padx=(0, 8))

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)

            t_row = ctk.CTkFrame(info, fg_color="transparent")
            t_row.pack(anchor="w")
            ctk.CTkLabel(t_row, text=u["full_name"], font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            if u.get("is_online"):
                ctk.CTkLabel(t_row, text=" 🟢", font=ctk.CTkFont(size=9)).pack(side="left")

            ctk.CTkLabel(info, text=f"@{u['username']} • #{u['id']}", font=ctk.CTkFont(size=10), text_color="gray50").pack(anchor="w")

            btn_box = ctk.CTkFrame(row, fg_color="transparent")
            btn_box.pack(side="right")

            ctk.CTkButton(
                btn_box,
                text="💬 Nhắn",
                width=55,
                height=28,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#0284C7",
                hover_color="#0369A1",
                command=lambda uid=u["id"]: self.start_direct_chat_with(uid)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                btn_box,
                text="➕ Bạn",
                width=50,
                height=28,
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
            self._bind_friend_context_menu(card, fr)

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
                self.net.remove_friend(self.current_user["id"], friend_id)
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
                        # Đồng bộ trạng thái tin nhắn đã thu hồi
                        for m in new_msgs:
                            m_id = m.get("id")
                            if m_id and m.get("is_deleted") and m_id in self.msg_bubbles:
                                bubble = self.msg_bubbles[m_id]
                                if not bubble.message.get("is_deleted"):
                                    self.master.after(0, bubble.mark_as_recalled)

                        missing_msgs = [m for m in new_msgs if m.get("id") and m.get("id") not in self.rendered_msg_ids]
                        if missing_msgs:
                            def _append_missing(msgs=missing_msgs):
                                for m in msgs:
                                    m_id = m.get("id")
                                    if m_id:
                                        self.rendered_msg_ids.add(m_id)
                                    bubble = ChatBubble(
                                        self.messages_scroll,
                                        m,
                                        self.current_user["id"],
                                        self.net,
                                        on_recall_callback=self.recall_message,
                                        on_reply_callback=self._set_reply_target,
                                        on_reaction_callback=self._on_bubble_reaction,
                                        on_pin_callback=self._on_bubble_pin
                                    )
                                    bubble.pack(fill="x")
                                    if m_id:
                                        self.msg_bubbles[m_id] = bubble
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
        # Tránh người dùng bấm spam nút tạo nhóm mở nhiều modal đè nhau
        if getattr(self, "_group_dialog", None) and self._group_dialog.winfo_exists():
            return
        self._group_dialog = CreateGroupDialog(self, self.current_user, self.net, on_group_created=self._on_group_created)

    def _on_group_created(self, conv_id):
        self.load_conversations()
        self._show_toast("👥 Đã tạo nhóm trò chuyện mới thành công!")
        if conv_id:
            def _select_new():
                for c in self.conversations:
                    if c.get("id") == conv_id:
                        self.select_conversation(c)
                        break
            self.after(300, _select_new)

    # --- TÍNH NĂNG TRẢ LỜI (REPLY), THẢ CẢM XÚC (REACTIONS) & GHIM TIN NHẮN (PIN) ---
    def _set_reply_target(self, msg: dict):
        self.reply_target_message = msg
        sender = msg.get("sender_name", "Tin nhắn")
        content = msg.get("content", "")
        if msg.get("message_type") in ("image", "file"):
            content = f"[{msg.get('file_name', 'Tệp đính kèm')}]"
        snip = content[:50] + "..." if len(content) > 50 else content
        self.lbl_reply_preview.configure(text=f"Đang trả lời {sender}: {snip}")
        self.reply_bar.pack(fill="x", padx=14, pady=(2, 2), before=self.input_row)
        self.msg_entry.focus_set()

    def _cancel_reply(self):
        self.reply_target_message = None
        try:
            self.reply_bar.pack_forget()
        except Exception:
            pass

    def _on_bubble_reaction(self, message_id: int, reaction: str):
        if not self.active_conv_id:
            return
        conv_id = self.active_conv_id
        def _do():
            self.net.toggle_reaction(conv_id, message_id, self.current_user["id"], reaction)
        threading.Thread(target=_do, daemon=True).start()

    def _on_reaction_updated(self, packet: dict):
        msg_id = packet.get("message_id")
        reactions = packet.get("reactions", [])
        if msg_id and msg_id in self.msg_bubbles:
            def _update():
                if msg_id in self.msg_bubbles:
                    self.msg_bubbles[msg_id].update_reactions(reactions)
            self.master.after(0, _update)

    def _on_bubble_pin(self, message_id: int):
        if not self.active_conv_id:
            return
        conv_id = self.active_conv_id
        is_pinned = self.current_pinned_message and self.current_pinned_message.get("id") == message_id
        def _do():
            if is_pinned:
                self.net.unpin_message(conv_id)
            else:
                self.net.pin_message(conv_id, message_id, self.current_user["id"])
        threading.Thread(target=_do, daemon=True).start()

    def unpin_current_message(self):
        if not self.active_conv_id:
            return
        conv_id = self.active_conv_id
        threading.Thread(target=lambda: self.net.unpin_message(conv_id), daemon=True).start()

    def _render_pinned_banner(self):
        if self.current_pinned_message:
            sender = self.current_pinned_message.get("sender_name", "")
            content = self.current_pinned_message.get("content", "")
            if len(content) > 60:
                content = content[:60] + "..."
            self.lbl_pinned_text.configure(text=f"📌 Đã ghim ({sender}): {content}")
            self.pinned_banner.grid(row=1, column=0, sticky="ew")
        else:
            self.pinned_banner.grid_forget()

    def _on_pinned_updated(self, packet: dict):
        conv_id = packet.get("conversation_id")
        if self.active_conv_id == conv_id:
            self.current_pinned_message = packet.get("pinned")
            self.master.after(0, self._render_pinned_banner)

    # --- TÍNH NĂNG CLOUD CỦA TÔI (SAVED MESSAGES) ---
    def open_saved_messages(self):
        def _do():
            res = self.net.get_saved_conversation(self.current_user["id"])
            if res and res.get("conversation_id"):
                conv_id = res.get("conversation_id")
                saved_conv = next((c for c in self.conversations if c["id"] == conv_id), None)
                if not saved_conv:
                    saved_conv = {
                        "id": conv_id,
                        "title": "Cloud của tôi (Lưu trữ cá nhân)",
                        "type": "saved",
                        "avatar_color": "#4F46E5",
                        "partner_id": None
                    }
                    self.conversations.insert(0, saved_conv)
                def _sel():
                    self.select_conversation(saved_conv)
                self.master.after(0, _sel)
        threading.Thread(target=_do, daemon=True).start()

    # --- TÍNH NĂNG CUỘC GỌI THOẠI & CUỘC GỌI VIDEO (VOICE & VIDEO CALL) ---
    def start_call(self, call_type="voice"):
        if not self.active_conv_data:
            self._show_toast("⚠️ Vui lòng chọn một cuộc trò chuyện để gọi!")
            return
        if self.active_conv_data.get("type") == "saved":
            self._show_toast("⚠️ Không thể gọi thoại trên không gian lưu trữ Cloud của tôi!")
            return
        if self.active_conv_data.get("type") == "group":
            self._show_toast("ℹ️ Chức năng gọi hiện hỗ trợ trên cuộc trò chuyện 1-1!")
            return
        partner_id = self.active_conv_data.get("partner_id")
        if not partner_id:
            self._show_toast("⚠️ Không tìm thấy đối phương để gọi!")
            return
        if self.active_call_window and self.active_call_window.running:
            self._show_toast("⚠️ Bạn đang trong một cuộc gọi khác!")
            return

        type_text = "cuộc gọi video" if call_type == "video" else "cuộc gọi thoại"
        self._show_toast(f"📞 Đang khởi tạo {type_text}...")

        def _do_invite():
            res = self.net.call_invite(
                caller_id=self.current_user["id"],
                receiver_id=partner_id,
                call_type=call_type,
                conversation_id=self.active_conv_id
            )
            def _apply():
                if res and res.get("success"):
                    channel_id = res.get("channel_id")
                    self.active_call_window = ActiveCallWindow(
                        master=self.master,
                        channel_id=channel_id,
                        current_user_id=self.current_user["id"],
                        partner_name=self.active_conv_data.get("title", "Người dùng"),
                        partner_avatar_color=self.active_conv_data.get("avatar_color", "#2563EB"),
                        call_type=call_type,
                        network_client=self.net,
                        on_ended_cb=self._on_call_closed
                    )
                else:
                    msg = res.get("message", "Khởi tạo cuộc gọi thất bại!") if res else "Không thể kết nối máy chủ!"
                    self._show_toast(f"❌ {msg}")
            self.master.after(0, _apply)
        threading.Thread(target=_do_invite, daemon=True).start()

    def _on_call_incoming(self, packet: dict):
        def _handle():
            if self.active_call_window and self.active_call_window.running:
                self.net.call_reject(packet.get("channel_id"))
                return
            if self.incoming_call_dialog and self.incoming_call_dialog.winfo_exists():
                return
            self.incoming_call_dialog = IncomingCallDialog(
                master=self.master,
                call_info=packet,
                on_accept_cb=self._accept_incoming_call,
                on_reject_cb=self._reject_incoming_call
            )
        self.master.after(0, _handle)

    def _accept_incoming_call(self, call_info: dict):
        channel_id = call_info.get("channel_id")
        self.net.call_accept(channel_id)
        self.active_call_window = ActiveCallWindow(
            master=self.master,
            channel_id=channel_id,
            current_user_id=self.current_user["id"],
            partner_name=call_info.get("caller_name", "Người dùng"),
            partner_avatar_color=call_info.get("avatar_color", "#2563EB"),
            call_type=call_info.get("call_type", "voice"),
            network_client=self.net,
            on_ended_cb=self._on_call_closed
        )
        self.active_call_window.set_connected()

    def _reject_incoming_call(self, call_info: dict):
        channel_id = call_info.get("channel_id")
        self.net.call_reject(channel_id)
        self.incoming_call_dialog = None

    def _on_call_connected(self, packet: dict):
        def _handle():
            if self.active_call_window and self.active_call_window.channel_id == packet.get("channel_id"):
                self.active_call_window.set_connected()
        self.master.after(0, _handle)

    def _on_call_rejected(self, packet: dict):
        def _handle():
            if self.active_call_window and self.active_call_window.channel_id == packet.get("channel_id"):
                reason = packet.get("reason", "Đối phương đã từ chối cuộc gọi.")
                self._show_toast(f"📞 {reason}")
                self.active_call_window.end_call()
                self.active_call_window = None
        self.master.after(0, _handle)

    def _on_call_ended(self, packet: dict):
        def _handle():
            if self.incoming_call_dialog and self.incoming_call_dialog.winfo_exists():
                self.incoming_call_dialog.destroy()
                self.incoming_call_dialog = None
            if self.active_call_window and self.active_call_window.running:
                self.active_call_window.running = False
                self.active_call_window.destroy()
                self.active_call_window = None
                self._show_toast("📞 Cuộc gọi đã kết thúc.")
        self.master.after(0, _handle)

    def _on_call_media_relay(self, packet: dict):
        if self.active_call_window and self.active_call_window.running:
            self.active_call_window.receive_media(packet)

    def _on_call_closed(self, channel_id: str):
        self.active_call_window = None

    # --- TÍNH NĂNG DESKTOP CHUYÊN SÂU ---
    def _find_conversation_by_id(self, conv_id: int):
        for c in self.conversations:
            if c.get("id") == conv_id:
                return c
        return {"id": conv_id, "title": f"Hội thoại #{conv_id}"}

    def _on_escape_pressed(self, event=None):
        if self.info_sidebar_open:
            self.toggle_info_sidebar()
            return "break"
        if self.reply_target_message:
            self._cancel_reply()
            return "break"
        if hasattr(self, "search_entry") and self.search_entry.get():
            self.search_entry.delete(0, "end")
            self._on_search_change("")
            return "break"

    def _on_msg_entry_up_arrow(self, event=None):
        """Bấm phím mũi tên Lên khi ô nhập trống để sửa hoặc thu hồi tin nhắn gần nhất."""
        if self.msg_entry.get().strip():
            return
        if not self.active_conv_id:
            return

        my_bubbles = [b for b in self.msg_bubbles.values() if b.is_self and not b.message.get("is_deleted")]
        if my_bubbles:
            last_bubble = my_bubbles[-1]
            last_msg = last_bubble.message
            content = last_msg.get("content", "")
            if content:
                self.msg_entry.insert(0, content)
                self.msg_entry.select_range(0, "end")
                self._show_toast("✏️ Nhấn Enter để gửi lại nội dung, hoặc chuột phải vào tin để thu hồi!")
        return "break"

    def send_image_file(self, filepath: str):
        """Gửi trực tiếp hình ảnh (chụp màn hình hoặc kéo thả) vào hội thoại hiện tại."""
        if not self.active_conv_id:
            self._show_toast("⚠️ Vui lòng chọn một cuộc trò chuyện trước khi gửi ảnh!")
            return
        reply_id = self.reply_target_message.get("id") if self.reply_target_message else None
        self._cancel_reply()
        def _upload():
            self.net.upload_file(self.active_conv_id, self.current_user["id"], filepath, reply_to_id=reply_id)
        threading.Thread(target=_upload, daemon=True).start()

    def open_screenshot_tool(self):
        if hasattr(self.master, "trigger_screenshot"):
            self.master.trigger_screenshot()

    def lock_app(self):
        if hasattr(self.master, "trigger_lock"):
            self.master.trigger_lock()

    def toggle_topmost(self):
        if hasattr(self.master, "toggle_topmost"):
            is_top = self.master.toggle_topmost()
            if is_top:
                self.btn_always_on_top.configure(fg_color="#3B82F6", text_color="white", text="📌 Đã ghim")
            else:
                self.btn_always_on_top.configure(fg_color=("gray90", "#334155"), text_color=("#0F172A", "#F8FAFC"), text="📌 Ghim")

    def popout_current_conversation(self):
        """Tách cuộc trò chuyện đang xem ra một cửa sổ độc lập (Pop-out Window)."""
        if not self.active_conv_id or not self.active_conv_data:
            return
        PopoutChatWindow(
            self.master,
            self.current_user,
            self.net,
            self.active_conv_id,
            self.active_conv_data
        )

    def toggle_info_sidebar(self):
        """Bật / tắt cột thứ 3 hiển thị thông tin hội thoại, ảnh, tệp đính kèm."""
        if self.info_sidebar_open:
            if self.info_sidebar:
                self.info_sidebar.grid_forget()
            self.info_sidebar_open = False
            self.btn_info.configure(fg_color=("#F1F5F9", "#334155"), text_color=("#475569", "#94A3B8"))
        else:
            if not self.info_sidebar:
                self._build_info_sidebar()
            self.grid_columnconfigure(2, weight=0, minsize=290)
            self.info_sidebar.grid(row=1, column=2, sticky="nsew")
            self.info_sidebar_open = True
            self.btn_info.configure(fg_color="#3B82F6", text_color="white")
            self._populate_info_sidebar()

    def popout_info_window(self):
        """Mở bảng thông tin hội thoại thành một cửa sổ riêng độc lập."""
        if not self.active_conv_id or not self.active_conv_data:
            return
        if self.info_sidebar_open:
            self.toggle_info_sidebar()
        st_text = self.lbl_chat_subtitle.cget("text") if hasattr(self, "lbl_chat_subtitle") else ""
        PopoutInfoWindow(
            self.master,
            self.current_user,
            self.net,
            self.active_conv_id,
            self.active_conv_data,
            pinned_message=self.current_pinned_message,
            subtitle=st_text
        )

    def _build_info_sidebar(self):
        self.info_sidebar = ctk.CTkFrame(self, width=290, corner_radius=0, fg_color=("white", "#1E293B"))

        # Header info sidebar
        sb_header = ctk.CTkFrame(self.info_sidebar, height=45, fg_color="transparent")
        sb_header.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(sb_header, text="Thông tin hội thoại", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        btn_close = ctk.CTkButton(
            sb_header, text="✕", width=26, height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="transparent", text_color="gray60", hover_color=("gray85", "#334155"),
            command=self.toggle_info_sidebar
        )
        btn_close.pack(side="right")

        btn_pop_info = ctk.CTkButton(
            sb_header, text="🗗 Hiện riêng", width=78, height=26,
            font=ctk.CTkFont(size=11),
            fg_color=("#F1F5F9", "#334155"), text_color=("#0284C7", "#38BDF8"),
            hover_color=("#E2E8F0", "#475569"),
            command=self.popout_info_window
        )
        btn_pop_info.pack(side="right", padx=(0, 6))

        # Scrollable Content
        self.info_scroll = ctk.CTkScrollableFrame(self.info_sidebar, fg_color="transparent")
        self.info_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _populate_info_sidebar(self):
        if not self.info_sidebar or not self.active_conv_data:
            return

        for w in self.info_scroll.winfo_children():
            w.destroy()

        conv = self.active_conv_data
        title = conv.get("title", "Hội thoại")
        avatar_col = conv.get("avatar_color", "#2563EB")

        # Profile Header in Sidebar
        avatar_btn = ctk.CTkButton(
            self.info_scroll,
            text=title[:1].upper(),
            width=70, height=70,
            corner_radius=35,
            fg_color=avatar_col,
            text_color="white",
            font=ctk.CTkFont(size=26, weight="bold"),
            state="disabled"
        )
        avatar_btn.pack(pady=(10, 6))

        ctk.CTkLabel(self.info_scroll, text=title, font=ctk.CTkFont(size=15, weight="bold")).pack()

        st_text = self.lbl_chat_subtitle.cget("text")
        ctk.CTkLabel(self.info_scroll, text=st_text, font=ctk.CTkFont(size=11), text_color="gray60").pack(pady=(2, 12))

        # Quick Actions Row in Info Sidebar
        act_row = ctk.CTkFrame(self.info_scroll, fg_color="transparent")
        act_row.pack(fill="x", pady=(0, 10))

        btn_pop_info = ctk.CTkButton(act_row, text="🗗 Mở cửa sổ riêng", height=30, font=ctk.CTkFont(size=11, weight="bold"),
                                     fg_color=("#EFF6FF", "#1E3A8A"), text_color=("#2563EB", "#60A5FA"),
                                     hover_color=("#DBEAFE", "#1E40AF"),
                                     command=self.popout_info_window)
        btn_pop_info.pack(side="left", fill="x", expand=True, padx=2)

        btn_pop = ctk.CTkButton(act_row, text="💬 Tách chat", height=30, font=ctk.CTkFont(size=11),
                                fg_color=("#F1F5F9", "#334155"), text_color=("#0F172A", "#F8FAFC"),
                                hover_color=("#E2E8F0", "#475569"),
                                command=self.popout_current_conversation)
        btn_pop.pack(side="left", fill="x", expand=True, padx=2)

        # Tabview for Media, Files & Pinned
        tabs = ctk.CTkTabview(self.info_scroll, height=360)
        tabs.pack(fill="both", expand=True, pady=6)

        tab_media = tabs.add("🖼️ Ảnh")
        tab_files = tabs.add("📁 Tệp tin")
        tab_pinned = tabs.add("📌 Ghim")

        # Fetch messages to populate media and files
        conv_id = self.active_conv_id
        def _load_data():
            res = self.net.get_messages(conv_id)
            if not res or "messages" not in res:
                return
            msgs = res["messages"]
            img_msgs = [m for m in msgs if m.get("message_type") == "image"]
            file_msgs = [m for m in msgs if m.get("message_type") == "file"]

            def _render():
                # 1. Render Media Tab
                if img_msgs:
                    m_scroll = ctk.CTkScrollableFrame(tab_media, fg_color="transparent")
                    m_scroll.pack(fill="both", expand=True)
                    for im in reversed(img_msgs):
                        orig_name = im.get("original_name", "Ảnh")
                        row = ctk.CTkFrame(m_scroll, fg_color=("#F8FAFC", "#0F172A"), corner_radius=6)
                        row.pack(fill="x", pady=2, padx=2)
                        ctk.CTkLabel(row, text="🖼️", font=ctk.CTkFont(size=14)).pack(side="left", padx=6)
                        ctk.CTkLabel(row, text=orig_name[:20], font=ctk.CTkFont(size=11)).pack(side="left", fill="x", expand=True)
                        ctk.CTkButton(row, text="Tải", width=40, height=24, font=ctk.CTkFont(size=10),
                                      command=lambda fid=im.get("file_id"), fn=orig_name: self._download_file_direct(fid, fn)).pack(side="right", padx=4)
                else:
                    ctk.CTkLabel(tab_media, text="Chưa có hình ảnh nào", font=ctk.CTkFont(size=11), text_color="gray60").pack(pady=20)

                # 2. Render Files Tab
                if file_msgs:
                    f_scroll = ctk.CTkScrollableFrame(tab_files, fg_color="transparent")
                    f_scroll.pack(fill="both", expand=True)
                    for fm in reversed(file_msgs):
                        orig_name = fm.get("original_name", "Tài liệu")
                        row = ctk.CTkFrame(f_scroll, fg_color=("#F8FAFC", "#0F172A"), corner_radius=6)
                        row.pack(fill="x", pady=2, padx=2)
                        ctk.CTkLabel(row, text="📄", font=ctk.CTkFont(size=14)).pack(side="left", padx=6)
                        ctk.CTkLabel(row, text=orig_name[:18], font=ctk.CTkFont(size=11)).pack(side="left", fill="x", expand=True)
                        ctk.CTkButton(row, text="Tải", width=40, height=24, font=ctk.CTkFont(size=10),
                                      command=lambda fid=fm.get("file_id"), fn=orig_name: self._download_file_direct(fid, fn)).pack(side="right", padx=4)
                else:
                    ctk.CTkLabel(tab_files, text="Chưa có tệp tin nào", font=ctk.CTkFont(size=11), text_color="gray60").pack(pady=20)

                # 3. Render Pinned Tab
                if self.current_pinned_message:
                    pin_box = ctk.CTkFrame(tab_pinned, fg_color=("#F0FDF4", "#064E3B"), corner_radius=8)
                    pin_box.pack(fill="x", padx=4, pady=8)
                    ctk.CTkLabel(pin_box, text=f"📌 {self.current_pinned_message.get('sender_name', 'Người dùng')}:",
                                 font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=8, pady=(6, 2))
                    ctk.CTkLabel(pin_box, text=self.current_pinned_message.get("content", ""),
                                 font=ctk.CTkFont(size=11), wraplength=220, justify="left").pack(anchor="w", padx=8, pady=(0, 6))
                else:
                    ctk.CTkLabel(tab_pinned, text="Chưa có tin nhắn nào được ghim", font=ctk.CTkFont(size=11), text_color="gray60").pack(pady=20)

            self.master.after(0, _render)
        threading.Thread(target=_load_data, daemon=True).start()

    def _download_file_direct(self, file_id: int, default_name: str):
        if not file_id:
            return
        save_path = filedialog.asksaveasfilename(initialfile=default_name, title="Lưu tệp tin", defaultextension=".*")
        if not save_path:
            return
        def _task():
            res = self.net.download_file(file_id)
            if res and res.get("success"):
                import base64
                data = base64.b64decode(res.get("file_data", ""))
                with open(save_path, "wb") as f:
                    f.write(data)
                self.master.after(0, lambda: messagebox.showinfo("Thành công", f"Đã lưu tệp tại:\n{save_path}"))
            else:
                self.master.after(0, lambda: messagebox.showerror("Lỗi", "Không thể tải tệp tin!"))
        threading.Thread(target=_task, daemon=True).start()


