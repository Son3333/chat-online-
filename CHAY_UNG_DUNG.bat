@echo off
title UNG DUNG NHAN TIN VA TRUYEN TIN - NHOM 05
cd /d "%~dp0"

echo ===================================================================
echo   KHOI DONG UNG DUNG NHAN TIN VA TRUYEN THONG TIN (NHOM 05)
echo ===================================================================
echo.

:: Tu dong keo ban moi nhat neu may clone bang Git
if exist ".git" (
    echo [1/4] Tu dong kiem tra va dong bo ban moi nhat tu GitHub...
    git pull origin main --quiet >nul 2>&1
)

echo [2/4] Kiem tra moi truong Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [LOI] May tinh cua ban chua cai dat Python hoac chua them vao PATH!
    echo Vui long cai dat Python tai https://www.python.org/ (Nho tich chon 'Add Python to PATH')
    echo.
    pause
    exit /b
)

echo [3/4] Tu dong kiem tra va cai dat thu vien ngam (customtkinter, pillow, pyngrok)...
python -m pip install -r requirements.txt --quiet --disable-pip-version-check

echo [4/4] Dang khoi chay ung dung va tu dong ket noi Server Online...
start "" pythonw "%~dp0launch.pyw"
exit
