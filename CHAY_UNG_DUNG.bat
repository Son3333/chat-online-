@echo off
chcp 65001 >nul
title Ung Dung Nhan Tin Va Truyen Du Lieu - Nhom 05
cd /d "%~dp0"

echo ===================================================================
echo     DO AN CHUYEN NGANH CONG NGHE PHAN MEM - KHOA CNTT DCNHA
echo             UNG DUNG NHAN TIN VA TRUYEN THONG TIN
echo ===================================================================
echo.
echo [1/4] Dang kiem tra moi truong he thong...

:: Tim kiem trinh thuc thi Python
set "PY_CMD="

:: Kiem tra lenh python trong PATH
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :python_found
)

:: Kiem tra lenh py (Python Launcher co san tren Windows)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :python_found
)

:: Quet tat ca cac thu muc cai dat Python pho bien tren Windows
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
        goto :python_found
    )
)

:python_not_found
echo.
echo ===================================================================
echo [THONG BAO QUAN TRONG] May tinh ban chua cai dat Python!
echo.
echo De chay ung dung, ban chi can tai va cai dat Python theo cac buoc:
echo   1. Mo trinh duyet va tai tai: https://www.python.org/downloads/
echo   2. Khi mo file cai dat len, LUU Y:
echo      Tich vao o "Add python.exe to PATH" o phia duoi cung!
echo   3. Bam "Install Now", cho 1 phut hoan tat.
echo   4. Sau do mo lai file CHAY_UNG_DUNG.bat nay la chay duoc ngay!
echo ===================================================================
echo.
pause
exit /b 1

:python_found
echo   [+] Da tim thay Python: %PY_CMD%

echo [2/4] Kiem tra thanh phan do hoa Tkinter...
"%PY_CMD%" -c "import tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ===================================================================
    echo [CANH BAO] Python cua ban thieu thanh phan do hoa Tkinter!
    echo Nguyen nhan: Khi cai Python da bo tich "tcl/tk and IDLE".
    echo Cach khac phuc: Cai lai Python tu python.org va giu nguyen mac dinh.
    echo ===================================================================
    echo.
    pause
    exit /b 1
)

echo [3/4] Kiem tra cac thu vien can thiet...
"%PY_CMD%" -c "import customtkinter, PIL" >nul 2>&1
if %errorlevel% equ 0 goto :libs_ready

echo   [+] Dang tu dong cai dat thu vien giao dien, vui long cho giay lat...
"%PY_CMD%" -m pip install -r requirements.txt --disable-pip-version-check --no-warn-script-location
if %errorlevel% neq 0 (
    echo.
    echo ===================================================================
    echo [LOI] Khong the tu dong cai dat thu vien qua pip!
    echo Vui long kiem tra lai ket noi mang Internet cua ban.
    echo ===================================================================
    echo.
    pause
    exit /b 1
)
echo   [+] Cai dat thu vien hoan tat thanh cong!

:libs_ready
echo   [+] Cac thu vien da day du va san sang!

:: Tu dong dong bo ban moi nhat tu GitHub neu co Git
if exist "%~dp0.git" (
    echo   [*] Dang tu dong dong bo ban cap nhat moi nhat tu GitHub...
    git pull origin main --quiet >nul 2>&1
)

echo [4/4] Dang khoi chay ung dung chat...
"%PY_CMD%" "%~dp0launch.pyw"

:: Neu Python dung lai hoac xay ra loi, giu man hinh de xem nguyen nhan
if %errorlevel% neq 0 (
    echo.
    echo ===================================================================
    echo [THONG BAO] Ung dung gap su co hoac da dung dot ngot!
    echo Chi tiet loi da duoc luu lai trong file: crash_log.txt
    echo ===================================================================
    echo.
    pause
)
