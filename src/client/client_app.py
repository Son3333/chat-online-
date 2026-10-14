import customtkinter as ctk
import sys
import os

from src.client.network import NetworkClient
from src.client.ui.auth_frame import AuthFrame
from src.client.ui.main_window import MainWindow

class ChatApplication(ctk.CTk):
    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        super().__init__()
        
        self.host = host
        self.port = port
        self.net = NetworkClient(host=self.host, port=self.port)
        self.current_user = None
        
        # Configure Window
        self.title("Ứng Dụng Nhắn Tin & Truyền Thông Tin - Nhóm 05")
        self.geometry("1100x720")
        self.minsize(850, 600)
        
        # Căn giữa màn hình
        self.center_window()

        # Themes
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # Xử lý đóng cửa sổ
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Container
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.current_frame = None
        self.show_auth_frame()

    def center_window(self):
        self.update_idletasks()
        width = 1100
        height = 720
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2) - 30
        self.geometry(f"{width}x{height}+{x}+{y}")

    def show_auth_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
        
        self.current_user = None
        self.current_frame = AuthFrame(self, on_login_success=self.show_main_window, network_client=self.net)
        self.current_frame.grid(row=0, column=0, sticky="nsew")

    def show_main_window(self, user_info: dict):
        if self.current_frame:
            self.current_frame.destroy()
        
        self.current_user = user_info
        self.title(f"Ứng Dụng Nhắn Tin - [{user_info['full_name']}]")
        self.current_frame = MainWindow(self, current_user=user_info, network_client=self.net, on_logout=self.show_auth_frame)
        self.current_frame.grid(row=0, column=0, sticky="nsew")

    def on_closing(self):
        try:
            self.net.disconnect()
        except Exception:
            pass
        self.destroy()

def run(host: str = "127.0.0.1", port: int = 8888):
    app = ChatApplication(host, port)
    app.mainloop()

if __name__ == "__main__":
    run()

