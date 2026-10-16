@echo off
chcp 65001 >nul
title TAO SHORTCUT NGOAI DESKTOP - VIBE NGUOI TOT
color 0A
cd /d "%~dp0"

echo ===================================================================
echo     VIBE NGUOI TOT - UNG DUNG NHAN TIN DESKTOP
echo     TAO BIEU TUONG LOI TAT (SHORTCUT) RA MAN HINH CHINH (DESKTOP)
echo ===================================================================
echo.

python "%~dp0scripts\create_shortcut.py"

echo.
echo [*] Tu nay ban chi can ra ngoai Desktop nhap dup vao bieu tuong la dung duoc luon!
echo     (May chu va Ung dung se tu dong chay ngam, khong can mo VS Code).
echo.
ping 127.0.0.1 -n 3 >nul
