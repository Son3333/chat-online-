@echo off
chcp 65001 >nul
title VIBE NGUOI TOT - CAP NHAT PHIEN BAN MOI
color 0A
cd /d "%~dp0"

echo =================================================================
echo       VIBE NGUOI TOT - DONG BO VA CAP NHAT TU DONG
echo =================================================================
echo.
echo [*] Dang kiem tra va tai ban cap nhat moi nhat tu GitHub...
echo.

git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] May tinh nay chua cai dat Git.
    echo [*] Vui long truy cap https://github.com/Son3333/chat-online-
    echo     bam nut Code -^> Download ZIP de tai ban moi nhat ve may.
    echo.
    pause
    exit /b 1
)

git pull origin main
if %errorlevel% neq 0 (
    echo.
    echo [!] Co loi khi dong bo qua git pull.
    echo [*] Dang thu reset va dong bo chinh xac voi GitHub...
    git fetch origin main
    git reset --hard origin/main
)

echo.
echo =================================================================
echo [OK] DA CAP NHAT PHIEN BAN MOI NHAT THANH CONG!
echo =================================================================
echo.
echo [*] Dang khoi dong ung dung ngay bay gio...
timeout /t 2 >nul
start "" "%~dp0CHAY_UNG_DUNG.bat"
exit /b 0
