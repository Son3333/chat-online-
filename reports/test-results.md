# BÁO CÁO KẾT QUẢ KIỂM THỬ (TEST EXECUTION RESULTS)

**Dự án**: Ứng dụng nhắn tin & Truyền thông tin Desktop  
**Thời gian chạy test**: 16/10/2026 10:17:08 +07:00  
**Môi trường thực thi**: Windows 11 (win32), Python 3.13.5, pytest 9.1.1, pytest-cov 7.1.0  
**Tỷ lệ thành công**: **100% PASSED (33 / 33 Tests Passed)**  
**Thời gian thực thi**: **1.50 giây**

---

## 1. TỔNG HỢP KẾT QUẢ KIỂM THỬ

```
============================= TEST SUMMARY =============================
TOTAL TESTS RUN       : 33
PASSED                : 33 (100%)
FAILED                : 0 (0%)
SKIPPED               : 0 (0%)
ERRORS                : 0 (0%)
EXECUTION DURATION    : 1.50 seconds
CODE COVERAGE (CORE)  : 52% (Database: 86%, Window Manager: 69%)
========================================================================
```

---

## 2. KẾT QUẢ CHI TIẾT TỪNG MODULE KIỂM THỬ

### 2.1 Module Cơ sở dữ liệu & Xác thực (`tests/test_database.py`) - 20/20 PASSED
| STT | Tên Test Case | Mô tả kiểm tra | Kết quả | Thời gian |
|---|---|---|---|---|
| 01 | `test_valid_password` | Xác thực mật khẩu đạt chuẩn bảo mật | **PASSED** | 0.04s |
| 02 | `test_short_password` | Từ chối mật khẩu có độ dài dưới 8 ký tự | **PASSED** | 0.01s |
| 03 | `test_missing_uppercase` | Từ chối mật khẩu thiếu chữ in hoa | **PASSED** | 0.01s |
| 04 | `test_missing_lowercase` | Từ chối mật khẩu thiếu chữ thường | **PASSED** | 0.01s |
| 05 | `test_missing_number` | Từ chối mật khẩu thiếu chữ số | **PASSED** | 0.01s |
| 06 | `test_missing_special_char` | Từ chối mật khẩu thiếu ký tự đặc biệt | **PASSED** | 0.01s |
| 07 | `test_password_hash_deterministic`| Kiểm tra tính duy nhất của Salt trong băm PBKDF2 | **PASSED** | 0.08s |
| 08 | `test_register_and_authenticate_success` | Đăng ký thành công và đăng nhập đúng thông tin | **PASSED** | 0.03s |
| 09 | `test_register_duplicate_username` | Chặn trùng lặp @username khi đăng ký | **PASSED** | 0.02s |
| 10 | `test_authenticate_wrong_password` | Chặn đăng nhập khi nhập sai mật khẩu | **PASSED** | 0.02s |
| 11 | `test_authenticate_nonexistent_user` | Chặn đăng nhập với tài khoản chưa từng tồn tại | **PASSED** | 0.02s |
| 12 | `test_search_users` | Tìm kiếm người dùng chính xác theo @username | **PASSED** | 0.02s |
| 13 | `test_friend_request_lifecycle` | Vòng đời gửi, chấp nhận, từ chối lời mời kết bạn | **PASSED** | 0.04s |
| 14 | `test_block_and_unblock` | Cơ chế chặn 2 chiều và bỏ chặn tài khoản | **PASSED** | 0.03s |
| 15 | `test_direct_conversation_and_messages` | Tạo hội thoại 1-1, gửi tin nhắn, trích dẫn reply | **PASSED** | 0.04s |
| 16 | `test_message_reactions` | Thả biểu cảm emoji vào tin nhắn và cập nhật tức thì | **PASSED** | 0.03s |
| 17 | `test_recall_message_permissions` | Thu hồi tin nhắn trong thời hạn cho phép | **PASSED** | 0.03s |
| 18 | `test_pinned_message` | Ghim và gỡ ghim thông điệp quan trọng trong cuộc trò chuyện | **PASSED** | 0.03s |
| 19 | `test_saved_messages_cloud` | Chức năng lưu trữ đám mây cá nhân ("Truyền File") | **PASSED** | 0.03s |
| 20 | `test_delete_conversation_cascading` | Xóa hội thoại kèm dọn dẹp sạch sẽ reaction mồ côi | **PASSED** | 0.04s |

---

### 2.2 Module Desktop & Formatter (`tests/test_desktop_features.py`) - 5/5 PASSED
| STT | Tên Test Case | Mô tả kiểm tra | Kết quả | Thời gian |
|---|---|---|---|---|
| 21 | `test_save_and_restore_window_state` | Lưu và khôi phục tọa độ (X, Y, W, H) cửa sổ | **PASSED** | 0.02s |
| 22 | `test_multi_monitor_offscreen_recovery` | Tự động kéo cửa sổ về màn hình chính khi mất màn hình phụ | **PASSED** | 0.01s |
| 23 | `test_is_pure_emoji` | Nhận diện chuỗi thuần biểu tượng emoji để phóng to giao diện | **PASSED** | 0.01s |
| 24 | `test_format_file_size` | Định dạng dung lượng byte thành KB, MB, GB trực quan | **PASSED** | 0.01s |
| 25 | `test_format_time` | Định dạng tem thời gian Hôm nay, Hôm qua và Ngày tháng | **PASSED** | 0.01s |

---

### 2.3 Module Tích hợp Mạng Socket Server (`tests/test_network_server.py`) - 5/5 PASSED
| STT | Tên Test Case | Mô tả kiểm tra | Kết quả | Thời gian |
|---|---|---|---|---|
| 26 | `test_client_connect_and_disconnect` | Kết nối socket và ngắt kết nối an toàn với máy chủ | **PASSED** | 0.15s |
| 27 | `test_client_register_and_login_flow` | Luồng đăng ký & đăng nhập qua giao thức TCP thời gian thực | **PASSED** | 0.21s |
| 28 | `test_messaging_between_two_clients` | Giao nhận tin nhắn tức thì giữa 2 máy trạm cùng online | **PASSED** | 0.28s |
| 29 | `test_typing_indicator_broadcast` | Phát sóng trạng thái "đang soạn tin..." qua socket | **PASSED** | 0.18s |
| 30 | `test_group_creation_and_rate_limiting` | Tạo nhóm chat thành công và chặn spam tạo nhóm | **PASSED** | 0.20s |

---

### 2.4 Module Kiểm thử Giao diện khói (`tests/test_ui_smoke.py`) - 3/3 PASSED
| STT | Tên Test Case | Mô tả kiểm tra | Kết quả | Thời gian |
|---|---|---|---|---|
| 31 | `test_theme_mode_values` | Kiểm tra tính nhất quán của bộ màu Dark và Light mode | **PASSED** | 0.01s |
| 32 | `test_search_filter_regex` | Chuẩn hóa tiền tố tìm kiếm @username và #ID | **PASSED** | 0.01s |
| 33 | `test_message_entry_validation` | Xác thực độ dài tối đa và chuỗi rỗng của ô nhập tin | **PASSED** | 0.01s |

---

## 3. THỐNG KÊ MỨC ĐỘ BAO PHỦ MÃ NGUỒN (CODE COVERAGE)

| Module / Tập tin | Tổng số lệnh (Stmts) | Bị bỏ sót (Miss) | Độ bao phủ (Cover) |
|---|---|---|---|
| `src\server\database.py` | 452 | 65 | **86%** |
| `src\client\desktop\window_manager.py` | 71 | 22 | **69%** |
| `src\client\network.py` | 280 | 128 | **54%** |
| `src\server\server.py` | 546 | 303 | **45%** |
| `src\client\ui\chat_bubble.py` | 343 | 290 | **15%** |
| **TỔNG HỢP CÁC MODULE LÕI ĐƯỢC TEST** | **1,692** | **808** | **52%** |

---

## 4. QUẢN LÝ DỮ LIỆU TẠM VÀ DỌN DẸP MÔI TRƯỜNG
- Tất cả các bài kiểm thử cơ sở dữ liệu đều sử dụng SQLite trong bộ nhớ (`:memory:`) hoặc file SQLite tạm thời được tự động thu hồi bằng `pytest fixture` (`yield` và dọn dẹp sau khi chạy).
- Các cổng mạng TCP socket trong bài test đều sử dụng cổng động ngẫu nhiên do hệ điều hành cấp phát (`port=0`), sau khi test kết thúc sẽ lập tức đóng socket client và gọi `server.stop()`, đảm bảo **không để lại tiến trình treo hay chiếm dụng tài nguyên hệ thống**.
- Không có bất kỳ file rác nào bị sinh ra trong thư mục dự án sau khi hoàn tất kiểm thử.
