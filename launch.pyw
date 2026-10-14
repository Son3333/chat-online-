import sys
import os
import subprocess
import socket
import time

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)
sys.path.insert(0, PROJECT_DIR)

# 1. TỰ ĐỘNG ĐỒNG BỘ BẢN MỚI NHẤT TỪ GITHUB (TRONG SUỐT HOÀN TOÀN)
def auto_update_from_github():
    # Trường hợp 1: Máy có kho Git (.git)
    if os.path.exists(os.path.join(PROJECT_DIR, ".git")):
        try:
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=PROJECT_DIR,
                timeout=4,
                creationflags=flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return
        except Exception:
            pass

    # Trường hợp 2: Máy tải bản ZIP không có Git
    version_file = os.path.join(PROJECT_DIR, ".version")
    current_version = ""
    if os.path.exists(version_file):
        try:
            with open(version_file, "r", encoding="utf-8") as f:
                current_version = f.read().strip()
        except Exception:
            pass

    try:
        import urllib.request
        import json
        import zipfile
        import io
        import shutil

        api_url = "https://api.github.com/repos/Son3333/chat-online-/commits/main"
        req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            latest_sha = data.get("sha", "")

        if latest_sha and latest_sha != current_version:
            zip_url = "https://github.com/Son3333/chat-online-/archive/refs/heads/main.zip"
            req_zip = urllib.request.Request(zip_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req_zip, timeout=15) as resp:
                zip_bytes = resp.read()

            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
                root_prefix = "chat-online--main/"
                for member in z.namelist():
                    if member.startswith(root_prefix) and member != root_prefix:
                        rel_path = member[len(root_prefix):]
                        if not rel_path:
                            continue
                        target_path = os.path.join(PROJECT_DIR, rel_path)
                        if member.endswith("/"):
                            os.makedirs(target_path, exist_ok=True)
                        else:
                            if rel_path in ["src/server/chat_database.db", "user_credentials.json", "server_config.json"]:
                                if os.path.exists(target_path):
                                    continue
                            os.makedirs(os.path.dirname(target_path), exist_ok=True)
                            with z.open(member) as src, open(target_path, "wb") as dst:
                                shutil.copyfileobj(src, dst)

            with open(version_file, "w", encoding="utf-8") as f:
                f.write(latest_sha)
    except Exception:
        pass

# Thực hiện đồng bộ ngầm
auto_update_from_github()

# 2. Tự động kiểm tra và cài đặt ngầm thư viện nếu máy mới chưa cài
try:
    import customtkinter
    import PIL
except ImportError:
    startupinfo = None
    flags = 0
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0 # SW_HIDE
        flags = subprocess.CREATE_NO_WINDOW
    try:
        req_file = os.path.join(PROJECT_DIR, "requirements.txt")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_file, "--quiet"],
            cwd=PROJECT_DIR,
            startupinfo=startupinfo,
            creationflags=flags
        )
    except Exception:
        pass

# 3. Kiểm tra xem Server đã chạy trên port 8888 chưa
def is_port_in_use(port=8888):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except Exception:
        return False

if not is_port_in_use(8888):
    # Khởi chạy MÁY CHỦ ONLINE (WAN) hoàn toàn ẩn dưới nền
    python_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(python_dir, "pythonw.exe")
    exe = pythonw if os.path.exists(pythonw) else sys.executable
    
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    server_script = os.path.join(PROJECT_DIR, "run_server_wan.py")
    
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        
    subprocess.Popen(
        [exe, server_script],
        cwd=PROJECT_DIR,
        startupinfo=startupinfo,
        creationflags=flags
    )
    
    # Chờ server mở port
    for _ in range(35):
        time.sleep(0.1)
        if is_port_in_use(8888):
            break

# 4. Lấy thông tin địa chỉ Online WAN để kết nối xuyên Internet
wan_host = "bore.pub"
wan_port = 28888
info_file = os.path.join(PROJECT_DIR, "wan_server_info.txt")

for _ in range(30):
    if os.path.exists(info_file):
        try:
            with open(info_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("DOMAIN="):
                        wan_host = line.strip().split("=")[1]
                    elif line.startswith("PORT="):
                        wan_port = int(line.strip().split("=")[1])
            break
        except Exception:
            pass
    time.sleep(0.1)

# 5. Khởi chạy giao diện chính Desktop Client kết nối Online
if __name__ == "__main__":
    from src.client.client_app import run
    run(host=wan_host, port=wan_port)
