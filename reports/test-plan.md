# KẾ HOẠCH KIỂM THỬ TỰ ĐỘNG (TEST PLAN & STRATEGY)

**Dự án**: Ứng dụng nhắn tin & Truyền thông tin Desktop (Python / CustomTkinter / TCP Socket)  
**Phiên bản**: v2.5.0  
**Tác giả**: QA Automation & DevOps Team  
**Ngày phê duyệt**: 16/10/2026  

---

## 1. MỤC TIÊU KIỂM THỬ (TEST OBJECTIVES)
1. Đảm bảo 100% các chức năng cốt lõi (Xác thực, Mã hóa mật khẩu, Quản lý danh bạ, Tin nhắn thời gian thực, Phản ứng biểu cảm, Lưu trữ đám mây, Đồng bộ cửa sổ) hoạt động chính xác theo đặc tả.
2. Kiểm tra tính ổn định của giao thức mạng TCP Socket và khả năng chịu tải, giới hạn tốc độ (rate limiting) khi khởi tạo nhóm/gửi tin nhắn.
3. Đảm bảo không xảy ra hiện tượng Crash hoặc đóng đột ngột (Unhandled Exception) ở tầng giao diện máy tính người dùng.
4. Đạt tỷ lệ bao phủ mã nguồn (Code Coverage) trên 50% toàn dự án và trên 85% cho tầng Database/Core Logic.
5. Tích hợp kiểm thử liên tục vào quy trình CI/CD qua GitHub Actions để tự động kiểm tra mỗi khi có commit hoặc pull request.

---

## 2. PHẠM VI KIỂM THỬ (TEST SCOPE)

### 2.1 Trong phạm vi (In-Scope)
- **Cơ sở dữ liệu (Database Layer)**:
  - Kiểm tra độ phức tạp của mật khẩu (Password Policy: chữ hoa, chữ thường, số, ký tự đặc biệt, độ dài tối thiểu 8 ký tự).
  - Thuật toán băm mật khẩu PBKDF2-HMAC-SHA256 kèm salt độc lập.
  - Vòng đời tài khoản: Đăng ký, đăng nhập sai/đúng, tìm kiếm người dùng theo username/ID.
  - Vòng đời quan hệ bạn bè: Gửi yêu cầu kết bạn, chấp nhận, từ chối, chặn và bỏ chặn 2 chiều.
  - Vòng đời hội thoại và tin nhắn: Tạo hội thoại 1-1, gửi tin, trích dẫn trả lời, thả cảm xúc emoji, ghim tin nhắn, thu hồi tin nhắn, truyền file lên cloud ("Truyền File"), cascade deletion.
- **Mạng và Máy chủ (Network & Protocol Integration)**:
  - Cơ chế bắt tay kết nối client - server TCP.
  - Giao thức mã hóa JSON-delimited protocol qua Socket.
  - Luồng đăng ký / đăng nhập qua socket thời gian thực.
  - Giao nhận tin nhắn tức thì giữa 2 client đang online.
  - Cơ chế phát sóng chỉ báo đang gõ phím (Typing Indicator broadcast).
  - Giới hạn tốc độ tạo nhóm chat (Rate Limiting).
- **Tính năng Desktop & Hệ điều hành (Desktop OS Features)**:
  - Lưu và khôi phục tọa độ cửa sổ `window_state.json`.
  - Cơ chế phục hồi vị trí cửa sổ khi ngắt kết nối màn hình phụ (Multi-monitor recovery).
  - Định dạng hiển thị kích thước tệp tin (B, KB, MB, GB).
  - Phân tích và phát hiện tin nhắn chứa thuần Emoji để phóng to icon.
  - Định dạng tem thời gian tin nhắn.
- **Kiểm thử Giao diện khói (UI Smoke Testing)**:
  - Chuyển đổi trạng thái giao diện Dark/Light mode và bảng mã màu.
  - Chuẩn hóa bộ lọc tìm kiếm (tiền tố `@` và `#`).
  - Xác thực độ dài và tính hợp lệ của ô nhập liệu tin nhắn.

### 2.2 Ngoài phạm vi (Out-of-Scope)
- Kiểm thử thiết bị phần cứng thực tế (Camera/Microphone vật lý) trong môi trường CI headless (được giả lập hoặc kiểm tra cục bộ).
- Stress test vượt ngưỡng 10.000 kết nối đồng thời trên một máy trạm đơn lẻ.

---

## 3. CHIẾN LƯỢC KIỂM THỬ (TEST STRATEGY)

```
        +----------------------------------------+
        |         E2E / Desktop Smoke UI        |  (3 tests)
        +----------------------------------------+
        |     Network & Protocol Integration     |  (5 tests)
        +----------------------------------------+
        |    Desktop OS & Core Formatter Logic   |  (5 tests)
        +----------------------------------------+
        |       Database & Security Rules        |  (20 tests)
        +----------------------------------------+
```

1. **Unit Testing**:
   - Kiểm tra độc lập các hàm xử lý dữ liệu, kiểm tra mật khẩu, định dạng thời gian và kích thước file không phụ thuộc mạng.
   - Cơ sở dữ liệu SQLite trong bộ nhớ (`:memory:`) hoặc file test tạm thời trong thư mục biệt lập được dọn dẹp sau mỗi test fixture.
2. **Integration Testing**:
   - Khởi động server thật trên cổng động (`port=0`) do hệ điều hành cấp phát tự động để tránh xung đột cổng với daemon đang chạy.
   - Kết nối 2 client socket thật để gửi nhận gói tin JSON trực tiếp qua loopback `127.0.0.1`.
3. **Static Analysis & Security Scanning**:
   - Sử dụng **Ruff** để kiểm soát style code, import, dead code, unbound variable theo chuẩn PEP 8.
   - Sử dụng **Bandit** với mức kiểm soát High/Medium để phát hiện các lỗ hổng SQLi, Hardcoded secrets, Insecure binding.
   - Sử dụng **pip-audit** để đối soát các CVE bảo mật trong thư viện dependencies.

---

## 4. MÔI TRƯỜNG & CÔNG CỤ (TEST TOOLS & ENVIRONMENT)

| Thành phần | Chi tiết cấu hình |
|---|---|
| **Hệ điều hành kiểm thử** | Windows 11 Pro 64-bit / Windows Server 2022 (GitHub Actions Runner) |
| **Python Runtime** | Python 3.13.5 (64-bit) |
| **Test Framework** | `pytest 9.1.1` |
| **Coverage Tool** | `pytest-cov 7.1.0` |
| **Linter / Formatter** | `ruff 0.9.x` |
| **Security Scanner** | `bandit 1.8.x`, `pip-audit 2.8.x` |
| **Môi trường tự động hóa** | GitHub Actions Workflow (`.github/workflows/ci.yml`) |

---

## 5. MA TRẬN KỊCH BẢN KIỂM THỬ (TEST MATRIX)

| Mã Module | Tên File Test | Số lượng Test | Mô tả mục tiêu |
|---|---|---|---|
| **CALL-01..06**| `tests/test_calling_feature.py`| 6 | Vòng đời cuộc gọi thoại/video, chuông reo, từ chối, chặn cuộc gọi, cuộc gọi nhỡ, relay audio/video |
| **DB-01..07** | `tests/test_database.py` | 7 | Xác thực độ phức tạp mật khẩu, băm PBKDF2 |
| **DB-08..12** | `tests/test_database.py` | 5 | Đăng ký tài khoản, đăng nhập đúng/sai, tìm kiếm |
| **DB-13..14** | `tests/test_database.py` | 2 | Vòng đời lời mời kết bạn, cơ chế chặn 2 chiều |
| **DB-15..20** | `tests/test_database.py` | 6 | Hội thoại 1-1, reactions, thu hồi tin, ghim tin, cloud, cascade deletion |
| **NET-01..05**| `tests/test_network_server.py`| 5 | Kết nối socket, flow login socket, nhắn tin P2P 2 client, typing indicator, rate limit |
| **DSK-01..05**| `tests/test_desktop_features.py`| 5 | Window manager restore, multi-monitor bounds, emoji check, file size format, time format |
| **UI-01..03** | `tests/test_ui_smoke.py` | 3 | Dark/Light mode theme values, Search filter regex, Message length validator |
| **TỔNG CỘNG** | **5 File Test** | **39 Test Cases** | **Đảm bảo 100% Passed** |

---

## 6. TIÊU CHÍ ĐÁNH GIÁ (PASS / FAIL CRITERIA)
- **Tiêu chí Đạt (Pass)**:
  - 100% test cases (39/39) vượt qua thành công, 0 lỗi, 0 warning nghiêm trọng.
  - Thời gian thực thi toàn bộ test suite dưới 5 giây.
  - Công cụ Ruff báo cáo `All checks passed!` không có lỗi cú pháp hay biến chưa khai báo.
  - Công cụ Bandit báo cáo `No issues identified` (0 Medium, 0 High).
  - Không sinh ra các file rác hoặc file tạm thời sau khi kết thúc quá trình chạy test.
