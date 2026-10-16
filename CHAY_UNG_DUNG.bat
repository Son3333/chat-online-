@echo off
chcp 65001 >nul
title UNG DUNG NHAN TIN - NHOM 05
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
:: 1. Kiem tra va khoi dong Server neu chua chay
netstat -ano | findstr :8888 | findstr LISTENING >nul 2>&1
if %errorlevel% equ 0 goto :launch_app

echo [*] Dang khoi dong Chat Server (127.0.0.1:8888)...
start "CHAT SERVER - LOCAL" "%PY_CMD%" "%~dp0run_server.py"
ping 127.0.0.1 -n 3 >nul

:launch_app
:: 2. Khoi chay ung dung Desktop duy nhat
echo [*] Dang khoi chay Ung Dung Messenger Desktop...

if exist "%~dp0frontend\node_modules\electron\dist\electron.exe" (
    start "" /d "%~dp0frontend" "%~dp0frontend\node_modules\electron\dist\electron.exe" .
    exit /b 0
)

if exist "%~dp0frontend\node_modules\.bin\electron.cmd" (
    start "" /d "%~dp0frontend" .\node_modules\.bin\electron.cmd .
    exit /b 0
)

start "" "%PY_CMD%" "%~dp0launch.pyw"
exit /b 0
