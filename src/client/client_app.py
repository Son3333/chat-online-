import customtkinter as ctk
import sys
import os
import threading
from typing import Optional

from src.client.network import NetworkClient
from src.client.ui.auth_frame import AuthFrame
from src.client.ui.main_window import MainWindow

from src.client.desktop.window_manager import restore_window_state, save_window_state, toggle_always_on_top
from src.client.desktop.tray import TrayManager
from src.client.desktop.screenshot import ScreenCaptureTool
from src.client.desktop.quick_switcher import QuickSwitcher
from src.client.desktop.quick_lock import QuickLockOverlay

class ChatApplication(ctk.CTk):
    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        super().__init__()
        
        self.host = host
        self.port = port
        self.net = NetworkClient(host=self.host, port=self.port)
        self.current_user = None
        self.current_frame = None
        self.lock_overlay: Optional[QuickLockOverlay] = None
        
        # Configure Window
        self.title("Ứng Dụng Nhắn Tin & Truyền Thông Tin - Nhóm 05")
        self.minsize(850, 600)
        
        # Khôi phục trạng thái kích thước và tọa độ từ lần trước (hỗ trợ đa màn hình)
        restore_window_state(self, default_w=1100, default_h=720)

        # Themes
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # Xử lý đóng cửa sổ: Thu nhỏ xuống Khay hệ thống (System Tray)
        self.protocol("WM_DELETE_WINDOW", self.on_closing_to_tray)

        # Container
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Khởi tạo công cụ chụp màn hình
        self.screenshot_tool = ScreenCaptureTool(self, on_send_image=self.on_screenshot_taken)

        # Khởi tạo System Tray Manager
        self.tray = TrayManager(
            app_title="ChatApp Nhóm 05",
            on_restore=lambda: self.after(0, self.restore_from_tray),
            on_screenshot=lambda: self.after(0, self.trigger_screenshot),
            on_lock=lambda: self.after(0, self.trigger_lock),
            on_status_change=self.on_tray_status_change,
            on_quit=lambda: self.after(0, self.force_exit)
        )
        self.tray.start()

        # Đăng ký phím tắt toàn cục / nội bộ
        self._setup_shortcuts()

        # Hiển thị màn hình đăng nhập
        self.show_auth_frame()

    def _setup_shortcuts(self):
        # 1. In-app hotkeys
        self.bind("<Control-k>", lambda e: self.trigger_quick_switcher())
        self.bind("<Control-K>", lambda e: self.trigger_quick_switcher())
        self.bind("<Control-l>", lambda e: self.trigger_lock())
        self.bind("<Control-L>", lambda e: self.trigger_lock())

        # 2. Global Hotkey (Chụp màn hình ngay cả khi app đang ẩn dưới tray)
        def _register_global():
            try:
                import keyboard
                keyboard.add_hotkey("ctrl+alt+a", lambda: self.after(0, self.trigger_screenshot))
            except Exception:
                pass
        threading.Thread(target=_register_global, daemon=True).start()

    def show_auth_frame(self, auto_login: bool = True):
        if self.current_frame:
            self.current_frame.destroy()
        
        self.current_user = None
        self.lock_overlay = None
        self.current_frame = AuthFrame(self, on_login_success=self.show_main_window, network_client=self.net, auto_login=auto_login)
        self.current_frame.grid(row=0, column=0, sticky="nsew")

    def show_main_window(self, user_info: dict):
        if self.current_frame:
            self.current_frame.destroy()
        
        self.current_user = user_info
        self.title(f"Ứng Dụng Nhắn Tin - [{user_info['full_name']}]")
        self.current_frame = MainWindow(
            self, 
            current_user=user_info, 
            network_client=self.net, 
            on_logout=lambda: self.show_auth_frame(auto_login=False)
        )
        self.current_frame.grid(row=0, column=0, sticky="nsew")

        # Cài đặt Quick Lock Overlay
        self.lock_overlay = QuickLockOverlay(
            self, 
            username=user_info.get("username", "user"),
            unlock_validator=self._validate_unlock_password
        )

    def _validate_unlock_password(self, password: str) -> bool:
        """Kiểm tra mật khẩu mở khóa bằng cách gửi xác thực tới máy chủ."""
        if not self.current_user:
            return True
        username = self.current_user.get("username")
        res = self.net.login(username, password)
        return bool(res and res.get("success"))

    def trigger_quick_switcher(self):
        """Mở hộp thoại chuyển đổi nhanh Ctrl+K."""
        if not self.current_frame or not isinstance(self.current_frame, MainWindow):
            return
        
        switcher = QuickSwitcher(
            self,
            conversations_provider=lambda: self.current_frame.conversations,
            on_select_conversation=lambda cid: self.current_frame.select_conversation(cid),
            action_handlers={
                "screenshot": self.trigger_screenshot,
                "saved": lambda: self.current_frame.open_saved_messages(),
                "lock": self.trigger_lock,
                "topmost": self.toggle_topmost
            }
        )
        switcher.show()

    def trigger_screenshot(self):
        self.screenshot_tool.start_capture()

    def on_screenshot_taken(self, image_path: str):
        if self.current_frame and isinstance(self.current_frame, MainWindow):
            self.current_frame.send_image_file(image_path)

    def trigger_lock(self):
        if self.lock_overlay:
            self.lock_overlay.lock()

    def toggle_topmost(self):
        new_state = toggle_always_on_top(self)
        return new_state

    def on_tray_status_change(self, status: str):
        pass

    def restore_from_tray(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def on_closing_to_tray(self):
        """Khi bấm [X], lưu tọa độ cửa sổ và ẩn xuống System Tray."""
        save_window_state(self)
        self.withdraw()

    def force_exit(self):
        """Thoát hoàn toàn ứng dụng."""
        save_window_state(self)
        self.tray.stop()
        try:
            self.net.disconnect()
        except Exception:
            pass
        self.destroy()
        sys.exit(0)

def run(host: str = "127.0.0.1", port: int = 8888):
    app = ChatApplication(host, port)
    app.mainloop()

if __name__ == "__main__":
    run()
