import sys
import os

if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr is not None:
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.server.server import ChatServer

def safe_print(*args, **kwargs):
    if sys.stdout is not None:
        try:
            print(*args, **kwargs)
        except Exception:
            pass

if __name__ == "__main__":
    safe_print("---------------------------------------------------------")
    safe_print("  DO AN CHUYEN NGANH CONG NGHE PHAN MEM - NHOM 05")
    safe_print("  DE TAI: XAY DUNG UNG DUNG NHAN TIN VA TRUYEN THONG TIN")
    safe_print("---------------------------------------------------------")
    server = ChatServer(host="0.0.0.0", port=8888)
    server.start()

