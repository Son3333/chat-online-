import sys
import os
import json
import socket
import traceback
import datetime

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)
sys.path.insert(0, PROJECT_DIR)

def log_crash(exc: Exception):
    """Ghi lại chi tiết lỗi vào crash_log.txt và hiển thị hộp thoại cảnh báo người dùng."""
    error_msg = traceback.format_exc()
    log_file = os.path.join(PROJECT_DIR, "crash_log.txt")
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 60 + "\n")
            f.write(f"THỜI ĐIỂM XẢY RA LỖI: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"PHIÊN BẢN PYTHON: {sys.version}\n")
            f.write(f"THƯ MỤC LÀM VIỆC: {PROJECT_DIR}\n")
            f.write("CHI TIẾT TRACEBACK:\n")
            f.write(error_msg)
            f.write("=" * 60 + "\n")
    except Exception:
        pass

    # In ra console nếu có console
    if sys.stdout is not None:
        try:
            print("\n[!] DA XAY RA LOI KHOI CHAY UNG DUNG:\n" + error_msg)
        except Exception:
            pass

    # Hiển thị popup thông báo lỗi trực tiếp trên màn hình Windows
    try:
        import ctypes
        user_alert = (
            f"Ứng dụng gặp sự cố khi khởi chạy!\n\n"
            f"Nguyên nhân: {type(exc).__name__}: {str(exc)}\n\n"
            f"Chi tiết kỹ thuật đã được lưu tại file:\ncrash_log.txt\n\n"
            f"Vui lòng chụp lại màn hình hoặc gửi file crash_log.txt để được hỗ trợ!"
        )
        ctypes.windll.user32.MessageBoxW(0, user_alert, "Lỗi Khởi Động - Ứng Dụng Nhắn Tin", 0x10)
    except Exception:
        pass

import subprocess
import time

def is_port_in_use(port=8888, host='127.0.0.1'):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.4)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def get_target_server():
    """Xác định địa chỉ Server để Client kết nối:
    1. Nếu cổng 8888 nội bộ đang chạy trên máy này -> Dùng 127.0.0.1:8888
    2. Đọc cấu hình từ wan_server_info.txt hoặc server_config.json.
    3. Nếu remote server đang online -> Kết nối remote server.
    4. Nếu không có server nào chạy -> Tự động bật run_server_wan.py chạy ngầm (Zero-config)!
    """
    if is_port_in_use(8888, '127.0.0.1'):
        return "127.0.0.1", 8888

    target_host = "bore.pub"
    target_port = 38888

    info_file = os.path.join(PROJECT_DIR, "wan_server_info.txt")
    if os.path.exists(info_file):
        try:
            with open(info_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("DOMAIN="):
                        target_host = line.strip().split("=")[1]
                    elif line.startswith("PORT="):
                        target_port = int(line.strip().split("=")[1])
        except Exception:
            pass

    cfg_file = os.path.join(PROJECT_DIR, "server_config.json")
    if os.path.exists(cfg_file):
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                target_host = data.get("host", target_host)
                target_port = int(data.get("port", target_port))
        except Exception:
            pass

    # Nếu target remote đang online (ví dụ máy bạn bè đã bật server trước)
    if target_host not in ('127.0.0.1', 'localhost'):
        if is_port_in_use(target_port, target_host):
            return target_host, target_port

    # Cả local và remote đều chưa chạy -> Tự động kích hoạt Server WAN ngầm (Headless)
    wan_script = os.path.join(PROJECT_DIR, "run_server_wan.py")
    if os.path.exists(wan_script):
        try:
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            # Ưu tiên dùng pythonw hoặc python để chạy ngầm
            subprocess.Popen(
                [sys.executable, wan_script],
                cwd=PROJECT_DIR,
                creationflags=flags
            )
            # Chờ tối đa 3 giây cho socket 8888 mở
            for _ in range(15):
                time.sleep(0.2)
                if is_port_in_use(8888, '127.0.0.1'):
                    return "127.0.0.1", 8888
        except Exception:
            pass

    return target_host, target_port

def main():
    try:
        # Kiểm tra thư viện customtkinter & pillow
        import customtkinter
        import PIL
    except ImportError as e:
        log_crash(e)
        sys.exit(1)

    try:
        # Xác định địa chỉ server kết nối
        host, port = get_target_server()

        # Khởi chạy giao diện chính Desktop Client
        from src.client.client_app import run
        run(host=host, port=port)
    except Exception as e:
        log_crash(e)
        sys.exit(1)

if __name__ == "__main__":
    main()
