# ĐỒ ÁN CHUYÊN NGÀNH CÔNG NGHỆ PHẦN MỀM
## ĐỀ TÀI: XÂY DỰNG ỨNG DỤNG NHẮN TIN VÀ TRUYỀN THÔNG TIN DESKTOP
### ỨNG DỤNG: VIBE NGƯỜI TỐT
**Nhóm thực hiện**: Nhóm 05 - Lớp: DCCNTT.14.5  
**Trường Đại học Công nghệ Đông Á - Khoa Công nghệ Thông tin**

---

### Danh sách thành viên nhóm:
1. **Vũ Duy Thái Sơn** *(Nhóm trưởng)* - MSV: `20231735`
2. **Vy Thế Mạnh** - MSV: `20231865`
3. **Vũ Minh Dân** - MSV: `20231833`
4. **Phạm Đức Tâm** - MSV: `20231715`
5. **Hữu** - Lớp: `DCCNTT.14.5`

---

## 🌟 Giới thiệu sản phẩm: Vibe Người Tốt

**Vibe Người Tốt** là ứng dụng nhắn tin desktop hiện đại, tốc độ cao và bảo mật được xây dựng theo kiến trúc đa nền tảng:
- **Giao diện Client**: React 18, TypeScript (Strict Mode), Vite, Tailwind CSS, Lucide Icons, chạy trên nền **Electron Desktop**.
- **Máy chủ Backend**: Python 3.13 TCP Socket đa luồng (Multi-threading), hỗ trợ giao tiếp qua mạng diện rộng **WAN (Internet)** qua đường hầm TCP `bore.pub:38888`.
- **Cơ sở dữ liệu**: SQLite (`src/server/chat_database.db`), bảo vệ mật khẩu bằng băm PBKDF2-HMAC-SHA256 (100.000 vòng lặp) kèm salt 16 bytes.
- **Biểu tượng thương hiệu**: Logo chính thức Cậu bé bút chì Shin-chan (`app.ico`, `logo.png`) hiển thị đồng bộ trên Desktop, thanh tiêu đề, màn hình chào mừng và hộp thoại đăng nhập.

---

## 🚀 Hướng dẫn khởi chạy nhanh (1-Click All-In-One)

### 1. Dành cho người dùng & Giảng viên chấm thi:
Chỉ cần nhấp đúp chuột vào file:
👉 **`CHAY_UNG_DUNG.bat`**

**Hệ thống sẽ tự động hoàn toàn:**
1. **Kiểm tra biểu tượng Desktop**: Nếu màn hình Desktop chưa có shortcut **Vibe Người Tốt**, hệ thống sẽ tự động tạo mới; nếu đã có sẵn thì giữ nguyên.
2. **Tự khởi động cùng Windows (Startup)**: Đăng ký Server WAN vào Windows Startup. Kể từ nay, mỗi khi máy tính bật lên là Server đã tự động chạy ngầm sẵn sàng.
3. **Kiểm tra máy chủ**: Tự động kích hoạt Server WAN (`127.0.0.1:8888` + `bore.pub:38888`) nếu chưa chạy.
4. **Mở ứng dụng Desktop**: Khởi chạy ngay cửa sổ ứng dụng **Vibe Người Tốt** trên màn hình.

---

## ⚡ Các tính năng nổi bật

### 1. Cơ chế Tự động hóa Thông minh (All-in-One Automation)
- **Tự động hóa Shortcut**: Nhận diện thông minh trên Desktop, không bao giờ tạo trùng lặp.
- **Server WAN ngầm vĩnh viễn**: Khởi động cùng Windows, không cần bật server thủ công mỗi lần nhắn tin.
- **Đồng bộ Git 2 giây (Auto-Update Listener)**:
  - Cứ mỗi 2 giây, ứng dụng tự động kiểm tra xem trên GitHub repository có bản cập nhật mới không.
  - Khi có cập nhật mới, ứng dụng hiển thị thông báo với 2 lựa chọn:
    - **`[Để sau]`**: Tiếp tục nhắn tin bình thường, không bao giờ ép buộc cập nhật.
    - **`[Cập nhật ngay]`**: Tự động pull code mới, biên dịch và khởi động lại phiên bản mới trong tích tắc.

### 2. Nhắn tin & Tương tác chuyên sâu (Interactive Messaging)
- **Nhắn tin văn bản thời gian thực**: Cá nhân 1-1 và Nhóm chat (Group Chat).
- **Trả lời trích dẫn (Reply / Quote)**: Trích dẫn tin nhắn gốc kèm tên người gửi, bấm vào tự cuộn đến tin nhắn cha.
- **Thả cảm xúc (Reactions)**: Thả và gỡ cảm xúc (❤️, 👍, 😂, 😮, 😢, 🔥) với bộ đếm số lượng trực tiếp.
- **Ghim tin nhắn (Pin Message)**: Ghim tin nhắn quan trọng lên đầu cuộc trò chuyện.
- **Thu hồi tin nhắn (Recall)**: Thu hồi tin nhắn ở cả 2 phía người gửi và người nhận.
- **Cloud cá nhân (Saved Messages)**: Lưu trữ ghi chú, tài liệu, hình ảnh cá nhân trên đám mây riêng biệt.
- **Tìm kiếm toàn cục (@username / #ID)**: Tra cứu nhanh mọi tài khoản trong hệ thống và bấm nút nhắn tin ngay.
- **Danh bạ & Bạn bè**: Gửi lời mời kết bạn, đồng ý/từ chối lời mời, hủy kết bạn và chặn người dùng làm phiền.
- **Trạng thái đối phương**: Chấm xanh Online và dòng chữ "Đang soạn tin..." (Typing indicator).

### 3. Đàm thoại Trực tuyến (Voice & Video Call Signaling)
- 📞 Gọi thoại (Voice Call) kết nối nhanh chóng.
- 📹 Gọi Video (Video Call) với đồng hồ đếm thời gian thực và quản lý trạng thái kết nối.

### 4. Tiện ích Desktop Chuyên nghiệp
- 🔒 **Khóa màn hình nhanh (`Ctrl + L`)**: Khóa ứng dụng tức thời bảo vệ sự riêng tư khi rời bàn làm việc.
- 📌 **Ghim cửa sổ luôn nổi (Always on Top)**: Ghim cửa sổ chat trên cùng để làm việc đa nhiệm.
- 🔄 **Làm mới dữ liệu (`Ctrl + R`)**: Nạp lại dữ liệu cuộc trò chuyện ngay lập tức.
- 🌓 **Giao diện Tối / Sáng (Dark / Light Mode)**: Chuyển đổi linh hoạt theo sở thích.

---

## 📁 Cấu trúc thư mục dự án

```
├── app.ico                    # Biểu tượng Windows Icon đa độ phân giải (Shin-chan)
├── logo.png                   # Logo chính thức của ứng dụng
├── CHAY_UNG_DUNG.bat          # File khởi chạy trọn gói 1-Click All-in-One
├── CHAY_SERVER_WAN.bat        # Khởi động Server WAN kèm đường hầm bore.pub:38888
├── DUNG_SERVER.bat            # Dọn dẹp và tắt toàn bộ tiến trình server và bore
├── CAP_NHAT.bat               # Đồng bộ mã nguồn thủ công từ GitHub
├── TAO_SHORTCUT_DESKTOP.bat   # Tạo lại biểu tượng lối tắt ngoài Desktop
│
├── frontend/                  # Mã nguồn ứng dụng Desktop (React + TypeScript + Electron)
│   ├── electron/              # Electron Main Process & Preload Bridge
│   │   ├── main.ts            # Quản lý cửa sổ, IPC, khởi chạy backend
│   │   ├── preload.ts         # contextBridge an toàn (contextIsolation: true)
│   │   ├── python_bridge.ts   # Cầu nối TCP Socket 4-byte BE Wire Client
│   │   └── updater.ts         # Dịch vụ lắng nghe Git 2 giây & tự động cập nhật
│   ├── src/                   # Giao diện người dùng React 18 + Tailwind CSS
│   │   ├── app/               # Entry point App.tsx & Router
│   │   ├── components/        # TitleBar, UpdateModal, Popout, các thành phần dùng chung
│   │   ├── features/chat/     # Sidebar danh sách hội thoại, ChatArea, Composer, Bubbles
│   │   ├── features/auth/     # Đăng nhập & Đăng ký tài khoản
│   │   ├── features/contacts/ # Danh bạ, Lời mời kết bạn, Chặn
│   │   ├── features/groups/   # Tạo nhóm chat
│   │   ├── features/calls/    # Giao diện cuộc gọi Voice / Video
│   │   ├── features/security/ # Màn hình khóa PIN Screen Lock
│   │   └── services/          # apiService (API Client)
│   ├── public/                # Logo, favicon và static assets
│   ├── package.json           # Cấu hình dependency và build script
│   └── vite.config.ts         # Cấu hình Vite build tool
│
├── src/server/                # Mã nguồn Python Core Backend
│   ├── server.py              # TCP Socket Server đa luồng (port 8888)
│   ├── database.py            # SQLite Database Manager
│   ├── chat_database.db       # Cơ sở dữ liệu SQLite (bảo tồn toàn bộ lịch sử)
│   └── uploads/               # Thư mục lưu trữ hình ảnh và tệp tin đính kèm
│
├── scripts/                   # Kịch bản tự động hóa hệ thống
│   ├── setup_all_in_one.py    # Kiểm tra desktop shortcut, Windows startup và server
│   ├── create_shortcut.py     # Tạo lối tắt Windows hỗ trợ Unicode
│   └── make_logo.py           # Bộ tạo logo và icon đa độ phân giải
│
└── docs/                      # Tài liệu và báo cáo kỹ thuật
    ├── BAO_CAO_HOAN_THANH_DO_AN.md # Báo cáo tổng kết đồ án chuyên ngành chi tiết
    └── MIGRATION_PLAN.md      # Tài liệu chi tiết kế hoạch và kết quả chuyển đổi kiến trúc
```

---

## 🤝 Bản quyền & Đóng góp
Dự án được xây dựng và hoàn thiện bởi **Nhóm 05 - DCCNTT.14.5 - Đại học Công nghệ Đông Á**.  
Mã nguồn lưu trữ tại GitHub: [https://github.com/Son3333/chat-online-](https://github.com/Son3333/chat-online-)
