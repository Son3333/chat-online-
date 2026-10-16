# HƯỚNG DẪN CẤU HÌNH VÀ VẬN HÀNH CI/CD (AUTOMATED CI/CD PIPELINE GUIDE)

**Dự án**: Ứng dụng nhắn tin & Truyền thông tin Desktop (Python / CustomTkinter)  
**Nền tảng**: GitHub Actions (`.github/workflows/ci.yml`)  
**Runner OS**: `windows-latest` (Windows Server 2022)  
**Phiên bản Python**: `3.13`  

---

## 1. TỔNG QUAN KIẾN TRÚC PIPELINE CI/CD

Pipeline CI/CD được thiết kế theo mô hình 3 giai đoạn (Stages) độc lập, bảo đảm chất lượng code từ khâu kiểm toán tĩnh, kiểm thử tự động cho đến khâu build gói cài đặt thực thi Windows (`.exe`):

```
       +---------------------------------------------+
       | Stage 1: lint-and-audit                     |
       | - Ruff Code Style & Unbound Variable Check  |
       | - Bandit Security Audit (0 High, 0 Medium)  |
       | - Pip-audit Dependency Vulnerability Scan   |
       +---------------------------------------------+
                              |
                             \|/  (Khi Stage 1 thành công)
       +---------------------------------------------+
       | Stage 2: test-suite                         |
       | - Pytest 33 Unit, Integration & UI Tests    |
       | - Code Coverage Calculation (pytest-cov)    |
       | - Artifact Upload (coverage.xml)            |
       +---------------------------------------------+
                              |
                             \|/  (Khi Stage 2 thành công)
       +---------------------------------------------+
       | Stage 3: package-and-smoke                  |
       | - PyInstaller Windows EXE Packaging         |
       | - Binary Integrity & File Size Smoke Test   |
       | - Artifact Upload (ChatApp_Nhom05.exe)      |
       +---------------------------------------------+
```

---

## 2. CẤU HÌNH WORKFLOW CHI TIẾT (`.github/workflows/ci.yml`)

### 2.1 Điều kiện kích hoạt (Triggers)
Workflow được kích hoạt tự động trong các trường hợp:
1. **Push**: Mỗi khi đẩy mã nguồn mới lên nhánh `main` hoặc `develop`.
2. **Pull Request**: Khi có yêu cầu ghép nhánh (PR) vào nhánh `main`.
3. **Thủ công (Manual)**: Quản trị viên hoặc thành viên nhóm có thể kích hoạt thủ công bất kỳ lúc nào thông qua nút **"Run workflow"** trong tab GitHub Actions (`workflow_dispatch`).

---

### 2.2 Chi tiết các Job trong Workflow

#### Job 1: `lint-and-audit`
- **Mục tiêu**: Ngăn chặn các lỗi cú pháp, biến chưa gán, code rác và lỗ hổng an ninh được đẩy vào repo.
- **Các lệnh thực thi**:
  ```bash
  # 1. Kiểm tra tĩnh phong cách code và lỗi tiềm ẩn
  python -m ruff check src

  # 2. Quét an ninh mã nguồn
  python -m bandit -r src -ll

  # 3. Quét lỗ hổng các thư viện trong requirements.txt
  python -m pip_audit -r requirements.txt
  ```

#### Job 2: `test-suite`
- **Mục tiêu**: Chạy toàn bộ 33 kịch bản kiểm thử tự động, tính toán độ bao phủ mã nguồn.
- **Các lệnh thực thi**:
  ```bash
  # Chạy pytest kèm báo cáo XML và Terminal
  python -m pytest --cov=src --cov-report=xml --cov-report=term-missing tests/
  ```
- **Artifact đầu ra**: Tệp `coverage.xml` được lưu trữ trên GitHub Actions trong 14 ngày để phục vụ phân tích.

#### Job 3: `package-and-smoke`
- **Mục tiêu**: Biên dịch ứng dụng thành tệp thực thi Windows standalone và kiểm tra tính toàn vẹn của tệp binary.
- **Các lệnh thực thi**:
  ```bash
  # Đóng gói với PyInstaller
  pyinstaller --noconsole --onedir --name "ChatApp_Nhom05" run_client.py

  # Kiểm tra sự tồn tại của file thực thi trong thư mục dist/
  Test-Path "dist/ChatApp_Nhom05/ChatApp_Nhom05.exe"
  ```
- **Artifact đầu ra**: Thư mục phân phối `ChatApp_Nhom05-Windows` chứa tệp `.exe` sẵn sàng cho người dùng tải về cài đặt.

---

## 3. HƯỚNG DẪN THEO DÕI VÀ GỠ LỖI (DEBUGGING GUIDE)

### 3.1 Cách xem log trên GitHub Actions
1. Truy cập vào kho mã nguồn trên GitHub: `https://github.com/phatdat08/ChatApp_Nhom5`.
2. Nhấp vào tab **Actions** ở thanh menu trên cùng.
3. Nhấp vào lần chạy (workflow run) mới nhất tương ứng với commit của bạn.
4. Nhấp vào tên từng Job (`lint-and-audit`, `test-suite`, hoặc `package-and-smoke`) để xem chi tiết log của từng bước.

### 3.2 Hướng dẫn xử lý khi Pipeline bị báo đỏ (Fail)

#### Trường hợp 1: `Ruff` báo lỗi Code Formatting hoặc Syntax
- **Nguyên nhân**: Tồn tại biến chưa khai báo, import thừa hoặc dòng code quá dài (> 120 ký tự).
- **Cách sửa cục bộ**:
  ```powershell
  python -m ruff check --fix src
  python -m ruff format src
  git add src/
  git commit -m "fix(lint): auto-fix ruff style issues"
  git push origin main
  ```

#### Trường hợp 2: `Bandit` báo lỗi an ninh (Security Warning)
- **Nguyên nhân**: Sử dụng URL không có https, ghép chuỗi SQL trực tiếp, hoặc bind cổng không an toàn.
- **Cách sửa**: Mở file được Bandit chỉ rõ, chuyển sang parameterized query `?` hoặc thêm `# nosec <MÃ_LUẬT>` kèm chú thích kỹ thuật.

#### Trường hợp 3: `pytest` có bài test bị thất bại
- **Nguyên nhân**: Logic nghiệp vụ bị thay đổi làm sai lệch kết quả mong đợi.
- **Cách sửa cục bộ**:
  ```powershell
  python -m pytest -v -k "tên_test_bị_lỗi"
  ```
  Quan sát traceback cụ thể, sửa code logic trong `src/` hoặc cập nhật assertion tương ứng trong `tests/` rồi push lại.

---

## 4. TỔNG KẾT
Hệ thống CI/CD đã được cấu hình hoàn chỉnh, tự động hóa 100% quy trình kiểm thử và phát hành. Giúp nhóm phát triển tiết kiệm thời gian, phát hiện sớm lỗi phát sinh và bảo đảm tính chuyên nghiệp cao nhất cho đồ án tốt nghiệp.
