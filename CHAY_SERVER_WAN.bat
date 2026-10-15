@echo off
chcp 65001 >nul
title CHAT SERVER MANG WAN (INTERNET) - NHOM 05
color 0B
cd /d "%~dp0"

echo ===================================================================
echo     DO AN CHUYEN NGANH CONG NGHE PHAN MEM - KHOA CNTT DCNHA
echo        KHOI DONG CHAT SERVER MANG DIEN RONG (WAN / INTERNET)
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

"%PY_CMD%" "%~dp0run_server_wan.py"
pause
