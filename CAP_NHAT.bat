@echo off
chcp 65001 >nul
title Cap Nhat Ung Dung - Nhom 05
color 0A
cd /d "%~dp0"

echo ===================================================================
echo      KIEM TRA VA CAP NHAT BAN MOI NHAT TU GITHUB (NHOM 05)
echo ===================================================================
echo.

:: Dong cac tien trinh cu dang chay ngam de giai phong thu muc
echo [*] Dang giai phong tien trinh cu...
taskkill /F /IM python.exe /IM pythonw.exe /IM bore.exe >nul 2>&1

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
echo [*] Dang tai ban cap nhat moi nhat tu GitHub...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $zip = 'update_temp.zip'; $dest = 'temp_update'; if (Test-Path $zip) { Remove-Item $zip -Force }; if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }; Write-Host '  [+] Dang tai goi zip tu GitHub...'; Invoke-WebRequest -Uri 'https://github.com/Son3333/chat-online-/archive/refs/heads/main.zip' -OutFile $zip; Write-Host '  [+] Dang giai nen ban moi...'; Expand-Archive -Path $zip -DestinationPath $dest -Force; Write-Host '  [+] Dang ghi de tap tin...'; Copy-Item -Path \"$dest\chat-online--main\*\" -Destination '.' -Recurse -Force; Remove-Item $zip -Force; Remove-Item $dest -Recurse -Force; Write-Host '  [+] Hoan tat cap nhat thanh cong!' -ForegroundColor Green } catch { Write-Host '  [-] Loi cap nhat: ' $_.Exception.Message -ForegroundColor Red; exit 1 }"

if %errorlevel% neq 0 (
    echo.
    echo ===================================================================
    echo [LOI] Khong the tai ban cap nhat tu dong!
    echo Ban co the tai truc tiep file zip moi nhat tai:
    echo   https://github.com/Son3333/chat-online-/archive/refs/heads/main.zip
    echo ===================================================================
) else (
    echo.
    echo ===================================================================
    echo   CAP NHAT HOAN TAT! Ban co the mo lai CHAY_UNG_DUNG.bat de su dung.
    echo ===================================================================
)
echo.
pause
