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
Ứng dụng nhắn tin và truyền thông tin là một phần mềm Desktop hiện đại xây dựng trên nền tảng **Python + CustomTkinter + TCP Socket thời gian thực + SQLite Database**, được thiết kế theo phong cách giao diện phẳng tối/sáng hiện đại (tương tự Telegram, Discord, Slack), hỗ trợ hoạt động trực tuyến hoàn toàn qua **Mạng diện rộng WAN (Internet)**.

### Các tính năng chính:
- **Cơ chế 1-Click Tự động hóa**: Người dùng tải về chỉ cần nhấp đúp file `.bat`, ứng dụng sẽ tự động kiểm tra, cài đặt ngầm các thư viện cần thiết, tự động khởi động máy chủ trực tuyến và mở giao diện ứng dụng.
- **Tự động mở Server Online WAN**: Sử dụng công nghệ TCP Tunneling không giới hạn, tự động đưa máy chủ lên Internet (`bore.pub:28888`) giúp mọi máy tính ở các mạng WiFi, 4G khác nhau đều kết nối được ngay lập tức.
- **Xác thực người dùng thực tế**: Đăng ký tài khoản, đăng nhập an toàn với mật khẩu băm SHA-256 + Salt.
- **Tính năng Ghi nhớ tài khẩu & mật khẩu**: Tự động lưu thông tin đăng nhập cục bộ trên máy để lần sau vào chat tức thì.
- **Nút Sao chép địa chỉ Server Online 1-Chạm**: Nằm ngay trên thanh tiêu đề ứng dụng, giúp bạn dễ dàng gửi link phòng chat cho bạn bè chỉ với 1 cú click.
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
- **Giao diện hiện đại**:
  - Hỗ trợ chuyển đổi mượt mà giữa chế độ Giao diện Tối (Dark Mode) và Giao diện Sáng (Light Mode).

---

## 🚀 Hướng dẫn khởi chạy khi tải từ GitHub về

### 1. Dành cho người dùng (Khởi động 1-Click Online):
* Sau khi tải mã nguồn từ GitHub về (hoặc giải nén file ZIP), bạn chỉ cần **nhấp đúp chuột vào file**:
  👉 **`CHAY_UNG_DUNG.bat`**
* **Hệ thống sẽ tự động hoàn toàn:**
  1. Kiểm tra môi trường Python.
  2. Tự động cài đặt ngầm các thư viện cần thiết (`customtkinter`, `pillow`, `pyngrok`).
  3. Tự động khởi động Chat Server trực tuyến (Online WAN).
  4. Mở cửa sổ giao diện ứng dụng Desktop lên màn hình chính và kết nối thẳng vào Server Online!

---

### 2. Cách kết nối và chat cùng bạn bè qua Internet:
* **Máy Chủ (Host)**: Bấm `CHAY_UNG_DUNG.bat` (hoặc `CHAY_SERVER_WAN.bat`). Sau khi đăng nhập, nhấp nút **`🌐 bore.pub:28888 📋`** trên thanh tiêu đề để sao chép địa chỉ gửi cho bạn bè.
* **Máy Bạn Bè**:
  - Mở ứng dụng qua file `CHAY_UNG_DUNG.bat`.
  - Nếu muốn kết nối vào máy chủ riêng của bạn, nhấp vào: **`⚙️ Cài đặt IP Máy chủ (LAN / WAN / Internet)`**.
  - Nhập địa chỉ bạn gửi (Mặc định đã tự điền sẵn `bore.pub:28888`).
  - Bấm **Đăng ký** hoặc **Đăng nhập** $\rightarrow$ Có thể chat nhóm, chat riêng và gửi file xuyên Internet!

---

## 📁 Cấu trúc thư mục dự án

```
├── CHAY_UNG_DUNG.bat         # File thực thi 1-Click (Tự cài ngầm thư viện + bật Server Online ngầm + mở App)
├── CHAY_SERVER_WAN.bat       # Khởi động Chat Server mạng diện rộng WAN (Internet)
├── CHAY_SERVER.bat           # Khởi động Chat Server mạng nội bộ (Port 8888)
├── bore.exe                  # Tiện ích TCP Tunneling công cộng kết nối Internet không giới hạn
├── run_server_wan.py         # Mã nguồn khởi động Server Online WAN
├── run_server.py             # Mã nguồn khởi động Chat Server nội bộ
├── run_client.py             # Mã nguồn giao diện Desktop Client
├── launch.pyw                # Trình khởi chạy ngầm tự kết nối Server Online
├── requirements.txt          # Danh sách thư viện phụ thuộc
├── .gitignore                # File cấu hình bỏ qua rác khi đẩy lên GitHub
├── README.md                 # Tài liệu hướng dẫn sử dụng
│
├── src/
│   ├── server/
│   │   ├── server.py         # Multi-threaded TCP Socket Server (định tuyến packet JSON + framing)
│   │   ├── database.py       # SQLite Database (Users, Friends, Conversations, Messages, Files)
│   │   ├── chat_database.db  # CSDL SQLite (tự động khởi tạo bảng dữ liệu)
│   │   └── uploads/          # Thư mục lưu trữ tệp và ảnh được gửi qua ứng dụng
│   │
│   └── client/
│       ├── client_app.py     # Cửa sổ chính Desktop Client (giao diện Dark/Light Telegram-like)
│       ├── network.py        # Tầng Socket Client đa luồng gửi/nhận thời gian thực
│       └── ui/
│           ├── auth_frame.py         # Giao diện Đăng nhập / Đăng ký + Ghi nhớ mật khẩu
│           ├── main_window.py        # Giao diện chính (Sidebar, Header, Danh sách đoạn chat, Nút sao chép IP)
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
