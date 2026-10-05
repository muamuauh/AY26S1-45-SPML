@echo off
setlocal
cd /d "%~dp0"
title TelecomEval annotation - keep this window open
call tools\env.bat
if errorlevel 1 goto fail
"%VENV%\Scripts\python.exe" tools\ls_tool.py start
if errorlevel 1 goto fail
exit /b 0
:fail
echo.
echo Something went wrong - see README.md, section FAQ.
pause
exit /b 1
