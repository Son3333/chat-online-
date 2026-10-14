import sys
import os
import time
import threading

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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.server.server import ChatServer
from pyngrok import ngrok, conf

def start_wan_server():
    print("=================================================================")
    print("  ĐỒ ÁN CHUYÊN NGÀNH CÔNG NGHỆ PHẦN MỀM - NHÓM 05")
    print("  KHỞI ĐỘNG MÁY CHỦ TRUYỀN THÔNG MẠNG DIỆN RỘNG (WAN / INTERNET)")
    print("=================================================================")

    # 1. Khởi động ChatServer nội bộ trên port 8888
    local_port = 8888
    server = ChatServer(host="0.0.0.0", port=local_port)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    time.sleep(1)

    print("\n[1/2] Đã khởi chạy máy chủ TCP Socket nội bộ tại cổng 8888.")
    print("[2/2] Đang thiết lập đường hầm mạng Internet (WAN Tunnel qua Ngrok)...")

    # 2. Mở cổng TCP qua Ngrok
    tunnel_url = None
    try:
        tunnel = ngrok.connect(local_port, "tcp")
        tunnel_url = tunnel.public_url # e.g. "tcp://0.tcp.ap.ngrok.io:12345"
    except Exception as e:
        err_msg = str(e)
        if "authtoken" in err_msg.lower():
            print("\n⚠️ CHÚ Ý: Ngrok yêu cầu Authtoken miễn phí để mở cổng TCP qua Internet.")
            print("👉 Các bước đơn giản (Chỉ làm 1 lần duy nhất):")
            print("   1. Vào trang: https://dashboard.ngrok.com/ (Đăng ký nhanh bằng Google)")
            print("   2. Copy mã Your Authtoken (Ví dụ: 2tcxyz...)")
            token_input = input("   Nhập AuthToken của bạn vào đây (rồi nhấn Enter): ").strip()
            if token_input:
                ngrok.set_auth_token(token_input)
                try:
                    tunnel = ngrok.connect(local_port, "tcp")
                    tunnel_url = tunnel.public_url
                except Exception as ex2:
                    print(f"❌ Lỗi kết nối sau khi nhập token: {ex2}")
                    return
            else:
                print("Chưa nhập token. Máy chủ tiếp tục chạy ở chế độ mạng LAN nội bộ (0.0.0.0:8888).")
                server_thread.join()
                return
        else:
            print(f"❌ Lỗi khởi tạo đường hầm WAN: {err_msg}")
            print("Máy chủ vẫn tiếp tục hoạt động ở chế độ mạng LAN nội bộ.")
            server_thread.join()
            return

    if tunnel_url:
        # Tách domain và port từ tunnel_url: "tcp://0.tcp.ap.ngrok.io:12345"
        clean_url = tunnel_url.replace("tcp://", "")
        domain, port = clean_url.split(":")
        
        print("\n" + "=" * 65)
        print("🎉 MÁY CHỦ CHAT ĐÃ ĐƯỢC ĐƯA LÊN MẠNG WAN (INTERNET) THÀNH CÔNG!")
        print("=" * 65)
        print(f"  • Tên miền WAN (IP/Domain) : {domain}")
        print(f"  • Cổng WAN (Port)          : {port}")
        print("-" * 65)
        print("👉 HƯỚNG DẪN CÁC THÀNH VIÊN TRONG NHÓM KẾT NỐI TỪ XA:")
        print("   1. Mở ứng dụng Desktop Client.")
        print("   2. Nhấp vào: '⚙️ Cài đặt IP Máy chủ (Dùng mạng LAN / WAN / Internet)'")
        print(f"   3. Nhập chính xác:")
        print(f"      - IP / Domain : {domain}")
        print(f"      - Port        : {port}")
        print("   4. Bấm 'Đăng nhập' là có thể chat, gửi ảnh, gửi file xuyên Internet!")
        print("=" * 65)
        print("Nhấn Ctrl + C để dừng máy chủ.\n")

        # Lưu thông tin WAN ra file để Client có thể tự đọc nếu cần
        try:
            with open("wan_server_info.txt", "w", encoding="utf-8") as f:
                f.write(f"DOMAIN={domain}\nPORT={port}\nFULL={tunnel_url}\n")
        except Exception:
            pass

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nĐang tắt máy chủ WAN...")
            ngrok.disconnect(tunnel_url)
            server.stop()
            print("Đã dừng an toàn.")

if __name__ == "__main__":
    start_wan_server()

