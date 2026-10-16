# BÁO CÁO KẾT QUẢ KIỂM THỬ (TEST EXECUTION RESULTS)

**Dự án**: Ứng dụng nhắn tin & Truyền thông tin Desktop  
**Thời gian cập nhật**: 16/10/2026 11:00:00 +07:00  
**Môi trường thực thi**: Windows 11 (win32), Python 3.13.5, pytest 9.1.1, pytest-cov 7.1.0  
**Tỷ lệ thành công**: **100% PASSED (39 / 39 Tests Passed)**  
**Thời gian thực thi**: **3.54 giây**

---

## 1. TỔNG HỢP KẾT QUẢ KIỂM THỬ

```
============================= TEST SUMMARY =============================
TOTAL TESTS RUN       : 39
PASSED                : 39 (100%)
FAILED                : 0 (0%)
SKIPPED               : 0 (0%)
ERRORS                : 0 (0%)
EXECUTION DURATION    : 3.54 seconds
CODE COVERAGE (CORE)  : 51% - 86% (Database: 86%, Window Manager: 69%, Server: 60%, Network: 57%)
========================================================================
```

---

## 2. KẾT QUẢ CHI TIẾT TỪNG MODULE KIỂM THỬ

### 2.1 Module Đàm thoại trực tuyến Voice & Video Call (`tests/test_calling_feature.py`) - 6/6 PASSED
| STT | Tên Test Case | Mô tả kiểm tra | Kết quả | Thời gian |
|---|---|---|---|---|
| 01 | `test_voice_call_full_lifecycle` | Vòng đời cuộc gọi thoại: Mời -> Chuông -> Chấp nhận -> Relay Audio -> Kết thúc -> Lưu lịch sử | **PASSED** | 1.15s |
| 02 | `test_video_call_reject_lifecycle` | Vòng đời từ chối cuộc gọi video: Người nhận bấm Từ chối, người gọi nhận thông báo tức thời | **PASSED** | 0.22s |
| 03 | `test_call_blocked_user_prevented` | Kiểm tra chặn an toàn: Người bị chặn không thể thực hiện cuộc gọi tới đối phương | **PASSED** | 0.20s |
| 04 | `test_missed_call_logging` | Ghi nhận cuộc gọi nhỡ khi người gọi hủy máy trước khi đối phương nhấc máy | **PASSED** | 0.35s |
| 05 | `test_media_relay_video_frames` | Chuyển tiếp khung hình JPEG Base64 thời gian thực qua kênh socket media relay | **PASSED** | 0.28s |
| 06 | `test_active_call_receive_media_handler` | Xác thực hàm `receive_media` xử lý packet đa phương tiện an toàn không gây lỗi giao diện | **PASSED** | 0.01s |

---

### 2.2 Module Cơ sở dữ liệu & Xác thực (`tests/test_database.py`) - 20/20 PASSED
| STT | Tên Test Case | Mô tả kiểm tra | Kết quả | Thời gian |
|---|---|---|---|---|
| 07 | `test_valid_password` | Xác thực mật khẩu đạt chuẩn bảo mật | **PASSED** | 0.04s |
| 08 | `test_short_password` | Từ chối mật khẩu có độ dài dưới 8 ký tự | **PASSED** | 0.01s |
| 09 | `test_missing_uppercase` | Từ chối mật khẩu thiếu chữ in hoa | **PASSED** | 0.01s |
| 10 | `test_missing_lowercase` | Từ chối mật khẩu thiếu chữ thường | **PASSED** | 0.01s |
| 11 | `test_missing_number` | Từ chối mật khẩu thiếu chữ số | **PASSED** | 0.01s |
| 12 | `test_missing_special_char` | Từ chối mật khẩu thiếu ký tự đặc biệt | **PASSED** | 0.01s |
| 13 | `test_password_hash_deterministic`| Kiểm tra tính duy nhất của Salt trong băm PBKDF2 | **PASSED** | 0.08s |
| 14 | `test_register_and_authenticate_success` | Đăng ký thành công và đăng nhập đúng thông tin | **PASSED** | 0.03s |
| 15 | `test_register_duplicate_username` | Chặn trùng lặp @username khi đăng ký | **PASSED** | 0.02s |
| 16 | `test_authenticate_wrong_password` | Chặn đăng nhập khi nhập sai mật khẩu | **PASSED** | 0.02s |
| 17 | `test_authenticate_nonexistent_user` | Chặn đăng nhập với tài khoản chưa từng tồn tại | **PASSED** | 0.02s |
| 18 | `test_search_users` | Tìm kiếm người dùng chính xác theo @username | **PASSED** | 0.02s |
| 19 | `test_friend_request_lifecycle` | Vòng đời gửi, chấp nhận, từ chối lời mời kết bạn | **PASSED** | 0.04s |
| 20 | `test_block_and_unblock` | Cơ chế chặn 2 chiều và bỏ chặn tài khoản | **PASSED** | 0.03s |
| 21 | `test_direct_conversation_and_messages` | Tạo hội thoại 1-1, gửi tin nhắn, trích dẫn reply | **PASSED** | 0.04s |
| 22 | `test_message_reactions` | Thả biểu cảm emoji vào tin nhắn và cập nhật tức thì | **PASSED** | 0.03s |
| 23 | `test_recall_message_permissions` | Thu hồi tin nhắn trong thời hạn cho phép | **PASSED** | 0.03s |
| 24 | `test_pinned_message` | Ghim và gỡ ghim thông điệp quan trọng trong cuộc trò chuyện | **PASSED** | 0.03s |
| 25 | `test_saved_messages_cloud` | Chức năng lưu trữ đám mây cá nhân ("Truyền File") | **PASSED** | 0.03s |
| 26 | `test_delete_conversation_cascading` | Xóa hội thoại kèm dọn dẹp sạch sẽ reaction mồ côi | **PASSED** | 0.04s |

---

### 2.3 Module Desktop & Formatter (`tests/test_desktop_features.py`) - 5/5 PASSED
| STT | Tên Test Case | Mô tả kiểm tra | Kết quả | Thời gian |
|---|---|---|---|---|
| 27 | `test_save_and_restore_window_state` | Lưu và khôi phục tọa độ (X, Y, W, H) cửa sổ | **PASSED** | 0.02s |
| 28 | `test_multi_monitor_offscreen_recovery` | Tự động kéo cửa sổ về màn hình chính khi mất màn hình phụ | **PASSED** | 0.01s |
| 29 | `test_is_pure_emoji` | Nhận diện chuỗi thuần biểu tượng emoji để phóng to giao diện | **PASSED** | 0.01s |
| 30 | `test_format_file_size` | Định dạng dung lượng byte thành KB, MB, GB trực quan | **PASSED** | 0.01s |
| 31 | `test_format_time` | Định dạng tem thời gian Hôm nay, Hôm qua và Ngày tháng | **PASSED** | 0.01s |

---

### 2.4 Module Tích hợp Mạng Socket Server (`tests/test_network_server.py`) - 5/5 PASSED
| STT | Tên Test Case | Mô tả kiểm tra | Kết quả | Thời gian |
|---|---|---|---|---|
| 32 | `test_client_connect_and_disconnect` | Kết nối socket và ngắt kết nối an toàn với máy chủ | **PASSED** | 0.15s |
| 33 | `test_client_register_and_login_flow` | Luồng đăng ký & đăng nhập qua giao thức TCP thời gian thực | **PASSED** | 0.21s |
| 34 | `test_messaging_between_two_clients` | Giao nhận tin nhắn tức thì giữa 2 máy trạm cùng online | **PASSED** | 0.28s |
| 35 | `test_typing_indicator_broadcast` | Phát sóng trạng thái "đang soạn tin..." qua socket | **PASSED** | 0.18s |
| 36 | `test_group_creation_and_rate_limiting` | Tạo nhóm chat thành công và chặn spam tạo nhóm | **PASSED** | 0.20s |

---

### 2.5 Module Kiểm thử Giao diện khói (`tests/test_ui_smoke.py`) - 3/3 PASSED
| STT | Tên Test Case | Mô tả kiểm tra | Kết quả | Thời gian |
|---|---|---|---|---|
| 37 | `test_theme_mode_values` | Kiểm tra tính nhất quán của bộ màu Dark và Light mode | **PASSED** | 0.01s |
| 38 | `test_search_filter_regex` | Chuẩn hóa tiền tố tìm kiếm @username và #ID | **PASSED** | 0.01s |
| 39 | `test_message_entry_validation` | Xác thực độ dài tối đa và chuỗi rỗng của ô nhập tin | **PASSED** | 0.01s |

---

## 3. THỐNG KÊ MỨC ĐỘ BAO PHỦ MÃ NGUỒN (CODE COVERAGE)

| Module / Tập tin | Tổng số lệnh (Stmts) | Bị bỏ sót (Miss) | Độ bao phủ (Cover) |
|---|---|---|---|
| `src\server\database.py` | 452 | 65 | **86%** |
| `src\client\desktop\window_manager.py` | 71 | 22 | **69%** |
| `src\server\server.py` | 546 | 221 | **60%** |
| `src\client\network.py` | 280 | 121 | **57%** |
| `src\client\ui\chat_bubble.py` | 351 | 298 | **15%** |
| `src\client\call\call_window.py` | 303 | 258 | **15%** |
| **TỔNG HỢP TOÀN BỘ HỆ THỐNG** | **2,003** | **985** | **51%** |

---

## 4. QUẢN LÝ DỮ LIỆU TẠM VÀ DỌN DẸP MÔI TRƯỜNG
- Tất cả các bài kiểm thử cuộc gọi và cơ sở dữ liệu đều sử dụng file tạm thời hoặc socket cổng ngẫu nhiên do hệ điều hành cấp phát (`port=0`), tự động thu hồi ngay sau khi kết thúc test (`yield` fixture).
- Không có bất kỳ file rác nào bị sinh ra trong thư mục dự án sau khi hoàn tất kiểm thử.
