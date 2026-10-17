@echo off
chcp 65001 >nul
title TAO LOI TAT NGOAI DESKTOP - VIBE NGUOI TOT
color 0A
cd /d "%~dp0"

echo =================================================================
echo   DANG TAO BIEU TUONG VIBE NGUOI TOT NGOAI MAN HINH CHINH (DESKTOP)
echo =================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\create_desktop_shortcut.ps1"

echo.
echo =================================================================
echo  [THANH CONG] Da tao xong bieu tuong Vibe Nguoi Tot ngoai Desktop!
echo  Tu nay ban co the mo ung dung truc tiep tu man hinh chinh.
echo =================================================================
echo.
timeout /t 3 >nul
exit /b 0
