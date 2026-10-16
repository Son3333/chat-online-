@echo off
chcp 65001 >nul
title CHAT SERVER MANG WAN (INTERNET) - VIBE NGUOI TOT
color 0B
cd /d "%~dp0"

echo ===================================================================
echo     VIBE NGUOI TOT - CHAT SERVER MANG DIEN RONG (WAN / INTERNET)
echo ===================================================================
echo.

python "%~dp0run_server_wan.py"
pause

