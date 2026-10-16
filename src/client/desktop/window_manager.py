"""
Module Quản lý Cửa sổ và Trạng thái Desktop
- Lưu & khôi phục vị trí (X, Y), kích thước, trạng thái Maximized.
- Xử lý Multi-monitor Off-screen Recovery (khi rút màn hình phụ).
- Ghim cửa sổ luôn nổi trên cùng (Always on Top).
- Quản lý Pop-out Chat Windows (Tách cửa sổ chat riêng).
"""

import os
import json
import tkinter as tk
import ctypes

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "window_state.json")

def get_virtual_screen_bounds():
    """Lấy tọa độ vùng hiển thị của toàn bộ các màn hình (hỗ trợ đa màn hình trên Windows)."""
    try:
        user32 = ctypes.windll.user32
        x = user32.GetSystemMetrics(76)   # SM_XVIRTUALSCREEN
        y = user32.GetSystemMetrics(77)   # SM_YVIRTUALSCREEN
        w = user32.GetSystemMetrics(78)   # SM_CXVIRTUALSCREEN
        h = user32.GetSystemMetrics(79)   # SM_CYVIRTUALSCREEN
        return x, y, w, h
    except Exception:
        return 0, 0, 1920, 1080

def save_window_state(root: tk.Tk, file_path=CONFIG_PATH):
    """Lưu lại tọa độ và kích thước hiện tại của cửa sổ."""
    try:
        is_maximized = False
        try:
            is_maximized = (root.state() == 'zoomed')
        except Exception:
            pass

        geom = root.geometry() # định dạng: "WxH+X+Y"
        parts = geom.replace("+", " ").replace("x", " ").split()
        if len(parts) >= 4:
            w, h, x, y = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
            state_data = {
                "width": w,
                "height": h,
                "x": x,
                "y": y,
                "maximized": is_maximized
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2)
    except Exception as e:
        print(f"[WindowManager] Lỗi lưu trạng thái: {e}")

def restore_window_state(root: tk.Tk, default_w=1080, default_h=720, file_path=CONFIG_PATH):
    """Khôi phục vị trí và kích thước cửa sổ từ lần chạy trước."""
    try:
        if not os.path.exists(file_path):
            _center_window(root, default_w, default_h)
            return

        with open(file_path, "r", encoding="utf-8") as f:
            state_data = json.load(f)

        w = state_data.get("width", default_w)
        h = state_data.get("height", default_h)
        x = state_data.get("x", 100)
        y = state_data.get("y", 100)
        maximized = state_data.get("maximized", False)

        # Kiểm tra tọa độ có nằm trong màn hình hợp lệ không (Off-screen recovery)
        vx, vy, vw, vh = get_virtual_screen_bounds()
        if x < vx or x > (vx + vw - 100) or y < vy or y > (vy + vh - 100):
            print("[WindowManager] Cửa sổ bị văng khỏi màn hình hiển thị, khôi phục về trung tâm!")
            _center_window(root, w, h)
            return

        root.geometry(f"{w}x{h}+{x}+{y}")
        if maximized:
            try:
                root.state('zoomed')
            except Exception:
                pass
    except Exception as e:
        print(f"[WindowManager] Lỗi khôi phục: {e}")
        _center_window(root, default_w, default_h)

def _center_window(root: tk.Tk, w, h):
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    cx = max(0, (sw - w) // 2)
    cy = max(0, (sh - h) // 2)
    root.geometry(f"{w}x{h}+{cx}+{cy}")

def toggle_always_on_top(window: tk.Toplevel or tk.Tk) -> bool:
    """Bật / tắt chế độ luôn nổi trên cùng."""
    try:
        current = window.attributes("-topmost")
        new_state = not current
        window.attributes("-topmost", new_state)
        return new_state
    except Exception:
        return False
