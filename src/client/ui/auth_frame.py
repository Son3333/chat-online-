import os
import json
import customtkinter as ctk
from typing import Callable

class AuthFrame(ctk.CTkFrame):
    def __init__(self, master, on_login_success: Callable, network_client):
        super().__init__(master, fg_color="transparent")
        self.on_login_success = on_login_success
        self.net = network_client
        
        self.auth_cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "user_credentials.json")
        self.cfg_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "server_config.json")
        self.wan_info_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "wan_server_info.txt")

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
        
        # Checkbox ghi nhớ mật khẩu
        self.remember_var = ctk.BooleanVar(value=False)
        self.remember_cb = ctk.CTkCheckBox(
            tab,
            text="Ghi nhớ tài khoản & mật khẩu",
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
        
        ctk.CTkLabel(tab, text="Tên đăng nhập (username):", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(2, 2))
        self.reg_user_entry = ctk.CTkEntry(tab, placeholder_text="Tên viết liền, không dấu", height=36, corner_radius=8)
        self.reg_user_entry.pack(fill="x", padx=15, pady=(0, 6))
        
        ctk.CTkLabel(tab, text="Mật khẩu:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(2, 2))
        self.reg_pwd_entry = ctk.CTkEntry(tab, placeholder_text="Mật khẩu bảo mật", show="•", height=36, corner_radius=8)
        self.reg_pwd_entry.pack(fill="x", padx=15, pady=(0, 10))
        self.reg_pwd_entry.bind("<Return>", lambda e: self.do_register())
        
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
        """Tự động điền tài khoản và mật khẩu nếu người dùng đã tích Ghi nhớ trước đó."""
        if os.path.exists(self.auth_cache_file):
            try:
                with open(self.auth_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("remember"):
                        self.login_user_entry.insert(0, data.get("username", ""))
                        self.login_pwd_entry.insert(0, data.get("password", ""))
                        self.remember_var.set(True)
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
        
        # Tự động đọc cấu hình WAN/LAN đã lưu trước đó nếu có
        saved_host = "127.0.0.1"
        saved_port = 8888
        
        if os.path.exists(self.wan_info_file):
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
                    saved_host = data.get("host", "127.0.0.1")
                    saved_port = data.get("port", 8888)
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
        host = self.entry_server_ip.get().strip() or "127.0.0.1"
        try:
            port = int(self.entry_server_port.get().strip() or 8888)
        except ValueError:
            port = 8888
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
        
        self.btn_register.configure(state="disabled", text="Đang xử lý...")
        self.reg_msg_label.configure(text="Đang gửi thông tin đăng ký...", text_color="#3B82F6")
        self.update_idletasks()
        
        res = self.net.register(username, password, fullname)
        self.btn_register.configure(state="normal", text="Tạo Tài Khoản Mới")
        
        if res is None:
            self.reg_msg_label.configure(text="Không thể kết nối đến Máy chủ!", text_color="#EF4444")
        elif res.get("success"):
            self.reg_msg_label.configure(text="Đăng ký thành công! Đang chuyển hướng...", text_color="#10B981")
            self.on_login_success(res["user"])
        else:
            self.reg_msg_label.configure(text=res.get("message", "Đăng ký thất bại!"), text_color="#EF4444")
