import sys
import os
import json
import time
import threading
import subprocess
import re
import urllib.request
import zipfile
import io

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

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

from src.server.server import ChatServer

def safe_log(msg: str):
    if sys.stdout is not None:
        try:
            print(msg)
        except Exception:
            try:
                print(msg.encode('ascii', 'replace').decode('ascii'))
            except Exception:
                pass

def ensure_bore_binary() -> str:
    """Đảm bảo file bore.exe sẵn sàng để mở cổng TCP Internet tự do không cần thẻ."""
    bore_path = os.path.join(PROJECT_DIR, "bore.exe")
    if os.path.exists(bore_path):
        return bore_path
    try:
        safe_log("[*] Dang tai tien ich TCP Tunneling bore.exe...")
        url = "https://github.com/ekzhang/bore/releases/download/v0.5.2/bore-v0.5.2-x86_64-pc-windows-msvc.zip"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            z.extractall(PROJECT_DIR)
        if os.path.exists(bore_path):
            safe_log("[+] Da tai thanh cong bore.exe!")
            return bore_path
    except Exception as e:
        safe_log(f"[-] Khong the tai bore.exe tu dong: {e}")
    return None

def start_wan_server():
    safe_log("=================================================================")
    safe_log("  DO AN CHUYEN NGANH CONG NGHE PHAN MEM - NHOM 05")
    safe_log("  KHOI DONG MAY CHU TRUYEN THONG MANG DIEN RONG (WAN / INTERNET)")
    safe_log("=================================================================")

    # 1. Khởi động ChatServer nội bộ trên port 8888
    local_port = 8888
    server = ChatServer(host="0.0.0.0", port=local_port)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    safe_log("\n[1/2] Da khoi chay may chu TCP Socket noi bo tai cong 8888.")
    safe_log("[2/2] Dang thiet lap duong ham mang Internet (WAN TCP Tunnel)...")

    domain = None
    port = None
    tunnel_proc = None

    # 2. Mở cổng TCP Online qua Bore (Ưu tiên 1 - Không cần thẻ tín dụng, không cần token)
    bore_path = ensure_bore_binary()
    if bore_path and os.path.exists(bore_path):
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        preferred_ports = [38888, 48888, 28888, 58888]
        for p in preferred_ports:
            try:
                safe_log(f"[*] Dang thu mo cong WAN co dinh: bore.pub:{p}...")
                tunnel_proc = subprocess.Popen(
                    [bore_path, "local", str(local_port), "--to", "bore.pub", "--port", str(p)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=flags
                )
                for _ in range(25):
                    line = tunnel_proc.stdout.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    safe_log(f"   [Tunnel] {line.strip()}")
                    if "listening at" in line:
                        m = re.search(r'listening at ([\w\.-]+):(\d+)', line)
                        if m:
                            domain, port = m.group(1), int(m.group(2))
                            break
                    elif "already in use" in line or "error" in line.lower():
                        break
                if domain and port:
                    break
                else:
                    try:
                        tunnel_proc.terminate()
                    except Exception:
                        pass
            except Exception as e:
                safe_log(f"[-] Loi thu cong {p}: {e}")

    # Fallback nếu bore không mở được port mong muốn
    if not domain or not port:
        safe_log("[!] Bore fallback: Thu mo cong ngau nhien...")
        try:
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            tunnel_proc = subprocess.Popen(
                [bore_path, "local", str(local_port), "--to", "bore.pub"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=flags
            )
            for _ in range(40):
                line = tunnel_proc.stdout.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                safe_log(f"   [Tunnel] {line.strip()}")
                if "listening at" in line:
                    m = re.search(r'listening at ([\w\.-]+):(\d+)', line)
                    if m:
                        domain, port = m.group(1), int(m.group(2))
                        break
        except Exception:
            pass

    if domain and port:
        safe_log("\n" + "=" * 65)
        safe_log("MAY CHU CHAT DA DUOC DUA LEN MANG WAN (INTERNET) THANH CONG!")
        safe_log("=" * 65)
        safe_log(f"  * Ten mien WAN (IP/Domain) : {domain}")
        safe_log(f"  * Cong WAN (Port)          : {port}")
        safe_log("-" * 65)
        safe_log("HUONG DAN CAC BAN KHAC KET NOI TU XA:")
        safe_log(f"  Dia chi ket noi: {domain}:{port}")
        safe_log("=" * 65)

        # Ghi ra file wan_server_info.txt cho các máy trạm từ xa tham khảo
        try:
            info_file = os.path.join(PROJECT_DIR, "wan_server_info.txt")
            with open(info_file, "w", encoding="utf-8") as f:
                f.write(f"DOMAIN={domain}\nPORT={port}\nFULL={domain}:{port}\n")
        except Exception:
            pass

        # Luôn đọc cạn buffer stdout của bore trong thread riêng để tránh tràn bộ đệm làm bore bị treo
        def _drain_tunnel_pipe(proc):
            try:
                while proc.poll() is None:
                    line = proc.stdout.readline()
                    if not line:
                        break
            except Exception:
                pass
        threading.Thread(target=_drain_tunnel_pipe, args=(tunnel_proc,), daemon=True).start()

        # Watchdog: Tu dong phuc hoi duong ham WAN ngay lap tuc neu bi rot mang hoac bore thoat
        def _tunnel_watchdog():
            nonlocal tunnel_proc
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            while True:
                time.sleep(3)
                if tunnel_proc is None or tunnel_proc.poll() is not None:
                    safe_log("[!] Duong ham WAN bi giam doan! Dang tu dong phuc hoi bore.pub:38888...")
                    try:
                        new_proc = subprocess.Popen(
                            [bore_path, "local", str(local_port), "--to", "bore.pub", "--port", str(port or 38888)],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            creationflags=flags
                        )
                        time.sleep(1.5)
                        if new_proc.poll() is None:
                            tunnel_proc = new_proc
                            threading.Thread(target=_drain_tunnel_pipe, args=(tunnel_proc,), daemon=True).start()
                            safe_log("[+] Da phuc hoi duong ham WAN thanh cong!")
                    except Exception as ex:
                        safe_log(f"[-] Loi phuc hoi duong ham: {ex}")
        threading.Thread(target=_tunnel_watchdog, daemon=True).start()

        # Keepalive: Gui ping giu ket noi bore.pub moi 35 giay tranh bi server ngat do idle
        def _keepalive_loop():
            import socket
            while True:
                time.sleep(35)
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(2.0)
                        s.connect(("bore.pub", port or 38888))
                except Exception:
                    pass
        threading.Thread(target=_keepalive_loop, daemon=True).start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            safe_log("\nDang tat may chu WAN...")
            if tunnel_proc:
                tunnel_proc.terminate()
            server.stop()
            safe_log("Da dung an toan.")
    else:
        safe_log("[-] Khong the mo duong ham WAN tu dong. May chu tiep tuc chay o che do LAN.")
        server_thread.join()

if __name__ == "__main__":
    start_wan_server()
