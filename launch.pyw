import sys
import os
import subprocess
import socket
import time

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)
sys.path.insert(0, PROJECT_DIR)

# 1. Tự động kiểm tra và cài đặt ngầm thư viện nếu máy mới chưa cài
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

# 2. Kiểm tra xem Server đã chạy trên port 8888 chưa
def is_port_in_use(port=8888):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except Exception:
        return False

if not is_port_in_use(8888):
    # Khởi chạy server hoàn toàn ẩn dưới nền bằng pythonw hoặc CREATE_NO_WINDOW
    python_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(python_dir, "pythonw.exe")
    exe = pythonw if os.path.exists(pythonw) else sys.executable
    
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    server_script = os.path.join(PROJECT_DIR, "run_server.py")
    
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
    for _ in range(25):
        time.sleep(0.1)
        if is_port_in_use(8888):
            break

# 3. Khởi chạy giao diện chính Desktop Client
if __name__ == "__main__":
    from src.client.client_app import run
    run(host="127.0.0.1", port=8888)

