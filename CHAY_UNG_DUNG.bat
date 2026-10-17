@echo off
chcp 65001 >nul
title VIBE NGUOI TOT - UNG DUNG NHAN TIN VA TRUYEN THONG TIN
color 0B
cd /d "%~dp0"

:: Xoa bien moi truong tranh xung dot Electron
set "ELECTRON_RUN_AS_NODE="
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

echo =================================================================
echo        VIBE NGUOI TOT - KHOI DONG HE THONG THONG MINH
echo =================================================================
echo.

:: Tu dong tao bieu tuong loi tat (Shortcut) ngoai man hinh Desktop
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\create_desktop_shortcut.ps1" >nul 2>&1

:: -------------------------------------------------------------
:: 1. Tim kiem trinh thuc thi Python
:: -------------------------------------------------------------
set "PY_CMD="
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :check_python_packages
)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :check_python_packages
)
for %%D in (
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%ProgramFiles%\Python314\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python310\python.exe"
    "C:\Python314\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
) do (
    if exist %%D (
        set "PY_CMD=%%~fD"
        goto :check_python_packages
    )
)

echo [!] CHUA TIM THAY PYTHON TREN MAY TINH NAY!
echo [*] Ung dung can Python 3.10+ de chay may chu du lieu Backend.
echo [*] Vui long cai dat Python tu https://www.python.org/downloads/
echo [*] LUU Y: Khi cai dat, nho tich vao o 'Add Python to PATH'!
echo.
pause
exit /b 1

:check_python_packages
:: Kiem tra cac thu vien Python can thiet: bcrypt, requests
"%PY_CMD%" -c "import bcrypt" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Phat hien thieu thu vien bao mat Python: bcrypt...
    echo [*] Dang tu dong cai dat thu vien Python can thiet...
    "%PY_CMD%" -m pip install bcrypt requests >nul 2>&1
)

:: -------------------------------------------------------------
:: 2. Tim kiem moi truong Node.js / npm
:: -------------------------------------------------------------
:: Uu tien thu muc tools portable neu co
if exist "C:\Users\admin\tools\node-v20.18.0-win-x64\node.exe" set "PATH=C:\Users\admin\tools\node-v20.18.0-win-x64;%PATH%"
if exist "%LOCALAPPDATA%\Programs\nodejs\node.exe" set "PATH=%LOCALAPPDATA%\Programs\nodejs;%PATH%"
if exist "%ProgramFiles%\nodejs\node.exe" set "PATH=%ProgramFiles%\nodejs;%PATH%"
if exist "C:\Program Files (x86)\nodejs\node.exe" set "PATH=C:\Program Files (x86)\nodejs;%PATH%"

node -v >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo =================================================================
    echo [!] MAY NAY CHUA CO NODE.JS DE CHAY GIAO DIEN CLIENT ELECTRON!
    echo =================================================================
    echo [*] Do ma nguon du an su dung React, TypeScript va Electron,
    echo     may tinh can co Node.js de khoi chay giao dien.
    echo.
    echo [*] Huong dan cai dat trong 1 phut:
    echo     1. Truy cap https://nodejs.org/ va tai ban LTS khuyen nghi v20 hoac v22.
    echo     2. Chay file cai dat va bam Next den het.
    echo     3. Sau khi cai xong, mo lai file CHAY_UNG_DUNG.bat nay la xong!
    echo =================================================================
    echo.
    pause
    exit /b 1
)

:: -------------------------------------------------------------
:: 3. Kiem tra thu vien Frontend: node_modules
:: -------------------------------------------------------------
if not exist "%~dp0frontend\node_modules\electron" (
    echo.
    echo =================================================================
    echo [*] PHAT HIEN LAN DAU TIEN CHAY UNG DUNG TREN MAY MOI!
    echo [*] Dang tu dong cai dat cac goi thu vien can thiet qua npm install...
    echo [*] Qua trinh nay chi dien ra 1 lan duy nhat, mat khoang 1-2 phut.
    echo =================================================================
    echo.
    cd /d "%~dp0frontend"
    call npm install
    if %errorlevel% neq 0 (
        echo.
        echo [!] Cai dat cac goi npm that bai! Vui long kiem tra lai ket noi mang.
        pause
        exit /b 1
    )
    cd /d "%~dp0"
)

:: -------------------------------------------------------------
:: 4. Kiem tra file build giao dien: dist va dist-electron
:: -------------------------------------------------------------
if not exist "%~dp0frontend\dist\index.html" (
    echo [*] Dang bien dich giao dien React Web: npm run build...
    cd /d "%~dp0frontend"
    call npm run build
    cd /d "%~dp0"
)
if not exist "%~dp0frontend\dist-electron\main.js" (
    echo [*] Dang bien dich trinh dieu khien Electron Desktop: npm run build:electron...
    cd /d "%~dp0frontend"
    call npm run build:electron
    cd /d "%~dp0"
)

:: -------------------------------------------------------------
:: 5. Chay khoi tao he thong All-in-one (Desktop Shortcut + WAN Server)
:: -------------------------------------------------------------
if exist "%~dp0scripts\setup_all_in_one.py" (
    "%PY_CMD%" "%~dp0scripts\setup_all_in_one.py"
)

:: -------------------------------------------------------------
:: 6. Khoi chay ung dung Desktop Vibe Nguoi Tot
:: -------------------------------------------------------------
echo [*] Dang mo Ung Dung Vibe Nguoi Tot...

set "ELECTRON_RUN_AS_NODE="
set "ELECTRON_NO_ATTACH_CONSOLE=1"
cd /d "%~dp0frontend"

if exist "node_modules\electron\dist\electron.exe" (
    start "" "node_modules\electron\dist\electron.exe" .
    exit /b 0
)

if exist "node_modules\.bin\electron.cmd" (
    start "" node_modules\.bin\electron.cmd .
    exit /b 0
)

call npx electron .
exit /b 0
