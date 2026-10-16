import sys
import os
import json
import socket
import subprocess
import time

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)
sys.path.insert(0, PROJECT_DIR)

def is_port_in_use(port=8888, host='127.0.0.1'):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.4)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def get_target_server():
    if is_port_in_use(8888, '127.0.0.1'):
        return "127.0.0.1", 8888

    target_host = "bore.pub"
    target_port = 38888

    wan_script = os.path.join(PROJECT_DIR, "run_server_wan.py")
    if os.path.exists(wan_script):
        try:
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.Popen(
                [sys.executable, wan_script],
                cwd=PROJECT_DIR,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=flags
            )
            for _ in range(15):
                time.sleep(0.2)
                if is_port_in_use(8888, '127.0.0.1'):
                    return "127.0.0.1", 8888
        except Exception:
            pass

    return target_host, target_port

def main():
    try:
        import customtkinter
        import PIL
    except ImportError:
        sys.exit(1)

    try:
        host, port = get_target_server()
        from src.client.client_app import run
        run(host=host, port=port)
    except Exception as e:
        sys.exit(1)

if __name__ == "__main__":
    main()

