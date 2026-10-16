import os
import subprocess
import sys

def create_desktop_shortcut():
    desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
    if not os.path.exists(desktop):
        return False

    temp_shortcut_name = "Vibe_Nguoi_Tot_temp.lnk"
    final_shortcut_name = "Vibe Người Tốt.lnk"

    temp_path = os.path.join(desktop, temp_shortcut_name)
    final_path = os.path.join(desktop, final_shortcut_name)

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
            return True
        except Exception:
            return True
    return os.path.exists(final_path)

if __name__ == "__main__":
    ok = create_desktop_shortcut()
    if ok:
        print("[OK] Da tao thanh cong loi tat ngoai Desktop: Vibe Nguoi Tot.lnk")
    else:
        print("[-] Khong the tao loi tat ngoai Desktop.")

