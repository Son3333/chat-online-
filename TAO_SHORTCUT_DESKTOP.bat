@echo off
title TAO SHORTCUT NGOAI DESKTOP - NHOM 05
color 0A
cd /d "%~dp0"

echo ===================================================================
echo     DO AN CHUYEN NGANH CONG NGHE PHAN MEM - NHOM 05
echo     TAO BIEU TUONG LOI TAT (SHORTCUT) RA MAN HINH CHINH (DESKTOP)
echo ===================================================================
echo.

powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([System.IO.Path]::Combine([System.Environment]::GetFolderPath('Desktop'),'Chat App - Nhom 05.lnk')); $s.TargetPath='pythonw.exe'; $s.Arguments='\"' + (Get-Item .).FullName + '\launch.pyw\"'; $s.WorkingDirectory=(Get-Item .).FullName; $s.Save()"

echo.
echo [OK] Da tao thanh cong loi tat ngoai Desktop: "Chat App - Nhom 05"
echo [*] Tu nay ban chi can ra ngoai Desktop nhap dup vao bieu tuong la dung duoc luon!
echo     (May chu va Ung dung se tu dong chay ngam, khong can mo VS Code).
echo.
ping 127.0.0.1 -n 4 >nul

