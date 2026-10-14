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
set "PY_CMD="

:: 1. Kiem tra python tren PATH
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :python_found
)

:: 2. Kiem tra py launcher (thuong co san tren moi may Windows cai Python)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :python_found
)

:: 3. Kiem tra thu muc cai dat mac dinh cua Windows
for %%D in (
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python310\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Program Files\Python313\python.exe"
    "C:\Program Files\Python312\python.exe"
    "C:\Program Files\Python311\python.exe"
) do (
    if exist %%D (
        set "PY_CMD=%%~D"
        goto :python_found
    )
)

:python_not_found
echo.
echo ===================================================================
echo [THONG BAO QUAN TRONG] May tinh ban chua cai dat Python!
echo.
echo De chay duoc app, ban chi can tai va cai dat Python (mat 1 phut):
echo  1. Mo trinh duyet va tai tai: https://www.python.org/downloads/
echo  2. Khi cai dat, LUU Y: TICH VAO O "Add python.exe to PATH" o duoi cung!
echo  3. Sau do mo lai file CHAY_UNG_DUNG.bat nay la xong!
echo ===================================================================
echo.
pause
exit /b

:python_found
echo   [+] Da tim thay Python: %PY_CMD%

echo [3/4] Kiem tra thu vien giao dien...
%PY_CMD% -c "import customtkinter, PIL" >nul 2>&1
if %errorlevel% neq 0 (
    echo   [+] Dang tu dong cai dat thu vien giao dien (Chi chay 1 lan dau tien, vui long cho giay lat)...
    %PY_CMD% -m pip install -r requirements.txt --quiet --disable-pip-version-check --no-warn-script-location
) else (
    echo   [+] Thu vien da san sang!
)

echo [4/4] Dang khoi chay ung dung va tu dong ket noi Server Online...
:: Chay launcher bang Python da tim thay
%PY_CMD% "%~dp0launch.pyw"
exit
