@echo off
title DUNG TOAN BO MAY CHU CHAT - VIBE NGUOI TOT
color 0C
cd /d "%~dp0"

echo ===================================================================
echo     VIBE NGUOI TOT - DUNG MAY CHU CHAT VA DUONG HAM WAN (BORE)
echo ===================================================================
echo.

echo [*] Dang tim kiem tien trinh may chu tren cong 8888...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8888 ^| findstr LISTENING') do (
    echo [*] Dang tat Server PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo [*] Dang tat duong ham bore.exe...
taskkill /F /IM bore.exe >nul 2>&1

echo.
echo ===================================================================
echo [OK] DA DUNG TOAN BO MAY CHU THANH CONG!
echo ===================================================================
echo.
ping 127.0.0.1 -n 3 >nul

