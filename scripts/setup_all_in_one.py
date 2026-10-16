import os
import sys
import socket
import subprocess

if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def ensure_desktop_shortcut():
    desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
    if not os.path.exists(desktop):
        return

    final_shortcut_name = "Vibe Người Tốt.lnk"
    final_path = os.path.join(desktop, final_shortcut_name)

    # Nếu đã có icon ngoài desktop rồi thì thôi
    if os.path.exists(final_path):
        print("[*] Biểu tượng 'Vibe Người Tốt' ngoài Desktop đã có sẵn -> Bỏ qua.")
        return

    print("[+] Chưa có biểu tượng ngoài Desktop -> Đang tạo lối tắt mới...")
    temp_shortcut_name = "Vibe_Nguoi_Tot_temp.lnk"
    temp_path = os.path.join(desktop, temp_shortcut_name)

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    bat_path = os.path.join(root, "CHAY_UNG_DUNG.bat")
    app_ico = os.path.join(root, "app.ico")
    electron_ico = os.path.join(root, "frontend", "node_modules", "electron", "dist", "electron.exe")
    ico_path = app_ico if os.path.exists(app_ico) else electron_ico

    ps_code = f"""
$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut('{temp_path}')
$sc.TargetPath = $env:ComSpec
$sc.Arguments = '/c "{bat_path}"'
$sc.WorkingDirectory = '{root}'
$sc.Description = 'Vibe Người Tốt - Ứng dụng nhắn tin bảo mật'
if (Test-Path '{ico_path}') {{
    $sc.IconLocation = '{ico_path},0'
}}
$sc.WindowStyle = 1
$sc.Save()
"""
    import base64
    encoded_command = base64.b64encode(ps_code.encode("utf-16le")).decode("ascii")
    subprocess.run(["powershell", "-NoProfile", "-EncodedCommand", encoded_command], capture_output=True)

    if os.path.exists(temp_path):
        try:
            if os.path.exists(final_path):
                os.remove(final_path)
            os.rename(temp_path, final_path)
            print("[OK] Đã tạo thành công biểu tượng ngoài Desktop: Vibe Người Tốt.lnk")
        except Exception:
            pass

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
    if os.path.exists(final_lnk):
        print("[*] Khởi động Server WAN cùng Windows đã được thiết lập -> Bỏ qua.")
        return

    temp_lnk = os.path.join(startup_dir, "Vibe_Server_WAN_temp.lnk")
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    wan_script = os.path.join(root, "run_server_wan.py")

    python_dir = os.path.dirname(sys.executable)
    pythonw_candidate = os.path.join(python_dir, "pythonw.exe")
    python_bin = pythonw_candidate if os.path.exists(pythonw_candidate) else sys.executable

    ps_code = f"""
$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut('{temp_lnk}')
$sc.TargetPath = '{python_bin}'
$sc.Arguments = '"{wan_script}"'
$sc.WorkingDirectory = '{root}'
$sc.Description = 'Vibe Server WAN Auto-Startup'
$sc.WindowStyle = 7
$sc.Save()
"""
    import base64
    encoded_command = base64.b64encode(ps_code.encode("utf-16le")).decode("ascii")
    subprocess.run(["powershell", "-NoProfile", "-EncodedCommand", encoded_command], capture_output=True)

    if os.path.exists(temp_lnk):
        try:
            if os.path.exists(final_lnk):
                os.remove(final_lnk)
            os.rename(temp_lnk, final_lnk)
            print("[OK] Đã đăng ký tự khởi động Server WAN cùng Windows (bật máy tính là server chạy ngầm sẵn sàng).")
        except Exception:
            pass

def ensure_server_running():
    # Kiểm tra cổng 8888
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1.0)
        s.connect(('127.0.0.1', 8888))
        s.close()
        print("[*] Server WAN đang hoạt động sẵn sàng trên cổng 8888.")
        return True
    except Exception:
        pass

    # Nếu chưa chạy, khởi động ngầm ngay
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
    ensure_windows_startup()
    ensure_server_running()
    print("=================================================================")

