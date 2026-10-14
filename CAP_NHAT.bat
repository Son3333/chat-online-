@echo off
title CAP NHAT UNG DUNG - NHOM 05
color 0A
cd /d "%~dp0"

echo ===================================================================
echo      KIEM TRA VA CAP NHAT BAN MOI NHAT TU GITHUB (NHOM 05)
echo ===================================================================
echo.

:: 1. Neu may tinh da clone bang Git
if exist ".git" (
    echo [*] Phat hien kho ma nguon Git. Dang dong bo ban moi nhat...
    git pull origin main
    if %errorlevel% equ 0 (
        echo.
        echo [OK] Da cap nhat ung dung len phien ban moi nhat thanh cong!
    ) else (
        echo.
        echo [!] Khong the dong bo qua Git (co the do mat ket noi mang).
    )
    echo.
    pause
    exit /b
)

:: 2. Neu may nguoi dung chi tai file ZIP ve (chua cai Git)
echo [*] Dang ket noi toi GitHub (https://github.com/Son3333/chat-online-)...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/Son3333/chat-online-/archive/refs/heads/main.zip' -OutFile 'update_temp.zip'; Expand-Archive -Path 'update_temp.zip' -DestinationPath 'temp_update' -Force; Copy-Item -Path 'temp_update\chat-online--main\*' -Destination '.' -Recurse -Force; Remove-Item 'update_temp.zip' -Force; Remove-Item 'temp_update' -Recurse -Force; Write-Host '[OK] Da tai va de ma nguon phien ban moi nhat thanh cong!' -ForegroundColor Green}"

echo.
echo ===================================================================
echo   CAP NHAT HOAN TAT! Ban co the mo lai CHAY_UNG_DUNG.bat de su dung.
echo ===================================================================
echo.
pause

