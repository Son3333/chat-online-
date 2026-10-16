import os
import json
import tempfile
from unittest.mock import MagicMock
from src.client.desktop.window_manager import save_window_state, restore_window_state
from src.client.ui.chat_bubble import is_pure_emoji, format_file_size, format_time


class TestWindowManager:
    def test_save_and_restore_window_state(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            # Mock root window
            mock_win = MagicMock()
            mock_win.state.return_value = "normal"
            mock_win.geometry.return_value = "1200x800+150+200"
            mock_win.winfo_screenwidth.return_value = 1920
            mock_win.winfo_screenheight.return_value = 1080

            # Save state
            save_window_state(mock_win, file_path=path)
            assert os.path.exists(path)

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data["x"] == 150
            assert data["y"] == 200
            assert data["width"] == 1200
            assert data["height"] == 800

            # Restore state onto a new mock window
            mock_win2 = MagicMock()
            mock_win2.winfo_screenwidth.return_value = 1920
            mock_win2.winfo_screenheight.return_value = 1080
            restore_window_state(mock_win2, file_path=path)

            mock_win2.geometry.assert_called_once()
            geom_arg = mock_win2.geometry.call_args[0][0]
            assert "1200x800+150+200" in geom_arg
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_multi_monitor_offscreen_recovery(self):
        """Nếu cửa sổ bị kéo sang màn hình phụ rồi rút cáp (tọa độ âm hoặc vượt ngoài màn hình chính)."""
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            # Write invalid/off-screen coordinates
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"x": -9999, "y": -9999, "width": 1100, "height": 720, "maximized": False}, f)

            mock_win = MagicMock()
            mock_win.winfo_screenwidth.return_value = 1920
            mock_win.winfo_screenheight.return_value = 1080

            restore_window_state(mock_win, file_path=path)
            geom_arg = mock_win.geometry.call_args[0][0]

            # Coordinates should be safely reset inside the main screen (x >= 0, y >= 0)
            assert "-9999" not in geom_arg
        finally:
            if os.path.exists(path):
                os.remove(path)


class TestChatBubbleFormatters:
    def test_is_pure_emoji(self):
        assert is_pure_emoji("😀") is True
        assert is_pure_emoji("🚀🔥❤️") is True
        assert is_pure_emoji("Hello 😀") is False
        assert is_pure_emoji("Tin nhắn văn bản") is False
        assert is_pure_emoji("") is False
        assert is_pure_emoji("    ") is False

    def test_format_file_size(self):
        assert format_file_size(0) == "0 B"
        assert format_file_size(512) == "512.0 B"
        assert format_file_size(2048) == "2.0 KB"
        assert format_file_size(1048576 * 5) == "5.0 MB"
        assert format_file_size(1073741824 * 3) == "3.0 GB"

    def test_format_time(self):
        assert format_time("2026-10-16 14:35:20") == "14:35"
        assert format_time("14:35") == "14:35"
        assert format_time("") == ""
