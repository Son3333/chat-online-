@echo off
chcp 65001 >nul
title TRUNG TAM KHOI DONG - HE THONG CHAT
color 0B
cd /d "%~dp0"

:: Them duong dan Node.js neu co
if exist "C:\Users\admin\tools\node-v20.18.0-win-x64" (
    set "PATH=C:\Users\admin\tools\node-v20.18.0-win-x64;%PATH%"
)

:: Tim kiem trinh thuc thi Python
set "PY_CMD="
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :menu
)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :menu
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
        goto :menu
    )
)
set "PY_CMD=python"

:menu
cls
echo ===================================================================
echo     DO AN CHUYEN NGANH CONG NGHE PHAN MEM - KHOA CNTT DCNHA
echo            TRUNG TAM DIEU KHIEN UNG DUNG NHAN TIN
echo ===================================================================
echo.
echo   [1] KHOI DONG APP TELEGRAM DESKTOP (Tu dong bat Server + Mo App)
echo   [2] Khoi dong Server WAN (bore.pub) + Mo Telegram Desktop
echo   [3] Mo ung dung Python cu (CustomTkinter)
echo   [4] Chi khoi dong Server (Local / WAN)
echo   [5] Cap nhat ma nguon moi nhat tu GitHub
echo   [6] Tao loi tat (Shortcut) ra ngoai man hinh Desktop
echo   [7] Dung tat ca Server dang chay ngam tren cong 8888
echo   [0] Thoat
echo.
echo ===================================================================
set /p "CHOICE=Nhap lua chon cua ban [Mac dinh: 1]: "

if "%CHOICE%"=="" set "CHOICE=1"
if "%CHOICE%"=="1" goto :opt_telegram
if "%CHOICE%"=="2" goto :opt_wan_telegram
if "%CHOICE%"=="3" goto :opt_python_gui
if "%CHOICE%"=="4" goto :opt_server_only
if "%CHOICE%"=="5" goto :opt_update
if "%CHOICE%"=="6" goto :opt_shortcut
if "%CHOICE%"=="7" goto :opt_stop_server
if "%CHOICE%"=="0" exit /b 0

echo [!] Lua chon khong hop le, vui long chon lai!
timeout /t 2 >nul
goto :menu

:: ---------------------------------------------------------------------
:: 1. KHOI DONG TELEGRAM DESKTOP + SERVER LOCAL
:: ---------------------------------------------------------------------
:opt_telegram
cls
echo [*] Dang kiem tra Chat Server...
netstat -ano | findstr :8888 | findstr LISTENING >nul 2>&1
if %errorlevel% equ 0 (
    echo [+] Server da dang chay tren cong 8888.
) else (
    echo [*] Dang khoi dong Chat Server (127.0.0.1:8888)...
    start "CHAT SERVER - LOCAL" "%PY_CMD%" "%~dp0run_server.py"
    timeout /t 2 /nobreak >nul
)

echo [*] Dang mo ung dung Telegram Desktop...
if exist "frontend\dist-package\Telegram Style Messenger 1.0.0.exe" (
    start "" "frontend\dist-package\Telegram Style Messenger 1.0.0.exe"
    exit /b 0
)
if exist "frontend\dist-package\win-unpacked\Telegram Style Messenger.exe" (
    start "" "frontend\dist-package\win-unpacked\Telegram Style Messenger.exe"
    exit /b 0
)
cd /d "%~dp0frontend"
start "" npx electron .
exit /b 0

:: ---------------------------------------------------------------------
:: 2. KHOI DONG TELEGRAM DESKTOP + SERVER WAN (BORE)
:: ---------------------------------------------------------------------
:opt_wan_telegram
cls
echo [*] Dang kiem tra Chat Server WAN...
netstat -ano | findstr :8888 | findstr LISTENING >nul 2>&1
if %errorlevel% equ 0 (
    echo [+] Server da dang chay san sang tren cong 8888.
) else (
    echo [*] Dang khoi dong Chat Server WAN (bore.pub)...
    start "CHAT SERVER WAN - NHOM 05" "%PY_CMD%" "%~dp0run_server_wan.py"
    timeout /t 3 /nobreak >nul
)

echo [*] Dang mo ung dung Telegram Desktop...
if exist "frontend\dist-package\Telegram Style Messenger 1.0.0.exe" (
    start "" "frontend\dist-package\Telegram Style Messenger 1.0.0.exe"
    exit /b 0
)
if exist "frontend\dist-package\win-unpacked\Telegram Style Messenger.exe" (
    start "" "frontend\dist-package\win-unpacked\Telegram Style Messenger.exe"
    exit /b 0
)
cd /d "%~dp0frontend"
start "" npx electron .
exit /b 0

:: ---------------------------------------------------------------------
:: 3. MO UNG DUNG GIAO DIEN PYTHON CU
:: ---------------------------------------------------------------------
:opt_python_gui
cls
echo [*] Dang kiem tra Chat Server...
netstat -ano | findstr :8888 | findstr LISTENING >nul 2>&1
if not %errorlevel% equ 0 (
    echo [*] Dang khoi dong Chat Server...
    start "CHAT SERVER - LOCAL" "%PY_CMD%" "%~dp0run_server.py"
    timeout /t 2 /nobreak >nul
)
echo [*] Dang khoi chay Python CustomTkinter Client...
start "" "%PY_CMD%" "%~dp0run_client.py"
exit /b 0

:: ---------------------------------------------------------------------
:: 4. CHI CHAY SERVER
:: ---------------------------------------------------------------------
:opt_server_only
cls
echo ===================================================================
echo   CHON CHE DO MAY CHU:
echo   [1] Local Server (127.0.0.1:8888)
echo   [2] WAN Server (bore.pub tunnel de chat qua Internet)
echo ===================================================================
set /p "SRV_MODE=Chon [1 hoac 2]: "
if "%SRV_MODE%"=="2" (
    start "CHAT SERVER WAN" "%PY_CMD%" "%~dp0run_server_wan.py"
) else (
    start "CHAT SERVER LOCAL" "%PY_CMD%" "%~dp0run_server.py"
)
goto :menu

:: ---------------------------------------------------------------------
:: 5. CAP NHAT MA NGUON GITHUB
:: ---------------------------------------------------------------------
:opt_update
cls
echo [*] Dang kiem tra va dong bo voi GitHub origin/main...
if exist ".git" (
    git fetch origin main
    git reset --hard origin/main
    echo [+] Da dong bo thanh cong voi GitHub!
) else (
    echo [-] Khong tim thay thu muc .git!
)
pause
goto :menu

:: ---------------------------------------------------------------------
:: 6. TAO SHORTCUT DESKTOP
:: ---------------------------------------------------------------------
:opt_shortcut
cls
echo [*] Dang tao shortcut ngoai Desktop...
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([System.IO.Path]::Combine([System.Environment]::GetFolderPath('Desktop'),'Telegram Style Messenger.lnk')); if (Test-Path 'frontend\dist-package\Telegram Style Messenger 1.0.0.exe') { $s.TargetPath=(Get-Item 'frontend\dist-package\Telegram Style Messenger 1.0.0.exe').FullName } else { $s.TargetPath=(Get-Item 'CHAY_UNG_DUNG.bat').FullName }; $s.WorkingDirectory=(Get-Item .).FullName; $s.Save()"
echo [+] Da tao bieu tuong loi tat thanh cong ngoai Desktop!
pause
goto :menu

:: ---------------------------------------------------------------------
:: 7. DUNG TAT CA SERVER DANG CHAY
:: ---------------------------------------------------------------------
:opt_stop_server
cls
color 0C
echo [*] Dang tim va dong cac tien trinh tren cong 8888...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8888 ^| findstr LISTENING') do (
    echo [*] Dang tat Server PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)
echo [*] Dang tat duong ham bore.exe...
taskkill /F /IM bore.exe >nul 2>&1
echo [+] Da dung toan bo Server thanh cong!
color 0B
pause
goto :menu
