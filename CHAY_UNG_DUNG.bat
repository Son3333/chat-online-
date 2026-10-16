@echo off
chcp 65001 >nul
title VIBE NGUOI TOT - UNG DUNG NHAN TIN
color 0B
cd /d "%~dp0"

:: Xoa bien moi truong tranh xung dot Electron
set "ELECTRON_RUN_AS_NODE="

if exist "C:\Users\admin\tools\node-v20.18.0-win-x64" (
    set "PATH=C:\Users\admin\tools\node-v20.18.0-win-x64;%PATH%"
)

:: Tim kiem trinh thuc thi Python
set "PY_CMD="
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :run_initializer
)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :run_initializer
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
        goto :run_initializer
    )
)
set "PY_CMD=python"

:run_initializer
:: 1. Chay khoi tao he thong All-in-one:
::    - Kiem tra Desktop shortcut (tao neu chua co, co roi thi bo qua)
::    - Dang ky Windows Startup cho Server WAN (may tinh bat la server chay ngam)
::    - Dam bao Server WAN dang hoat dong tren cong 8888
if exist "%~dp0scripts\setup_all_in_one.py" (
    "%PY_CMD%" "%~dp0scripts\setup_all_in_one.py"
)

:launch_app
:: 2. Khoi chay ung dung Desktop Vibe Nguoi Tot
echo [*] Dang mo Ung Dung Vibe Nguoi Tot...

if exist "%~dp0frontend\node_modules\electron\dist\electron.exe" (
    start "" /d "%~dp0frontend" "%~dp0frontend\node_modules\electron\dist\electron.exe" .
    exit /b 0
)

if exist "%~dp0frontend\node_modules\.bin\electron.cmd" (
    start "" /d "%~dp0frontend" .\node_modules\.bin\electron.cmd .
    exit /b 0
)

exit /b 0
