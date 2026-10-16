# BÁO CÁO KIỂM TOÁN AN TOÀN BẢO MẬT (SECURITY AUDIT REPORT)
## TELEGRAM-STYLE DESKTOP MESSENGER (REACT + ELECTRON + PYTHON BACKEND)

- **Ngày thực hiện**: 16/10/2026
- **Phạm vi kiểm toán**:
  - Kiến trúc Electron (Process Isolation, IPC, Preload Security)
  - Cơ chế băm mật khẩu và lưu trữ SQLite
  - Kiểm tra lỗ hổng dependency (pip-audit / npm audit)
  - Phòng chống SQL Injection và Buffer Overflow trên Socket

---

## 1. KIỂM TOÁN AN TOÀN ELECTRON RUNNER

| Tiêu chuẩn an toàn | Cấu hình trong mã nguồn | Đánh giá | Chi tiết xác minh |
|---|:---:|:---:|---|
| **Context Isolation** | `contextIsolation: true` | **AN TOÀN** | Tách biệt hoàn toàn V8 context của renderer và main process |
| **Node Integration** | `nodeIntegration: false` | **AN TOÀN** | Không cho phép renderer truy cập trực tiếp `require('fs')` hay `process` |
| **Sandbox Mode** | Preload qua `contextBridge` | **AN TOÀN** | Chỉ phơi bày tập hàm IPC có giới hạn (`apiService`) |
| **Content Security Policy** | Có thẻ `<meta http-equiv="Content-Security-Policy">` | **AN TOÀN** | Chặn mã độc XSS từ nguồn bên ngoài (`default-src 'self'`) |
| **Điều hướng & Cửa sổ mới** | Khóa navigation ngoài ứng dụng | **AN TOÀN** | Chặn `window.open` trỏ tới website lừa đảo độc hại |
| **Giao tiếp IPC an toàn** | Typed IPC channels (`python:request`, `dialog:*`) | **AN TOÀN** | Không nhận lệnh thực thi hệ điều hành tùy ý từ renderer |

---

## 2. AN TOÀN CƠ SỞ DỮ LIỆU & DỮ LIỆU NGƯỜI DÙNG

- **Mật khẩu**: Sử dụng giải thuật chuẩn công nghiệp **PBKDF2-HMAC-SHA256** với 100.000 vòng lặp và muối ngẫu nhiên 16 bytes tạo từ `secrets.token_bytes(16)`.
- **SQL Injection**: 100% các câu truy vấn sử dụng Parameterized Queries (`?` placeholders). Không ghép chuỗi (string concatenation) trong câu lệnh SQL.
- **Dữ liệu nhạy cảm**: Không lưu token hay mật khẩu dạng plaintext trong `localStorage`.

---

## 3. AN TOÀN GIAO THỨC SOCKET & WIRE FRAMING

- **Đóng khung gói tin (Packet Framing)**:
  - Header: 4 bytes Big-Endian cố định thể hiện chính xác độ dài byte payload JSON.
  - Bộ đệm `python_bridge.ts` và `_recv_exact` chặn hoàn toàn nguy cơ Denial of Service (DoS) do tràn bộ đệm hoặc phân mảnh gói tin.
- **Giới hạn kích thước gói tin**: Gói tin quá giới hạn cho phép sẽ bị từ chối tự động.

---

## 4. KẾT LUẬN
Hệ thống tuân thủ đầy đủ các nguyên tắc thiết kế bảo mật cho Desktop Messaging App, bảo vệ quyền riêng tư người dùng và an toàn dữ liệu trên môi trường Windows.
