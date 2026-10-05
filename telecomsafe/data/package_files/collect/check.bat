@echo off
setlocal
cd /d "%~dp0"
title TelecomEval collection - check
call tools\uv.bat
if errorlevel 1 goto end
uv run --no-project --python 3.12 --with pillow python tools\check.py
:end
echo.
pause
