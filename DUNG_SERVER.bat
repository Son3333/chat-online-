@echo off
chcp 65001 >nul
title DUNG MAY CHU VIBE NGUOI TOT
color 0C
cd /d "%~dp0"

echo =================================================================
echo        VIBE NGUOI TOT - DUNG MAY CHU WAN VA TIEN TRINH NGAM
echo =================================================================
echo.

echo [*] Dang tat duong ham bore.exe...
taskkill /F /IM bore.exe >nul 2>&1

echo [*] Dang tat cac cua so may chu WAN dang chay...
taskkill /F /FI "WINDOWTITLE eq VIBE NGUOI TOT - MAY CHU TRUYEN THONG WAN*" >nul 2>&1

echo [*] Dang giai phong cong mang 8888...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8888 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo =================================================================
echo [OK] DA DUNG TAT CA MAY CHU VA TIEN TRINH THANH CONG!
echo =================================================================
echo.
pause

