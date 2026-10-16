# QUY TẮC DỰ ÁN (PROJECT RULES & PREFERENCES)

1. **QUẢN LÝ FILE TEST & DỮ LIỆU TẠM:**
   - Sau khi thực hiện kiểm thử tự động (pytest/unit test), luôn tự động dọn dẹp và xóa sạch toàn bộ các tệp/thư mục kiểm thử sinh ra (`tests/`, `ci/`, `.pytest_cache/`, `.coverage`).
   - Không commit hoặc để lại các file test trong thư mục làm việc của dự án.
   - Giữ `requirements.txt` sạch sẽ, chỉ bao gồm các thư viện runtime phục vụ chạy ứng dụng.

2. **CẬP NHẬT BÁO CÁO TỰ ĐỘNG:**
   - Mỗi khi bổ sung tính năng mới hoặc hoàn tất kiểm thử, tự động cập nhật ngay lập tức các tệp báo cáo đồ án:
     + Các file Word báo cáo: `BAO CAO ĐỒ ÁN CHUYÊN NGÀNH - CHƯƠNG 4 - NHÓM 5.docx` (Database schema, danh sách chức năng) và `BAO CAO ĐỒ ÁN CHUYÊN NGÀNH - CHƯƠNG 5 - KẾT LUẬN - NHÓM 5.docx` (Cấu trúc thư mục, Bảng kết quả kiểm thử Test Cases, Kết luận).
     + Tài liệu `README.md`: Cập nhật danh sách tính năng sản phẩm và cây thư mục dự án tương ứng.

3. **BẢO TOÀN TRẠNG THÁI SERVER & MÃ NGUỒN:**
   - Luôn duy trì server WAN chạy ngầm ổn định.
   - Commit và push sạch sẽ lên GitHub nhánh `main`.

