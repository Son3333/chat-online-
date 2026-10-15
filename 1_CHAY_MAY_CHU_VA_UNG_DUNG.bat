@echo off
chcp 65001 >nul
title KHOI DONG HE THONG CHAT (SERVER + CLIENT) - NHOM 05
color 0B
cd /d "%~dp0"

echo ===================================================================
echo     DO AN CHUYEN NGANH CONG NGHE PHAN MEM - KHOA CNTT DCNHA
echo            KHOI DONG TRON GOI MAY CHU WAN VA UNG DUNG CHAT
echo ===================================================================
echo.

:: Tim kiem trinh thuc thi Python
set "PY_CMD="
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :py_ready
)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :py_ready
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
        goto :py_ready
    )
)
:py_ready

:: 1. Kiem tra xem Server 8888 da chay chua
netstat -ano | findstr :8888 | findstr LISTENING >nul 2>&1
if %errorlevel% equ 0 (
    echo [1/2] May chu WAN da dang chay san sang tren cong 8888.
) else (
    echo [1/2] Dang khoi dong Chat Server WAN (bore.pub:38888)...
    start "CHAT SERVER WAN - NHOM 05" "%PY_CMD%" "%~dp0run_server_wan.py"
    timeout /t 3 /nobreak >nul
)

:: 2. Tu dong dong bo ban moi nhat
if exist "%~dp0.git" (
    echo [*] Dang dong bo ma nguon moi nhat tu GitHub...
    git fetch origin main --quiet >nul 2>&1
    git reset --hard origin/main --quiet >nul 2>&1
)

:: 3. Khoi chay giao dien Client
echo [2/2] Dang khoi chay giao dien Desktop Client...
start "" "%PY_CMD%" "%~dp0launch.pyw"

echo.
echo ===================================================================
echo   DA KHOI DONG THANH CONG!
echo   Cua so nay se tu dong dong sau 3 giay.
echo ===================================================================
timeout /t 3 >nul
exit
