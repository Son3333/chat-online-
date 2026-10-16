@echo off
chcp 65001 >nul
title VIBE NGUOI TOT - UNG DUNG NHAN TIN
color 0B
cd /d "%~dp0"

:: Xoa bien moi truong tranh xung dot Electron
set "ELECTRON_RUN_AS_NODE="

if exist "C:\Users\admin\tools\node-v20.18.0-win-x64" (
    set "PATH=C:\Users\admin\tools\node-v20.18.0-win-x64;%PATH%"
)

:: Tim kiem trinh thuc thi Python
set "PY_CMD="
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :shortcut_check
)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :shortcut_check
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
        goto :shortcut_check
    )
)
set "PY_CMD=python"

:shortcut_check
:: 1. Tu dong kiem tra va tao loi tat (Shortcut) ngoai Desktop neu chua co
if not exist "%USERPROFILE%\Desktop\Vibe Người Tốt.lnk" (
    if exist "%~dp0scripts\create_shortcut.py" (
        "%PY_CMD%" "%~dp0scripts\create_shortcut.py" >nul 2>&1
    )
)

:check_server
:: 2. Kiem tra va khoi dong Server neu chua chay
netstat -ano | findstr :8888 | findstr LISTENING >nul 2>&1
if %errorlevel% equ 0 goto :launch_app

echo [*] Dang khoi dong Chat Server (WAN + Local)...
if exist "%~dp0run_server_wan.py" (
    start "CHAT SERVER - VIBE NGUOI TOT" "%PY_CMD%" "%~dp0run_server_wan.py"
) else (
    start "CHAT SERVER - VIBE NGUOI TOT" "%PY_CMD%" "%~dp0run_server.py"
)
ping 127.0.0.1 -n 3 >nul

:launch_app
:: 3. Khoi chay ung dung Desktop Vibe Nguoi Tot
echo [*] Dang mo Ung Dung Vibe Nguoi Tot...

if exist "%~dp0frontend\node_modules\electron\dist\electron.exe" (
    start "" /d "%~dp0frontend" "%~dp0frontend\node_modules\electron\dist\electron.exe" .
    exit /b 0
)

if exist "%~dp0frontend\node_modules\.bin\electron.cmd" (
    start "" /d "%~dp0frontend" .\node_modules\.bin\electron.cmd .
    exit /b 0
)

exit /b 0
