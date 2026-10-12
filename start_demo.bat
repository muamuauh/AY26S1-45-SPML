@echo off
rem TelecomSafe Baseline Demo v1 - double-click to start.
rem Optional: start_demo.bat path\to\weights.pt   (default: the E2 baseline)
rem Keep this file ASCII-only: cmd.exe misparses lines with multi-byte UTF-8 text
rem (part of a line gets run as a command), with or without chcp 65001.
setlocal
cd /d "%~dp0"

rem Locate the telecomsafe conda environment: default location first, then ask conda.
set "PY=%USERPROFILE%\.conda\envs\telecomsafe\python.exe"
if not exist "%PY%" (
    for /f "delims=" %%i in ('conda run -n telecomsafe python -c "import sys; print(sys.executable)" 2^>nul') do set "PY=%%i"
)
if not exist "%PY%" (
    echo [Error] conda environment "telecomsafe" not found.
    echo         Create it from the repository root: conda env create -f environment.yml
    pause
    exit /b 1
)

set "WEIGHTS=runs\phase1\e2\weights\best.pt"
if not "%~1"=="" set "WEIGHTS=%~1"
if not exist "%WEIGHTS%" if "%~1"=="" (
    echo E2 weights not found locally; downloading them from the GitHub Release...
    "%PY%" -m telecomsafe.weights e2
)
if not exist "%WEIGHTS%" (
    echo [Error] weights not found: %WEIGHTS%
    echo         Download them: python -m telecomsafe.weights e2
    echo         or retrain:    python -m telecomsafe.train --exp e2
    pause
    exit /b 1
)

set PYTHONIOENCODING=utf-8
echo TelecomSafe Demo starting (weights: %WEIGHTS%)...
echo The browser opens automatically when it is ready: http://127.0.0.1:7860
echo Close this window or press Ctrl+C to stop the server.
echo.
"%PY%" -m telecomsafe.demo.app --weights "%WEIGHTS%" --open
if errorlevel 1 (
    echo.
    echo [Error] The demo exited with an error. If it says port 7860 is in use,
    echo         close the demo window that is already running first.
)
pause
