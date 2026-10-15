@echo off
chcp 65001 >nul
title Cap Nhat Ung Dung - Nhom 05
color 0A
cd /d "%~dp0"

echo ===================================================================
echo      KIEM TRA VA CAP NHAT BAN MOI NHAT TU GITHUB (NHOM 05)
echo ===================================================================
echo.

:: Dong cac tien trinh cu dang chay de giai phong file
echo [*] Dang dong ung dung de giai phong thu muc...
taskkill /F /IM python.exe /IM pythonw.exe >nul 2>&1
timeout /t 1 /nobreak >nul

set "UPDATE_OK=0"

:: 1. Neu may tinh da clone bang Git:
if exist ".git" (
    echo [*] Phat hien kho ma nguon Git. Dang dong bo tuyet doi voi origin/main...
    git fetch origin main
    if %errorlevel% equ 0 (
        git reset --hard origin/main
        if %errorlevel% equ 0 (
            set "UPDATE_OK=1"
        )
    )
)

:: 2. Neu khong co Git hoac Git gap loi -> Tu dong tai ZIP de ghi de:
if "%UPDATE_OK%"=="0" (
    echo [*] Dang tai goi ma nguon ZIP moi nhat tu GitHub...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue'; try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $zip = 'update_temp.zip'; $dest = 'temp_update'; if (Test-Path $zip) { Remove-Item $zip -Force }; if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }; Write-Host '  [+] Dang tai goi zip tu GitHub...' -ForegroundColor Cyan; Invoke-WebRequest -Uri 'https://github.com/Son3333/chat-online-/archive/refs/heads/main.zip' -OutFile $zip; Write-Host '  [+] Dang giai nen ban moi...' -ForegroundColor Cyan; Expand-Archive -Path $zip -DestinationPath $dest -Force; Write-Host '  [+] Dang ghi de tap tin cap nhat...' -ForegroundColor Cyan; Copy-Item -Path \"$dest\chat-online--main\*\" -Destination '.' -Recurse -Force; Remove-Item $zip -Force; Remove-Item $dest -Recurse -Force; exit 0 } catch { Write-Host '  [-] Loi cap nhat zip: ' $_.Exception.Message -ForegroundColor Red; exit 1 }"
    if %errorlevel% equ 0 (
        set "UPDATE_OK=1"
    )
)

echo.
if "%UPDATE_OK%"=="1" (
    echo ===================================================================
    echo   [THANH CONG] DA CAP NHAT LEN PHIEN BAN MOI NHAT CUA NHOM 05!
    echo   Ban co the mo lai CHAY_UNG_DUNG.bat de su dung ngay.
    echo ===================================================================
) else (
    echo ===================================================================
    echo   [THAT BAI] Khong the cap nhat tu dong! Vui long kiem tra ket noi mang.
    echo ===================================================================
)
echo.
pause
