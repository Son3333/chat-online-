# HƯỚNG DẪN THIẾT LẬP VÀ VẬN HÀNH CI/CD (CI/CD SETUP & OPERATIONS)
## DỰ ÁN ỨNG DỤNG NHẮN TIN TELEGRAM-STYLE DESKTOP

- **Nền tảng**: GitHub Actions
- **Tập tin cấu hình**:
  - `ci/ci.yml`: Pipeline tự động kiểm thử toàn diện (Backend Pytest + Frontend Vitest + Linting)
  - `ci/build-windows.yml`: Pipeline tự động build và đóng gói file thực thi Windows `.exe`

---

## 1. CÁC BƯỚC THIẾT LẬP TRÊN GITHUB ACTIONS

Để kích hoạt workflow tự động trên GitHub:

1. **Ủy quyền Workflow Scope cho GitHub Token** (nếu dùng Personal Access Token):
   - Truy cập: GitHub Settings -> Developer Settings -> Personal Access Tokens (Tokens classic).
   - Chọn token đang dùng và tích chọn quyền `workflow` (Update GitHub Action workflows).
   - Lưu token và copy tập tin từ `ci/ci.yml` và `ci/build-windows.yml` vào `.github/workflows/`.

2. **Cấu trúc Pipeline CI (`ci/ci.yml`)**:
   - `Checkout`: Kéo mã nguồn mới nhất từ nhánh `main`.
   - `Setup Python 3.13` & `Setup Node.js 20`.
   - `Install Dependencies`: Cài đặt `requirements.txt` và `npm ci`.
   - `Linting & Type Check`: `ruff check src tests` và `npm run build` (kiểm tra TypeScript strict mode).
   - `Run Tests`: Chạy `python -m pytest` (39 tests) và `npm test` (12 tests).
   - `Build Artifacts`: Biên dịch React và đóng gói Electron.

3. **Cấu trúc Pipeline Windows Build (`ci/build-windows.yml`)**:
   - Runner: `windows-latest`.
   - Thực thi `npx electron-builder --win portable`.
   - Xuất bản Artifact: Tải lên file thực thi `Telegram Style Messenger 1.0.0.exe` để tải về trực tiếp từ tab Actions trên GitHub.

---

## 2. CHẠY KIỂM THỬ VÀ BUILD TẠI MÁY CỤC BỘ (LOCAL RUNNER)

Bất kỳ lập trình viên nào tải repository về đều có thể chạy quy trình kiểm thử và đóng gói cục bộ mà không cần phụ thuộc vào GitHub Actions:

```powershell
# 1. Kiểm tra linter backend Python
python -m ruff check src tests

# 2. Chạy 39 bài test backend
python -m pytest

# 3. Chạy 12 bài test frontend
cd frontend
npm test

# 4. Build giao diện React và đóng gói Windows Executable (.exe)
npm run build
npm run build:electron
npx electron-builder --win portable
```
Kết quả file `.exe` sẽ được tạo tại thư mục `frontend/dist-package/`.
