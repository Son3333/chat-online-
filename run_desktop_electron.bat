@echo off
title Telegram Style Desktop Messenger
set PATH=C:\Users\admin\tools\node-v20.18.0-win-x64;%PATH%
cd /d "%~dp0"
if exist "frontend\dist-package\Telegram Style Messenger 1.0.0.exe" (
    echo [INFO] Khoi chay Telegram Desktop Portable...
    start "" "frontend\dist-package\Telegram Style Messenger 1.0.0.exe"
    exit /b 0
)
if exist "frontend\dist-package\win-unpacked\Telegram Style Messenger.exe" (
    echo [INFO] Khoi chay Telegram Desktop Unpacked...
    start "" "frontend\dist-package\win-unpacked\Telegram Style Messenger.exe"
    exit /b 0
)
echo [INFO] Dang khoi chay Electron tu source code...
cd frontend
call npx electron .

