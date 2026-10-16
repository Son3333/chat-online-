@echo off
chcp 65001 >nul
title VIBE NGUOI TOT - MAY CHU TRUYEN THONG WAN (DOC LAP VS CODE)
color 0A
cd /d "%~dp0"

echo =================================================================
echo        VIBE NGUOI TOT - MAY CHU MANG DIEN RONG (WAN SERVER)
echo =================================================================
echo [*] May chu dang chay o che do DOC LAP HOAN TOAN voi VS Code!
echo [*] Ban co the tat VS Code ma may chu van hoat dong xuyen suot 24/7.
echo [*] Giu nguyen cua so nay de duy tri ket noi giua cac may tu xa qua Internet.
echo =================================================================
echo.

:: Tim kiem trinh thuc thi Python
set "PY_CMD="
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :start_server
)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :start_server
)
for %%D in (
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%ProgramFiles%\Python314\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python310\python.exe"
    "C:\Python314\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
) do (
    if exist %%D (
        set "PY_CMD=%%~fD"
        goto :start_server
    )
)

echo [!] KHONG TIM THAY PYTHON TREN MAY!
echo [*] Vui long cai dat Python 3.10+ de chay may chu.
pause
exit /b 1

:start_server
:: Kiem tra neu port 8888 da co may chu khac chay
netstat -ano | findstr :8888 | findstr LISTENING >nul 2>&1
if %errorlevel% equ 0 (
    echo [!] Phat hien cong 8888 dang co mot tien trinh may chu chay.
    echo [*] Dang don dep tien trinh cu de dam bao may chu moi nhat...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8888 ^| findstr LISTENING') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    taskkill /F /IM bore.exe >nul 2>&1
    timeout /t 1 >nul
)

echo [*] Dang khoi dong Chat Server WAN va duong ham bore.pub:38888...
echo.
"%PY_CMD%" -u run_server_wan.py

echo.
echo [-] May chu da dung lai.
pause
