---
name: project-core-principles
description: Bộ nguyên tắc cốt lõi bắt buộc phải đọc và tuân thủ nghiêm ngặt trước khi thực hiện bất kỳ hành động nào trong dự án Vibe Messenger.
---

# BỘ NGUYÊN TẮC CỐT LÕI CỦA DỰ ÁN (BẮT BUỘC TUÂN THỦ 100%)

> [!IMPORTANT]
> TRƯỚC KHI BẮT TAY LÀM BẤT KỲ YÊU CẦU NÀO HOẶC CHỈNH SỬA BẤT KỲ DÒNG CODE NÀO, BẮT BUỘC PHẢI ĐỌC LẠI BỘ QUY TẮC NÀY!

---

### NGUYÊN TẮC 1: BÁO CÁO KẾ HOẠCH & TƯ DUY LOGIC TRƯỚC KHI LÀM
- **Không được làm như một cái máy**: Không được người dùng nói gì thì hấp tấp nhào vào code ngay mà không suy nghĩ thấu đáo bài toán, logic nghiệp vụ và góc độ an toàn bảo mật.
- **Trước khi chỉnh sửa bất kỳ file nào**: Phải trình bày mạch lạc cho người dùng nghe:
  1. Bản chất vấn đề và logic bài toán thực tế là gì?
  2. Kế hoạch chi tiết xử lý như thế nào? (Sửa file nào, sửa hàm nào, cơ chế luồng dữ liệu ra sao?)
  3. Để người dùng nắm được toàn bộ quy trình trước khi bắt đầu thực hiện.

---

### NGUYÊN TẮC 2: PHÁT TRIỂN TRÊN MÔI TRƯỜNG TEST / STAGING
- **Tuyệt đối không can thiệp trực tiếp vào bản chính thức (`main`)**:
  - Mọi thay đổi code, cài đặt tính năng mới phải được thực hiện trên nhánh test: `staging-feature-upgrade`.
  - Mọi hoạt động kiểm thử độc lập phải diễn ra trên môi trường này trước khi được xem xét đưa vào bản chính thức.

---

### NGUYÊN TẮC 3: BẮT BUỘC SCREEN (CHỤP ẢNH MÀN HÌNH) TRỰC QUAN ĐỂ ĐỐI CHIẾU
- **Sau khi cập nhật giao diện hoặc tính năng**: BẮT BUỘC phải chụp ảnh màn hình (screenshot) thực tế các giao diện liên quan.
- Đối chiếu trực quan xem:
  - Giao diện có thay đổi đúng mong đợi không?
  - Có bị vỡ khung, đè nút, lệch bố cục hay không?
  - Có bị lỗi hiển thị hay mất tính năng cũ nào không?
- Phải có file ảnh chụp màn hình thực tế lưu tại thư mục `screenshots/` để người dùng kiểm chứng bằng mắt.

---

### NGUYÊN TẮC 4: TỰ ĐỘNG PHÁT HIỆN & FIX SẠCH TOÀN BỘ BUG TIỀM ẨN
- Trong quá trình phát triển và kiểm thử ở môi trường test, nếu phát hiện bất kỳ lỗi tiềm ẩn nào (logic luồng dữ liệu lỏng lẻo, lỗ hổng bảo mật, bắt ngoại lệ chưa kín, logic bị chồng chéo):
  - Phải **tự động xử lý và fix sạch sẽ ngay lập tức**.
  - Tuyệt đối không để bất kỳ lỗi nào còn tồn tại trước khi cập nhật vào bản chính thức.

---

### NGUYÊN TẮC 5: NGÔN NGỮ GIAO DIỆN CHUẨN END-USER (CẤM BIỆT NGỮ KỸ THUẬT)
- **Tuyệt đối nghiêm cấm**: Sử dụng bất kỳ thuật ngữ nội bộ của nhà phát triển hay code lên giao diện người dùng (ví dụ: *từ máy chủ*, *CSDL*, *Toast*, *Socket*, *phát qua Windows Notification*, v.v.).
- Tất cả nhãn, thông báo, modal, cảnh báo phải viết bằng ngôn ngữ tự nhiên, chuyên nghiệp và chuẩn mực trải nghiệm người dùng cuối (End-User UX).

---

### NGUYÊN TẮC 6: KIỂM THỬ XONG MỚI MERGE MAIN VÀ ĐẨY GITHUB
- Chỉ khi nào:
  1. Tính năng mới hoạt động chuẩn 100%.
  2. Các tính năng cũ không bị ảnh hưởng.
  3. Đã có ảnh chụp màn hình chứng minh trực quan.
  4. Fix sạch mọi bug tiềm ẩn.
- Lúc đó mới được phép:
  - Merge từ `staging-feature-upgrade` vào bản chính thức `main`.
  - Push lên kho chứa GitHub.

---

### NGUYÊN TẮC 7: TUYỆT ĐỐI KHÔNG ĐƯỢC ĐÁNH NOTE / GHI CHÚ TRONG CODE
- **Tuyệt đối nghiêm cấm**: Việc viết các ghi chú, comment (`//`, `#`, `/* */`, docstring ví dụ) trong mã nguồn làm để lộ bất kỳ thông tin nhạy cảm nào (số điện thoại, email, tài khoản, mật khẩu, token bảo mật, đường dẫn nội bộ hoặc logic nghiệp vụ quan trọng).
- **Mã nguồn tự tường minh**: Viết code sạch (clean code), đặt tên biến và hàm rõ ràng. Tuyệt đối không để lại các note nháp, note ví dụ chứa dữ liệu thật hay các comment rác trong toàn bộ codebase dự án.

