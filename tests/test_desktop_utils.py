import os
import json
import tempfile
import pytest
from unittest.mock import MagicMock
from PIL import Image

from src.client.desktop.window_manager import (
    save_window_state,
    restore_window_state,
    get_virtual_screen_bounds
)
from src.client.desktop.tray import TrayManager

class TestWindowManager:
    def test_get_virtual_screen_bounds(self):
        x, y, w, h = get_virtual_screen_bounds()
        assert isinstance(x, int)
        assert isinstance(y, int)
        assert isinstance(w, int)
        assert isinstance(h, int)
        assert w > 0
        assert h > 0

    def test_save_and_restore_window_state(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            temp_config = tf.name

        try:
            # Mock root window
            mock_root = MagicMock()
            mock_root.state.return_value = 'normal'
            mock_root.geometry.return_value = "1024x768+120+80"

            # 1. Save
            save_window_state(mock_root, file_path=temp_config)
            assert os.path.exists(temp_config)
            
            with open(temp_config, "r", encoding="utf-8") as f:
                saved = json.load(f)
            assert saved["width"] == 1024
            assert saved["height"] == 768
            assert saved["x"] == 120
            assert saved["y"] == 80
            assert saved["maximized"] is False

            # 2. Restore
            restore_root = MagicMock()
            restore_root.winfo_screenwidth.return_value = 1920
            restore_root.winfo_screenheight.return_value = 1080
            
            restore_window_state(restore_root, file_path=temp_config)
            restore_root.geometry.assert_called_with("1024x768+120+80")

        finally:
            if os.path.exists(temp_config):
                try:
                    os.remove(temp_config)
                except Exception:
                    pass

    def test_off_screen_recovery(self):
        """Khi màn hình phụ bị rút cáp, tọa độ cũ nằm ngoài màn hình -> phải tự căn giữa."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            temp_config = tf.name

        try:
            # Saved position is far offscreen (e.g., disconnected secondary display)
            invalid_state = {
                "width": 800,
                "height": 600,
                "x": 88888,
                "y": 88888,
                "maximized": False
            }
            with open(temp_config, "w", encoding="utf-8") as f:
                json.dump(invalid_state, f)

            mock_root = MagicMock()
            mock_root.winfo_screenwidth.return_value = 1920
            mock_root.winfo_screenheight.return_value = 1080

            restore_window_state(mock_root, default_w=800, default_h=600, file_path=temp_config)
            
            # Center of 1920x1080 for 800x600: cx = (1920-800)//2 = 560, cy = (1080-600)//2 = 240
            mock_root.geometry.assert_called_with("800x600+560+240")

        finally:
            if os.path.exists(temp_config):
                try:
                    os.remove(temp_config)
                except Exception:
                    pass

class TestTrayIconGeneration:
    def test_tray_icon_image_creation(self):
        tray = TrayManager()
        
        # 1. Zero unread, online
        img_online = tray._create_icon_image(unread_count=0, status="online")
        assert isinstance(img_online, Image.Image)
        assert img_online.size == (64, 64)
        assert img_online.mode == "RGBA"

        # 2. Busy status
        img_busy = tray._create_icon_image(unread_count=0, status="busy")
        assert img_busy.size == (64, 64)

        # 3. Badge with count < 100
        img_badge = tray._create_icon_image(unread_count=5, status="online")
        assert img_badge.size == (64, 64)

        # 4. Badge overflow (99+)
        img_overflow = tray._create_icon_image(unread_count=120, status="online")
        assert img_overflow.size == (64, 64)

class TestQuickSwitcherFilter:
    def test_quick_switcher_filtering_logic(self):
        convs = [
            {"id": 1, "title": "Nhóm Đồ Án CNPM", "type": "group"},
            {"id": 2, "title": "Alice Nguyen", "type": "direct"},
            {"id": 3, "title": "Bob Builder", "type": "direct"},
            {"id": 4, "title": "Cloud của tôi (Saved Messages)", "type": "saved"}
        ]
        
        quick_actions = [
            {"type": "action", "key": "screenshot", "title": "📷 Chụp màn hình (Ctrl+Alt+A)", "sub": "Công cụ chụp và vẽ chú thích"},
            {"type": "action", "key": "saved", "title": "☁️ Cloud của tôi (Saved Messages)", "sub": "Lưu trữ tin nhắn & tệp cá nhân"},
            {"type": "action", "key": "lock", "title": "🔒 Khóa màn hình (Ctrl+L)", "sub": "Bảo vệ riêng tư nhanh"},
            {"type": "action", "key": "topmost", "title": "📌 Ghim cửa sổ nổi trên cùng", "sub": "Bật/Tắt Always-on-Top"}
        ]

        def filter_items(query: str):
            q = query.strip().lower()
            res = []
            for act in quick_actions:
                if not q or q in act["title"].lower() or q in act["sub"].lower():
                    res.append(act)
            for c in convs:
                t = c.get("title", "")
                if not q or q in t.lower():
                    res.append({"type": "conv", "data": c, "title": t})
            return res

        # Empty search returns all actions + conversations
        all_items = filter_items("")
        assert len(all_items) == len(quick_actions) + len(convs)

        # Search "alice"
        alice_items = filter_items("alice")
        assert any(item.get("title") == "Alice Nguyen" for item in alice_items)
        assert not any(item.get("title") == "Bob Builder" for item in alice_items)

        # Search "chụp"
        screen_items = filter_items("chụp")
        assert any(item.get("key") == "screenshot" for item in screen_items)
