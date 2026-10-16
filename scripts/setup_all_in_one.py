import os
import sys
import socket
import subprocess

if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

try:
    from scripts.create_shortcut import make_shortcut
except ImportError:
    from create_shortcut import make_shortcut

def ensure_desktop_shortcut():
    desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
    if not os.path.exists(desktop):
        return

    final_shortcut_name = "Vibe Người Tốt.lnk"
    final_path = os.path.join(desktop, final_shortcut_name)

    # Nếu đã có icon hợp lệ ngoài desktop rồi (> 500 bytes) thì thôi
    if os.path.exists(final_path) and os.path.getsize(final_path) > 500:
        print("[*] Biểu tượng 'Vibe Người Tốt' ngoài Desktop đã có sẵn -> Bỏ qua.")
        return

    print("[+] Chưa có biểu tượng ngoài Desktop hoặc bị lỗi -> Đang tạo lối tắt mới...")
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    bat_path = os.path.join(root, "CHAY_UNG_DUNG.bat")
    ico_path = os.path.join(root, "app.ico")

    ok = make_shortcut(
        shortcut_path=final_path,
        target_path=bat_path,
        arguments="",
        working_dir=root,
        icon_path=ico_path,
        description="Vibe Người Tốt - Ứng dụng nhắn tin bảo mật",
        show_cmd=1
    )
    if ok:
        print("[OK] Đã tạo thành công biểu tượng ngoài Desktop: Vibe Người Tốt.lnk")
    else:
        print("[-] Không thể tạo lối tắt ngoài Desktop.")

def ensure_windows_startup():
    startup_dir = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    if not os.path.exists(startup_dir):
        return

    # Clean old vbs if any
    old_vbs = os.path.join(startup_dir, "Vibe_Server_WAN_AutoStartup.vbs")
    if os.path.exists(old_vbs):
        try:
            os.remove(old_vbs)
        except Exception:
            pass

    final_lnk = os.path.join(startup_dir, "Vibe_Server_WAN.lnk")
    if os.path.exists(final_lnk) and os.path.getsize(final_lnk) > 500:
        print("[*] Khởi động Server WAN cùng Windows đã được thiết lập -> Bỏ qua.")
        return

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    wan_script = os.path.join(root, "run_server_wan.py")

    python_dir = os.path.dirname(sys.executable)
    pythonw_candidate = os.path.join(python_dir, "pythonw.exe")
    python_bin = pythonw_candidate if os.path.exists(pythonw_candidate) else sys.executable

    ok = make_shortcut(
        shortcut_path=final_lnk,
        target_path=python_bin,
        arguments=f'"{wan_script}"',
        working_dir=root,
        icon_path="",
        description="Vibe Server WAN Auto-Startup",
        show_cmd=7 # Minimized
    )
    if ok:
        print("[OK] Đã đăng ký tự khởi động Server WAN cùng Windows (bật máy tính là server chạy ngầm sẵn sàng).")


def check_wan_server_online(host="bore.pub", port=38888):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1.5)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

def ensure_server_running():
    # 1. Kiểm tra cổng 8888 cục bộ
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(0.8)
        s.connect(('127.0.0.1', 8888))
        s.close()
        print("[*] Server cục bộ đang hoạt động sẵn sàng trên cổng 8888.")
        return True
    except Exception:
        pass

    # 2. Kiểm tra nếu Máy chủ WAN (Internet) đang trực tuyến
    if check_wan_server_online("bore.pub", 38888):
        print("[+] Đã phát hiện Máy chủ WAN trực tuyến tại bore.pub:38888!")
        print("[*] Ứng dụng trên máy này sẽ kết nối trực tiếp tới Máy chủ WAN.")
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cfg_file = os.path.join(root, "server_config.json")
        try:
            import json
            with open(cfg_file, "w", encoding="utf-8") as f:
                json.dump({"host": "bore.pub", "port": 38888}, f, indent=2)
        except Exception:
            pass
        return True

    # 3. Nếu chưa có máy chủ nào -> Khởi động Chat Server WAN ngầm làm Host
    print("[+] Server chưa chạy -> Đang khởi động Chat Server WAN ngầm...")
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    wan_script = os.path.join(root, "run_server_wan.py")
    python_dir = os.path.dirname(sys.executable)
    pythonw_candidate = os.path.join(python_dir, "pythonw.exe")
    python_bin = pythonw_candidate if os.path.exists(pythonw_candidate) else sys.executable

    if os.name == 'nt':
        flags = subprocess.CREATE_NO_WINDOW
        subprocess.Popen([python_bin, wan_script], cwd=root, creationflags=flags)
    else:
        subprocess.Popen([python_bin, wan_script], cwd=root)
    print("[OK] Đã kích hoạt Chat Server WAN chạy ngầm.")
    return True

if __name__ == "__main__":
    print("=================================================================")
    print("   VIBE NGUOI TOT - ALL-IN-ONE SYSTEM INITIALIZER")
    print("=================================================================")
    ensure_desktop_shortcut()
    # Chỉ tự động kích hoạt startup Server nếu không có WAN server sẵn từ máy khác
    if not check_wan_server_online("bore.pub", 38888):
        ensure_windows_startup()
    ensure_server_running()
    print("=================================================================")

