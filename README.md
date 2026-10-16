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

[![CI/CD Pipeline](https://github.com/phatdat08/ChatApp_Nhom5/actions/workflows/ci.yml/badge.svg)](https://github.com/phatdat08/ChatApp_Nhom5/actions/workflows/ci.yml)
![Tests](https://img.shields.io/badge/Pytest-39%20Passed%20(100%25)-brightgreen)
![Security Audit](https://img.shields.io/badge/Bandit%20Audit-0%20Issues%20(Safe)-blue)
![Dependencies](https://img.shields.io/badge/pip--audit-0%20Vulnerabilities-success)
![Linter](https://img.shields.io/badge/Ruff-Passed-informational)

---

## 🌟 Giới thiệu sản phẩm (Desktop Application)
Ứng dụng nhắn tin và truyền thông tin là một phần mềm Desktop hiện đại xây dựng trên nền tảng **Python + CustomTkinter + TCP Socket thời gian thực + SQLite Database**, được thiết kế theo phong cách giao diện phẳng tối/sáng hiện đại (tương tự Telegram, Discord, Slack), hỗ trợ hoạt động trực tuyến hoàn toàn qua **Mạng diện rộng WAN (Internet)**.

### Các tính năng chính:
- **Cơ chế 1-Click Tự động hóa**: Người dùng tải về chỉ cần nhấp đúp file `.bat`, ứng dụng sẽ tự động kiểm tra, cài đặt ngầm các thư viện cần thiết, tự động khởi động máy chủ trực tuyến và mở giao diện ứng dụng.
- **Tự động mở Server Online WAN**: Sử dụng công nghệ TCP Tunneling không giới hạn, tự động đưa máy chủ lên Internet (`bore.pub:38888`) giúp mọi máy tính ở các mạng WiFi, 4G khác nhau đều kết nối được ngay lập tức.
- **Xác thực người dùng & Bảo mật**: Đăng ký tài khoản, kiểm tra độ mạnh mật khẩu (chữ hoa, chữ thường, số, ký tự đặc biệt), mật khẩu băm SHA-256 + Salt. Tự động forced logout tài khoản trên thiết bị cũ khi đăng nhập thiết bị mới.
- **Đàm thoại trực tuyến & Chia sẻ màn hình (Voice / Video Call & Screen Sharing)**:
  - 📞 **Gọi thoại (Voice Call)** thời gian thực với độ trễ thấp < 120ms.
  - 📹 **Gọi Video (Video Call)** độ nét cao (20-30 FPS) hiển thị song song PIP hai khung hình camera.
  - 🖥️ **Chia sẻ màn hình (Screen Sharing)**: Chuyển đổi linh hoạt từ camera sang chia sẻ trực tiếp toàn màn hình máy tính với đối phương.
- **Nhắn tin thời gian thực & Tương tác chuyên sâu (Interactive Messaging)**:
  - Nhắn tin cá nhân 1-1 và Nhắn tin nhóm (Group Chat) chống spam, kiểm soát tần suất tạo nhóm.
  - ↩️ **Trả lời / Trích dẫn tin nhắn (Reply / Quote)**: Hiển thị khung trích dẫn tin nhắn gốc kèm tên người gửi, bấm vào tự cuộn đến tin nhắn cha.
  - ❤️ **Thả biểu cảm tin nhắn (Message Reactions)**: Thả và gỡ cảm xúc (❤️, 👍, 😂, 😮, 😢, 😡) với huy hiệu đếm số lượng người thả.
  - 📌 **Ghim tin nhắn quan trọng (Pin Message)**: Ghim tin nhắn lên thanh tiêu đề hội thoại cho tất cả thành viên dễ theo dõi.
  - ☁️ **Không gian "Cloud của tôi" (Saved Messages)**: Lưu trữ tin nhắn, ghi chú, ảnh và tệp tài liệu cá nhân trên đám mây riêng biệt.
  - 🗑️ **Thu hồi tin nhắn (Unsend / Recall)**: Thu hồi tin nhắn đã gửi ở cả hai phía người gửi và người nhận.
  - 🚫 **Chặn người dùng (Block / Unblock)**: Chặn tài khoản gửi tin nhắn hoặc gọi điện làm phiền.
  - 💬 **Đang soạn tin (Typing indicator)**: Báo trạng thái đối phương đang gõ phím.
- **Bộ công cụ Desktop Chuyên nghiệp (Native Desktop Integration)**:
  - 📥 **Khay hệ thống (System Tray)**: Bấm nút [X] ứng dụng thu nhỏ chạy ngầm dưới khay; icon tự động hiện chấm đỏ đếm số tin nhắn chưa đọc kèm tooltip tóm tắt.
  - 📷 **Công cụ Chụp màn hình tích hợp (`Ctrl + Alt + A`)**: Kính lúp Pixel Loupe phóng đại từng điểm ảnh, thanh công cụ vẽ chú thích (Hình chữ nhật, Mũi tên, Chữ viết, Bộ đếm số bước `1-2-3`, Làm mờ nhạy cảm Mosaic/Blur). Tự lưu clipboard và gửi thẳng vào khung chat.
  - 🔍 **Thanh tìm kiếm & Lệnh nhanh Quick Switcher (`Ctrl + K`)**: Command Palette tìm kiếm tức thời hội thoại và thực thi lệnh tắt trong tích tắc.
  - 🔒 **Khóa bảo vệ nhanh Quick Lock (`Ctrl + L`)**: Khóa màn hình tức thời khi rời máy tính, yêu cầu mật khẩu để mở khóa.
  - 🪟 **Tách cửa sổ chat riêng (Pop-out Window)**: Mở cuộc trò chuyện trong một cửa sổ độc lập để theo dõi song song nhiều việc.
  - 📌 **Ghim cửa sổ luôn nổi trên cùng (Always on Top)**.
  - 🖥️ **Tự động xử lý rút màn hình phụ (Off-screen recovery)**: Tự phát hiện và đưa cửa sổ về màn hình chính nếu tọa độ lưu bị văng ra ngoài.
  - 🔔 **Thông báo Toast góc màn hình**: Pop-up thông báo hiện đại kèm avatar người gửi và tự đóng sau 4 giây.
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
├── .github/workflows/ci.yml  # Pipeline CI/CD tự động (Lint, Test, Package EXE)
├── pyproject.toml            # Cấu hình chuẩn hóa Ruff Linter và Pytest
├── tests/                    # Bộ kiểm thử tự động toàn diện (39 test cases, 100% Pass)
│   ├── test_calling_feature.py # Kiểm thử toàn diện Đàm thoại trực tuyến Voice & Video Call
│   ├── test_database.py      # Kiểm thử CSDL, mật khẩu, xác thực, danh bạ, tin nhắn
│   ├── test_network_server.py# Kiểm thử tích hợp Socket TCP, handshake, broadcast
│   ├── test_desktop_features.py# Kiểm thử Window Manager, phục hồi màn hình, formatters
│   └── test_ui_smoke.py      # Kiểm thử khói Giao diện, Theme, ô tìm kiếm, nhập liệu
├── reports/                  # Báo cáo kỹ thuật chi tiết sau kiểm toán
│   ├── bug-report.md         # Danh sách và giải pháp 10 lỗi phát hiện
│   ├── test-plan.md          # Kế hoạch và ma trận kiểm thử chi tiết (39 tests)
│   ├── test-results.md       # Kết quả kiểm thử chi tiết (39 passed, 100%)
│   ├── security-audit.md     # Báo cáo an ninh Bandit (0 Issues) và pip-audit
│   └── ci-cd-setup.md        # Hướng dẫn quy trình CI/CD và debug GitHub Actions
│
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
│       ├── call/             # Mô-đun Đàm thoại trực tuyến Voice & Video Call
│       │   └── call_window.py    # Giao diện gọi thoại/video, chia sẻ màn hình, phát chuông, streaming
│       ├── desktop/          # Bộ mô-đun tích hợp sâu hệ thống Desktop
│       │   ├── tray.py           # Quản lý System Tray, icon động, badge đếm tin chưa đọc
│       │   ├── screenshot.py     # Chụp màn hình (Ctrl+Alt+A), Pixel loupe, thanh vẽ chú thích
│       │   ├── quick_switcher.py # Command Palette tìm nhanh hội thoại & lệnh tắt (Ctrl+K)
│       │   ├── quick_lock.py     # Khóa màn hình nhanh bảo vệ riêng tư (Ctrl+L)
│       │   ├── popout_window.py  # Tách khung chat độc lập đa cửa sổ
│       │   ├── toast.py          # Thông báo Toast hiện đại góc dưới màn hình
│       │   └── window_manager.py # Quản lý tọa độ, Always on Top, chống văng màn hình phụ
│       └── ui/
│           ├── auth_frame.py         # Giao diện Đăng nhập / Đăng ký + Ghi nhớ mật khẩu
│           ├── main_window.py        # Giao diện chính (Sidebar, Header, Danh sách đoạn chat, Nút sao chép IP)
│           ├── chat_bubble.py        # Bong bóng chat tin nhắn, reply/quote, reactions, ghim tin nhắn
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

---

## 🧪 Kiểm thử tự động & CI/CD Pipeline

Dự án tích hợp đầy đủ bộ công cụ kiểm thử hiện đại và tự động hóa CI/CD:

### 1. Lệnh chạy kiểm thử tự động (Pytest)
```powershell
# Chạy toàn bộ 33 test cases kèm thống kê độ bao phủ (Coverage)
python -m pytest --cov=src --cov-report=term-missing tests/
```

### 2. Lệnh kiểm tra chất lượng mã nguồn & Linter (Ruff)
```powershell
python -m ruff check src
```

### 3. Lệnh quét an ninh mã nguồn (Bandit)
```powershell
python -m bandit -r src -ll
```

### 4. Lệnh kiểm tra lỗ hổng phụ thuộc (pip-audit)
```powershell
python -m pip_audit -r requirements.txt
```

### 5. Xem các báo cáo kỹ thuật chi tiết
- 📋 [Báo cáo Kiểm toán và Sửa lỗi](reports/bug-report.md)
- 📝 [Kế hoạch và Chiến lược Kiểm thử](reports/test-plan.md)
- 📊 [Kết quả Kiểm thử Tự động Chi tiết](reports/test-results.md)
- 🛡️ [Đánh giá An ninh & Bảo mật Phần mềm](reports/security-audit.md)
- 🚀 [Hướng dẫn Thiết lập & Vận hành CI/CD](reports/ci-cd-setup.md)

