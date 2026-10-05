@echo off
setlocal
cd /d "%~dp0"
title TelecomEval annotation - export
call tools\env.bat
if errorlevel 1 goto fail
"%VENV%\Scripts\python.exe" tools\ls_tool.py export
if errorlevel 1 goto fail
echo.
pause
exit /b 0
:fail
echo.
echo Something went wrong - see README.md, section FAQ.
pause
exit /b 1
