@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "ELECTRON_RUN_AS_NODE="
set "ELECTRON_NO_ATTACH_CONSOLE=1"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

if exist "C:\Users\admin\tools\node-v20.18.0-win-x64\node.exe" set "PATH=C:\Users\admin\tools\node-v20.18.0-win-x64;%PATH%"
if exist "%LOCALAPPDATA%\Programs\nodejs\node.exe" set "PATH=%LOCALAPPDATA%\Programs\nodejs;%PATH%"
if exist "%ProgramFiles%\nodejs\node.exe" set "PATH=%ProgramFiles%\nodejs;%PATH%"
if exist "C:\Program Files (x86)\nodejs\node.exe" set "PATH=C:\Program Files (x86)\nodejs;%PATH%"

set "NEED_SETUP=0"
if not exist "%~dp0frontend\node_modules\electron\dist\electron.exe" set "NEED_SETUP=1"
if not exist "%~dp0frontend\dist\index.html" set "NEED_SETUP=1"
if not exist "%~dp0frontend\dist-electron\main.js" set "NEED_SETUP=1"

if "%NEED_SETUP%"=="1" (
    powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0scripts\setup_progress.ps1"
    if %errorlevel% neq 0 exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0scripts\create_desktop_shortcut.ps1" >nul 2>&1

cd /d "%~dp0frontend"
if exist "node_modules\electron\dist\electron.exe" (
    start "" "node_modules\electron\dist\electron.exe" .
    exit /b 0
)

if exist "node_modules\.bin\electron.cmd" (
    start "" node_modules\.bin\electron.cmd .
    exit /b 0
)

exit /b 1
