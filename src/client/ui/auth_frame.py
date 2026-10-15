import os
import json
import customtkinter as ctk
from typing import Callable

class AuthFrame(ctk.CTkFrame):
    def __init__(self, master, on_login_success: Callable, network_client, auto_login: bool = True):
        super().__init__(master, fg_color="transparent")
        self.on_login_success = on_login_success
        self.net = network_client
        self.auto_login = auto_login
        
        project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
        self.auth_cache_file = os.path.join(project_root, "user_credentials.json")
        self.cfg_file = os.path.join(project_root, "server_config.json")
        self.wan_info_file = os.path.join(project_root, "wan_server_info.txt")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Center card container
        self.card = ctk.CTkFrame(self, width=420, corner_radius=18, fg_color=("white", "#1E293B"))
        self.card.grid(row=0, column=0, padx=20, pady=20)
        self.card.grid_columnconfigure(0, weight=1)
        
        # Header Logo & Title
        self.logo_label = ctk.CTkLabel(
            self.card, 
            text="💬", 
            font=ctk.CTkFont(size=52)
        )
        self.logo_label.pack(pady=(28, 0))
        
        self.title_label = ctk.CTkLabel(
            self.card, 
            text="Ứng Dụng Nhắn Tin & Truyền Tin", 
            font=ctk.CTkFont(size=21, weight="bold")
        )
        self.title_label.pack(pady=(6, 2))
        
        self.sub_label = ctk.CTkLabel(
            self.card, 
            text="Hệ thống nhắn tin thời gian thực & truyền tệp tin", 
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40")
        )
        self.sub_label.pack(pady=(0, 16))
        
        # Tab View: Đăng nhập / Đăng ký
        self.tabview = ctk.CTkTabview(self.card, width=370, corner_radius=12)
        self.tabview.pack(padx=24, pady=(0, 12))
        
        self.tab_login = self.tabview.add("Đăng Nhập")
        self.tab_register = self.tabview.add("Đăng Ký")
        
        self._build_login_tab()
        self._build_register_tab()
        self._build_server_config()
        self._load_remembered_credentials()

    def _build_login_tab(self):
        tab = self.tab_login
        
        ctk.CTkLabel(tab, text="Tên đăng nhập:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(12, 2))
        self.login_user_entry = ctk.CTkEntry(tab, placeholder_text="Nhập tên đăng nhập...", height=38, corner_radius=8)
        self.login_user_entry.pack(fill="x", padx=15, pady=(0, 8))
        self.login_user_entry.bind("<Return>", lambda e: self.do_login())
        
        ctk.CTkLabel(tab, text="Mật khẩu:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(4, 2))
        self.login_pwd_entry = ctk.CTkEntry(tab, placeholder_text="Nhập mật khẩu...", show="•", height=38, corner_radius=8)
        self.login_pwd_entry.pack(fill="x", padx=15, pady=(0, 8))
        self.login_pwd_entry.bind("<Return>", lambda e: self.do_login())
        
        # Checkbox ghi nhớ đăng nhập (Mặc định tích sẵn để lần sau không phải gõ lại)
        self.remember_var = ctk.BooleanVar(value=True)
        self.remember_cb = ctk.CTkCheckBox(
            tab,
            text="Ghi nhớ đăng nhập (Tự động vào app lần sau)",
            variable=self.remember_var,
            font=ctk.CTkFont(size=12),
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=6
        )
        self.remember_cb.pack(anchor="w", padx=15, pady=(4, 8))
        
        self.login_msg_label = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=12), text_color="#EF4444")
        self.login_msg_label.pack(pady=(0, 6))
        
        self.btn_login = ctk.CTkButton(
            tab, 
            text="Đăng Nhập Ngay", 
            height=42, 
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.do_login
        )
        self.btn_login.pack(fill="x", padx=15, pady=(0, 15))

    def _build_register_tab(self):
        tab = self.tab_register
        
        ctk.CTkLabel(tab, text="Họ và tên hiển thị:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(8, 2))
        self.reg_name_entry = ctk.CTkEntry(tab, placeholder_text="Ví dụ: Nguyễn Văn A", height=36, corner_radius=8)
        self.reg_name_entry.pack(fill="x", padx=15, pady=(0, 6))
        
        ctk.CTkLabel(tab, text="Tên đăng nhập (@username duy nhất):", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(2, 2))
        self.reg_user_entry = ctk.CTkEntry(tab, placeholder_text="Ví dụ: son_nguyen hoặc nguyenvana", height=36, corner_radius=8)
        self.reg_user_entry.pack(fill="x", padx=15, pady=(0, 2))

        ctk.CTkLabel(
            tab, 
            text="* Username là duy nhất toàn hệ thống (không trùng ai, dùng để tìm kiếm)", 
            font=ctk.CTkFont(size=10),
            text_color="#0284C7"
        ).pack(anchor="w", padx=15, pady=(0, 6))
        
        ctk.CTkLabel(tab, text="Mật khẩu:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(2, 2))
        self.reg_pwd_entry = ctk.CTkEntry(tab, placeholder_text="Ví dụ: Matkhau@123", show="•", height=36, corner_radius=8)
        self.reg_pwd_entry.pack(fill="x", padx=15, pady=(0, 2))
        self.reg_pwd_entry.bind("<Return>", lambda e: self.do_register())
        
        ctk.CTkLabel(
            tab, 
            text="* Yêu cầu: >= 6 ký tự, gồm chữ hoa, thường, số & ký tự đặc biệt", 
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray40")
        ).pack(anchor="w", padx=15, pady=(0, 8))
        
        self.reg_msg_label = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=12), text_color="#EF4444")
        self.reg_msg_label.pack(pady=(0, 6))
        
        self.btn_register = ctk.CTkButton(
            tab, 
            text="Tạo Tài Khoản Mới", 
            height=40, 
            corner_radius=8,
            fg_color="#10B981", 
            hover_color="#059669",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.do_register
        )
        self.btn_register.pack(fill="x", padx=15, pady=(0, 15))

    def _load_remembered_credentials(self):
        """Tự động điền và tự động đăng nhập thẳng vào ứng dụng nếu đã đăng nhập trước đó."""
        if os.path.exists(self.auth_cache_file):
            try:
                with open(self.auth_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    u = data.get("username", "")
                    p = data.get("password", "")
                    if u and p:
                        self.login_user_entry.insert(0, u)
                        self.login_pwd_entry.insert(0, p)
                        # Tự động đăng nhập vào ứng dụng sau khi giao diện sẵn sàng (nếu không phải vừa chủ động bấm Đăng xuất)
                        if getattr(self, "auto_login", True):
                            self.after(100, self.do_login)
            except Exception:
                pass

    def _build_server_config(self):
        """Khung cấu hình địa chỉ Server để chat qua mạng LAN hoặc WAN / Internet."""
        self.show_cfg = False
        self.server_cfg_btn = ctk.CTkButton(
            self.card,
            text="⚙️ Cài đặt IP Máy chủ (LAN / WAN / Internet)",
            fg_color="transparent",
            hover_color=("gray85", "#334155"),
            text_color=("gray40", "gray60"),
            font=ctk.CTkFont(size=11),
            command=self.toggle_server_config
        )
        self.server_cfg_btn.pack(pady=(0, 14))
        
        self.server_cfg_frame = ctk.CTkFrame(self.card, fg_color=("gray95", "#0F172A"), corner_radius=8)
        
        # Tự động đọc cấu hình: Ưu tiên 127.0.0.1 nếu máy chủ local đang mở, ngược lại đọc WAN info
        saved_host = "bore.pub"
        saved_port = 38888
        
        import socket
        def _is_local_server_active():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.25)
                    return s.connect_ex(('127.0.0.1', 8888)) == 0
            except Exception:
                return False

        if _is_local_server_active():
            saved_host = "127.0.0.1"
            saved_port = 8888
        elif os.path.exists(self.wan_info_file):
            try:
                with open(self.wan_info_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("DOMAIN="):
                            saved_host = line.strip().split("=")[1]
                        elif line.startswith("PORT="):
                            saved_port = int(line.strip().split("=")[1])
            except Exception:
                pass
        elif os.path.exists(self.cfg_file):
            try:
                with open(self.cfg_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    saved_host = data.get("host", "bore.pub")
                    saved_port = data.get("port", 38888)
            except Exception:
                pass

        cfg_row = ctk.CTkFrame(self.server_cfg_frame, fg_color="transparent")
        cfg_row.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(cfg_row, text="IP / Domain:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 4))
        self.entry_server_ip = ctk.CTkEntry(cfg_row, width=140, height=28, font=ctk.CTkFont(size=11))
        self.entry_server_ip.insert(0, saved_host)
        self.entry_server_ip.pack(side="left", padx=(0, 8))
        
        ctk.CTkLabel(cfg_row, text="Port:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 4))
        self.entry_server_port = ctk.CTkEntry(cfg_row, width=60, height=28, font=ctk.CTkFont(size=11))
        self.entry_server_port.insert(0, str(saved_port))
        self.entry_server_port.pack(side="left")

    def toggle_server_config(self):
        if self.show_cfg:
            self.server_cfg_frame.pack_forget()
            self.show_cfg = False
        else:
            self.server_cfg_frame.pack(fill="x", padx=20, pady=(0, 14))
            self.show_cfg = True

    def _apply_server_settings(self):
        host = self.entry_server_ip.get().strip() or "bore.pub"
        try:
            port = int(self.entry_server_port.get().strip() or 38888)
        except ValueError:
            port = 38888
        self.net.set_server(host, port)
        try:
            with open(self.cfg_file, "w", encoding="utf-8") as f:
                json.dump({"host": host, "port": port}, f)
        except Exception:
            pass

    def do_login(self):
        self._apply_server_settings()
        username = self.login_user_entry.get().strip()
        password = self.login_pwd_entry.get().strip()
        
        if not username or not password:
            self.login_msg_label.configure(text="Vui lòng nhập tên đăng nhập và mật khẩu!", text_color="#EF4444")
            return
        
        self.btn_login.configure(state="disabled", text="Đang kết nối...")
        self.login_msg_label.configure(text="Đang kết nối tới máy chủ...", text_color="#3B82F6")
        self.update_idletasks()
        
        res = self.net.login(username, password)
        
        # Tự động chuyển kết nối dự phòng nếu mạng Internet WAN lag nhưng local server đang chạy
        if res is None:
            import socket
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.3)
                    local_live = (s.connect_ex(('127.0.0.1', 8888)) == 0)
            except Exception:
                local_live = False

            if local_live and self.net.host != "127.0.0.1":
                self.net.set_server("127.0.0.1", 8888)
                res = self.net.login(username, password)

        self.btn_login.configure(state="normal", text="Đăng Nhập Ngay")
        
        if res is None:
            self.login_msg_label.configure(text="Không thể kết nối đến Máy chủ! Vui lòng khởi động server trước.", text_color="#EF4444")
        elif res.get("success"):
            # Lưu hoặc xóa thông tin ghi nhớ
            if self.remember_var.get():
                try:
                    with open(self.auth_cache_file, "w", encoding="utf-8") as f:
                        json.dump({
                            "username": username,
                            "password": password,
                            "remember": True
                        }, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            else:
                if os.path.exists(self.auth_cache_file):
                    try:
                        os.remove(self.auth_cache_file)
                    except Exception:
                        pass
                        
            self.login_msg_label.configure(text="Đăng nhập thành công!", text_color="#10B981")
            self.on_login_success(res["user"])
        else:
            self.login_msg_label.configure(text=res.get("message", "Đăng nhập thất bại!"), text_color="#EF4444")

    def do_register(self):
        self._apply_server_settings()
        fullname = self.reg_name_entry.get().strip()
        username = self.reg_user_entry.get().strip()
        password = self.reg_pwd_entry.get().strip()
        
        if not fullname or not username or not password:
            self.reg_msg_label.configure(text="Vui lòng nhập đầy đủ các trường!", text_color="#EF4444")
            return
        
        import re
        clean_user = username.lstrip("@").lower()
        if len(clean_user) < 3 or len(clean_user) > 20:
            self.reg_msg_label.configure(text="Username phải dài từ 3 đến 20 ký tự!", text_color="#EF4444")
            return
        if not re.match(r"^[a-z0-9_]+$", clean_user):
            self.reg_msg_label.configure(text="Username chỉ được gồm chữ cái, số và gạch dưới (_), không dấu/khoảng trắng!", text_color="#EF4444")
            return

        if len(password) < 6:
            self.reg_msg_label.configure(text="Mật khẩu phải từ 6 ký tự trở lên!", text_color="#EF4444")
            return
        if not re.search(r"[A-Z]", password):
            self.reg_msg_label.configure(text="Mật khẩu cần ít nhất 1 chữ in hoa (A-Z)!", text_color="#EF4444")
            return
        if not re.search(r"[a-z]", password):
            self.reg_msg_label.configure(text="Mật khẩu cần ít nhất 1 chữ in thường (a-z)!", text_color="#EF4444")
            return
        if not re.search(r"[0-9]", password):
            self.reg_msg_label.configure(text="Mật khẩu cần ít nhất 1 chữ số (0-9)!", text_color="#EF4444")
            return
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`]", password):
            self.reg_msg_label.configure(text="Mật khẩu cần ít nhất 1 ký tự đặc biệt (!@#$%...)!", text_color="#EF4444")
            return
        
        self.btn_register.configure(state="disabled", text="Đang xử lý...")
        self.reg_msg_label.configure(text="Đang gửi thông tin đăng ký...", text_color="#3B82F6")
        self.update_idletasks()
        
        res = self.net.register(username, password, fullname)
        self.btn_register.configure(state="normal", text="Tạo Tài Khoản Mới")
        
        if res is None:
            self.reg_msg_label.configure(text="Không thể kết nối đến Máy chủ!", text_color="#EF4444")
        elif res.get("success"):
            # Tự động lưu thông tin đăng nhập khi đăng ký tài khoản thành công
            try:
                with open(self.auth_cache_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "username": username,
                        "password": password,
                        "remember": True
                    }, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

            self.reg_msg_label.configure(text="Đăng ký thành công! Đang chuyển hướng...", text_color="#10B981")
            self.on_login_success(res["user"])
        else:
            self.reg_msg_label.configure(text=res.get("message", "Đăng ký thất bại!"), text_color="#EF4444")
