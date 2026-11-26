# Vibe Người Tốt — ứng dụng nhắn tin Windows

## Tải và chạy

1. Chọn **Code → Download ZIP** tại kho này và giải nén toàn bộ.
2. Mở `CHAY_UNG_DUNG.bat`.
3. Lần đầu ứng dụng tải bộ chạy Electron; cần kết nối Internet. Không cần Python hoặc tự chạy máy chủ.
4. Đăng ký hoặc đăng nhập để sử dụng.

Bản tải chứa giao diện đã biên dịch. Giữ nguyên thư mục `frontend`, `scripts`, biểu tượng và `client_config.json` khi giải nén.

## Kết nối

Ứng dụng khách kết nối đến máy chủ của chủ dự án qua địa chỉ công khai trong `client_config.json`. Máy chủ phải đang bật và có Internet. Bản tải không chứa mã backend, database, tệp người dùng hoặc thông tin SMTP và không tự tạo máy chủ trên máy người dùng.

Nếu địa chỉ đường hầm thay đổi, cần tải lại cấu hình mới hoặc thay địa chỉ kết nối trong ứng dụng. Dịch vụ đường hầm có thể gián đoạn; không bảo đảm hoạt động khi máy chủ tắt.

## Bản 1.0.3

Sửa nút gửi bị kẹt sau một lần mất kết nối hoặc quá thời gian chờ. Giữ nội dung chưa gửi, mở lại nút gửi và hiển thị lý do khi tin bị từ chối. Nếu chưa xác nhận tin đã gửi, kiểm tra lịch sử trước khi gửi lại để tránh trùng tin.

### Các bản sửa từ 1.0.2

Khắc phục kết nối Internet bị gián đoạn ở cổng cũ. Địa chỉ hiện tại: `bore.pub:48888`. Bổ sung phát hiện kết nối treo, kết nối lại, tránh ghi đè yêu cầu đồng thời và thông báo rõ khi chưa tải được danh sách trò chuyện. Điều chỉnh thời gian chờ gửi OTP và thông báo lỗi dễ hiểu.

Nếu đang dùng bản cũ, đổi cổng sang `48888` trong màn hình đăng nhập rồi đăng nhập lại, hoặc tải bản mới. Máy chủ vẫn phải đang chạy trên máy chủ dự án.

### Các bản sửa từ 1.0.1

Sửa hiển thị trích dẫn, ghim tin, trạng thái đăng xuất, đồng bộ nhóm và khoá PIN. Máy chủ riêng đã được cập nhật quyền đọc lịch sử/tệp sau rời nhóm hoặc bị kick và xử lý xác minh email.

Kiểm thử đã xác nhận các luồng chính trên môi trường riêng. Cuộc gọi video chưa xác nhận được hình hai chiều với hai thiết bị độc lập; bản này phát hành với giới hạn đó.

## Cập nhật

Người dùng tải ZIP mới và giải nén vào thư mục mới. Với bản Git clone, dùng `CAP_NHAT.bat` hoặc chức năng cập nhật trong ứng dụng.

## Phát triển giao diện

Trong `frontend`: chạy `npm ci`, `npm run build`, `npm run build:electron`. Mã máy chủ và cấu hình riêng được quản lý ở máy chủ, không phân phối cùng ứng dụng khách.
