# ĐỒ ÁN CHUYÊN NGÀNH CÔNG NGHỆ PHẦN MỀM
## ĐỀ TÀI: XÂY DỰNG ỨNG DỤNG NHẮN TIN VÀ TRUYỀN THÔNG TIN
### Nhóm thực hiện: Nhóm 05 - Lớp: DCCNTT.14.5
**Trường Đại học Công nghệ Đông Á - Khoa Công nghệ Thông tin**

---

### Danh sách thành viên nhóm:
1. **Vũ Duy Thái Sơn** *(Nhóm trưởng)* - MSV: `20231735`
2. **Vy Thế Mạnh** - MSV: `20231865`
3. **Vũ Minh Dân** - MSV: `20231833`
4. **Phạm Đức Tâm** - MSV: `20231715`
5. **Hữu** - Lớp: `DCCNTT.14.5`

---

## 🌟 Giới thiệu sản phẩm (Desktop Application)
Ứng dụng nhắn tin và truyền thông tin là một phần mềm Desktop hiện đại xây dựng trên nền tảng **Python + CustomTkinter + TCP Socket thời gian thực + SQLite Database**, được thiết kế theo phong cách giao diện phẳng tối/sáng hiện đại (tương tự Telegram, Discord, Slack), hỗ trợ hoạt động trên cả mạng nội bộ **LAN** và mạng diện rộng **WAN (Internet)**.

### Các tính năng chính:
- **Cơ chế 1-Click Tự động hóa**: Người dùng tải về chỉ cần nhấp đúp file `.bat`, ứng dụng sẽ tự động kiểm tra, cài đặt ngầm các thư viện cần thiết, tự động khởi động server nền và mở giao diện ứng dụng lên màn hình.
- **Xác thực người dùng**: Đăng ký tài khoản, đăng nhập an toàn với mật khẩu băm SHA-256 + Salt.
- **Hỗ trợ Đăng nhập 1-Click**: Cung cấp sẵn 5 nút đăng nhập nhanh cho 5 thành viên của nhóm (`Sơn (TN)`, `Mạnh`, `Dân`, `Tâm`, `Hữu`) giúp việc kiểm thử và báo cáo bảo vệ đồ án diễn ra nhanh chóng.
- **Nhắn tin thời gian thực (Real-time TCP Socket)**:
  - Nhắn tin cá nhân 1-1 với bạn bè.
  - Nhắn tin nhóm (Group Chat) nhiều thành viên.
  - Hiển thị bong bóng chat với thời gian, trạng thái gửi `✓`.
  - Hỗ trợ thanh biểu tượng cảm xúc (Emoji bar) nhanh: 😊, 👍, ❤️, 🎉, 🔥, 😂...
  - Thông báo trạng thái người dùng đang soạn tin nhắn (*Typing indicator*).
- **Truyền tải và chia sẻ tệp tin đa phương tiện**:
  - Gửi hình ảnh (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`).
  - Gửi tài liệu và tệp nén (`.pdf`, `.docx`, `.xlsx`, `.zip`, `.txt`...).
  - Tải về tệp tin trực tiếp về máy tính an toàn kèm định lượng dung lượng (KB/MB).
- **Hỗ trợ Mạng diện rộng WAN (Internet)**:
  - Máy chủ hỗ trợ mở cổng toàn cầu qua TCP Tunnel (`run_server_wan.py`).
  - Client có tính năng `⚙️ Cài đặt IP Máy chủ` để kết nối từ xa từ bất kỳ đâu.
- **Giao diện hiện đại**:
  - Hỗ trợ chuyển đổi mượt mà giữa chế độ Giao diện Tối (Dark Mode) và Giao diện Sáng (Light Mode).

---

## 🚀 Hướng dẫn khởi chạy khi tải từ GitHub về

### 1. Dành cho người dùng thông thường (Zero Configuration):
* Sau khi tải mã nguồn từ GitHub về (hoặc giải nén file ZIP), bạn chỉ cần **nhấp đúp chuột vào file**:
  👉 **`CHAY_UNG_DUNG.bat`**
* **Hệ thống sẽ tự động hoàn toàn:**
  1. Kiểm tra môi trường Python.
  2. Tự động cài đặt ngầm các thư viện cần thiết (`customtkinter`, `pillow`, `pyngrok`).
  3. Tự động khởi động Chat Server chạy ngầm trong suốt dưới nền.
  4. Mở cửa sổ giao diện ứng dụng Desktop lên màn hình chính.

---

### 2. Cách Chat qua Mạng diện rộng WAN (Internet giữa các máy tính khác nhau):
* **Bước 1 (Máy làm Server)**: Nhấp đúp vào **`CHAY_SERVER_WAN.bat`**. Cửa sổ sẽ hiển thị địa chỉ WAN công khai (Ví dụ: `0.tcp.ap.ngrok.io`, cổng `12345`).
* **Bước 2 (Các máy thành viên ở xa)**:
  - Mở ứng dụng qua file `CHAY_UNG_DUNG.bat`.
  - Nhấp vào dòng: **`⚙️ Cài đặt IP Máy chủ (Dùng mạng LAN / WAN / Internet)`**.
  - Nhập địa chỉ Domain và Port mà máy chủ đã cấp.
  - Bấm **Đăng nhập** $\rightarrow$ Có thể chat nhóm, chat riêng và gửi file xuyên Internet!

---

## 📁 Cấu trúc thư mục dự án

```
├── CHAY_UNG_DUNG.bat         # File thực thi 1-Click (Tự cài ngầm thư viện + bật Server ngầm + mở App)
├── CHAY_SERVER.bat           # Khởi động Chat Server mạng nội bộ (Port 8888)
├── CHAY_SERVER_WAN.bat       # Khởi động Chat Server mạng diện rộng WAN (Internet)
├── run_server.py             # Mã nguồn khởi động Chat Server
├── run_server_wan.py         # Mã nguồn khởi động Server kèm TCP Tunnel WAN
├── run_client.py             # Mã nguồn giao diện Desktop Client
├── launch.pyw                # Trình khởi chạy ngầm không hiện cửa sổ đen
├── requirements.txt          # Danh sách thư viện phụ thuộc
├── .gitignore                # File cấu hình bỏ qua rác khi đẩy lên GitHub
├── README.md                 # Tài liệu hướng dẫn sử dụng
│
├── src/
│   ├── server/
│   │   ├── server.py         # Multi-threaded TCP Socket Server (định tuyến packet JSON + framing)
│   │   ├── database.py       # SQLite Database (Users, Friends, Conversations, Messages, Files)
│   │   ├── chat_database.db  # CSDL SQLite (đã tự động tạo sẵn tài khoản 5 thành viên nhóm)
│   │   └── uploads/          # Thư mục lưu trữ tệp và ảnh được gửi qua ứng dụng
│   │
│   └── client/
│       ├── client_app.py     # Cửa sổ chính Desktop Client (giao diện Dark/Light Telegram-like)
│       ├── network.py        # Tầng Socket Client đa luồng gửi/nhận thời gian thực
│       └── ui/
│           ├── auth_frame.py         # Giao diện Đăng nhập / Đăng ký + Nút Đăng nhập 1-Click
│           ├── main_window.py        # Giao diện chính (Sidebar, Header, Danh sách đoạn chat)
│           ├── chat_bubble.py        # Bong bóng chat tin nhắn, xem/tải ảnh & tệp tài liệu
│           └── create_group_dialog.py# Hộp thoại tạo nhóm chat mới
│
└── BÁO CÁO CÁC CHƯƠNG ĐỒ ÁN (FILE WORD .DOCX ĐỘC LẬP):
    ├── BÁO CÁO ĐỒ ÁN CHUYÊN NGÀNH - CHƯƠNG 1 - NHÓM 5.docx
    ├── BÁO CÁO ĐỒ ÁN CHUYÊN NGÀNH - CHƯƠNG 2 - NHÓM 5.docx
    ├── BÁO CÁO ĐỒ ÁN CHUYÊN NGÀNH - CHƯƠNG 3 - NHÓM 5.docx
    ├── BÁO CÁO ĐỒ ÁN CHUYÊN NGÀNH - CHƯƠNG 4 - NHÓM 5.docx
    ├── BÁO CÁO ĐỒ ÁN CHUYÊN NGÀNH - CHƯƠNG 5 - KẾT LUẬN - NHÓM 5.docx
    └── Nhóm-Lớp-KẾ HOẠCH THỰC HIỆN ĐỒ ÁN.docx
```
