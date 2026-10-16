@echo off
chcp 65001 >nul
title KHOI DONG UNG DUNG CHAT - NHOM 05
color 0B
cd /d "%~dp0"

:: Xoa bien moi truong tranh xung dot Electron
set "ELECTRON_RUN_AS_NODE="

:: Them duong dan Node.js neu co
if exist "C:\Users\admin\tools\node-v20.18.0-win-x64" (
    set "PATH=C:\Users\admin\tools\node-v20.18.0-win-x64;%PATH%"
)

:: Tim kiem trinh thuc thi Python
set "PY_CMD="
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :check_server
)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :check_server
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
        goto :check_server
    )
)
set "PY_CMD=python"

:check_server
echo ===================================================================
echo     DO AN CHUYEN NGANH CONG NGHE PHAN MEM - KHOA CNTT DCNHA
echo            KHOI DONG UNG DUNG NHAN TIN VA TRUYEN THONG TIN
echo ===================================================================
echo.

:: 1. Kiem tra va khoi dong Server neu chua bat
netstat -ano | findstr :8888 | findstr LISTENING >nul 2>&1
if %errorlevel% equ 0 goto :server_already_up

echo [*] Dang khoi dong Chat Server cong 8888...
start "CHAT SERVER - LOCAL" "%PY_CMD%" "%~dp0run_server.py"
ping 127.0.0.1 -n 3 >nul
goto :select_app

:server_already_up
echo [*] May chu Chat Server da san sang tren cong 8888.

:select_app
echo.
echo   [1] Ung dung moi phong cach Telegram Desktop (Mac dinh sau 3s)
echo   [2] Ung dung giao dien Python goc (CustomTkinter)
echo.
choice /c 12 /t 3 /d 1 /m "Chon giao dien khoi chay [1 hoac 2]: "
if %errorlevel% equ 2 goto :launch_python

:launch_telegram
echo.
echo [*] Dang mo ung dung Telegram Desktop...
if exist "%~dp0frontend\dist-package\win-unpacked\Telegram Style Messenger.exe" (
    start "" /d "%~dp0frontend\dist-package\win-unpacked" "Telegram Style Messenger.exe"
    goto :done
)
if exist "%~dp0frontend\dist-package\Telegram Style Messenger 1.0.0.exe" (
    start "" "%~dp0frontend\dist-package\Telegram Style Messenger 1.0.0.exe"
    goto :done
)
if exist "%~dp0frontend\node_modules\.bin\electron.cmd" (
    start "" /d "%~dp0frontend" .\node_modules\.bin\electron.cmd .
    goto :done
)

:launch_python
echo.
echo [*] Dang mo ung dung Python Client...
start "" "%PY_CMD%" "%~dp0launch.pyw"
goto :done

:done
echo.
echo ===================================================================
echo   [OK] UNG DUNG DA DUOC BAT THANH CONG!
echo ===================================================================
ping 127.0.0.1 -n 3 >nul
exit /b 0
