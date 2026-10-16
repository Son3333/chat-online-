"""
Module Quản lý Khay Hệ thống (System Tray Integration)
- Tích hợp pystray chạy luồng ngầm mượt mà.
- Hiển thị Icon ứng dụng kèm Badge đỏ báo số tin nhắn chưa đọc.
- Tooltip tóm tắt trạng thái và số tin nhắn chưa đọc.
- Menu ngữ cảnh chuột phải: Mở ứng dụng, Đổi trạng thái, Chụp màn hình, Khóa màn hình, Thoát.
"""

import threading
from typing import Callable, Optional
from PIL import Image, ImageDraw, ImageFont

class TrayManager:
    def __init__(self, 
                 app_title="ChatApp Desktop",
                 on_restore: Optional[Callable] = None,
                 on_screenshot: Optional[Callable] = None,
                 on_lock: Optional[Callable] = None,
                 on_status_change: Optional[Callable[[str], None]] = None,
                 on_quit: Optional[Callable] = None):
        self.app_title = app_title
        self.on_restore = on_restore
        self.on_screenshot = on_screenshot
        self.on_lock = on_lock
        self.on_status_change = on_status_change
        self.on_quit = on_quit

        self.unread_count = 0
        self.status = "online" # online, busy, invisible
        self.icon = None
        self._thread = None
        self._running = False

    def _create_icon_image(self, unread_count=0, status="online"):
        """Vẽ Icon động 64x64 pixel với chấm trạng thái và huy hiệu chưa đọc."""
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Nền icon hình tròn xanh đại diện cho App
        bg_color = (37, 99, 235, 255) # Blue 600
        draw.ellipse([4, 4, 60, 60], fill=bg_color)

        # Vẽ biểu tượng bong bóng chat đơn giản màu trắng
        draw.rounded_rectangle([16, 16, 48, 42], radius=6, fill=(255, 255, 255, 255))
        draw.polygon([(22, 42), (32, 42), (20, 52)], fill=(255, 255, 255, 255))

        # Chấm trạng thái nhỏ ở góc dưới phải
        status_colors = {
            "online": (34, 197, 94, 255),   # Xanh lá
            "busy": (239, 68, 68, 255),     # Đỏ
            "invisible": (148, 163, 184, 255) # Xám
        }
        st_color = status_colors.get(status, (34, 197, 94, 255))
        draw.ellipse([44, 44, 58, 58], fill=st_color, outline=(255, 255, 255, 255), width=2)

        # Nếu có tin nhắn chưa đọc, vẽ huy hiệu tròn đỏ góc trên phải
        if unread_count > 0:
            badge_text = str(unread_count) if unread_count < 100 else "99+"
            draw.ellipse([36, 2, 62, 28], fill=(239, 68, 68, 255), outline=(255, 255, 255, 255), width=2)
            try:
                # Cố gắng vẽ số text
                draw.text((43, 6), badge_text[0], fill=(255, 255, 255, 255))
            except Exception:
                pass

        return img

    def start(self):
        """Khởi động System Tray trong một luồng riêng."""
        if self._running:
            return
        self._running = True

        def _run():
            try:
                import pystray
                from pystray import MenuItem as item, Menu

                image = self._create_icon_image(self.unread_count, self.status)

                def do_restore(icon, item):
                    if self.on_restore:
                        self.on_restore()

                def do_screenshot(icon, item):
                    if self.on_screenshot:
                        self.on_screenshot()

                def do_lock(icon, item):
                    if self.on_lock:
                        self.on_lock()

                def set_status(st):
                    def _setter(icon, item):
                        self.status = st
                        if self.on_status_change:
                            self.on_status_change(st)
                        self.update_tray(self.unread_count, st)
                    return _setter

                def do_quit(icon, item):
                    self.stop()
                    if self.on_quit:
                        self.on_quit()

                status_menu = Menu(
                    item('🟢 Trực tuyến (Online)', set_status('online')),
                    item('🔴 Bận (Do Not Disturb)', set_status('busy')),
                    item('⚪ Vô hình (Invisible)', set_status('invisible'))
                )

                menu = Menu(
                    item('💬 Mở cửa sổ chính', do_restore, default=True),
                    item('👤 Trạng thái hoạt động', status_menu),
                    item('📷 Chụp màn hình (Ctrl+Alt+A)', do_screenshot),
                    item('🔒 Khóa ứng dụng (Ctrl+L)', do_lock),
                    Menu.SEPARATOR,
                    item('🚪 Thoát ứng dụng', do_quit)
                )

                self.icon = pystray.Icon("ChatApp", image, self._get_tooltip(), menu)
                self.icon.run()
            except Exception as e:
                print(f"[TrayManager] Lỗi khởi động Tray: {e}")

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def _get_tooltip(self):
        if self.unread_count > 0:
            return f"{self.app_title} ({self.unread_count} tin nhắn mới)"
        return f"{self.app_title} - Trực tuyến"

    def update_tray(self, unread_count: int, status: Optional[str] = None):
        """Cập nhật huy hiệu chưa đọc và tooltip."""
        self.unread_count = unread_count
        if status:
            self.status = status

        if self.icon:
            try:
                new_img = self._create_icon_image(self.unread_count, self.status)
                self.icon.icon = new_img
                self.icon.title = self._get_tooltip()
            except Exception:
                pass

    def stop(self):
        self._running = False
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass

