@echo off
rem TelecomSafe Baseline Demo v1 — double-click to start.
rem Optional: start_demo.bat path\to\weights.pt   (default: the E2 baseline)
chcp 65001 >nul
setlocal
cd /d "%~dp0"

rem Locate the telecomsafe conda environment: default location first, then ask conda.
set "PY=%USERPROFILE%\.conda\envs\telecomsafe\python.exe"
if not exist "%PY%" (
    for /f "delims=" %%i in ('conda run -n telecomsafe python -c "import sys; print(sys.executable)" 2^>nul') do set "PY=%%i"
)
if not exist "%PY%" (
    echo [错误] 找不到 conda 环境 telecomsafe。
    echo        请先在项目目录执行：conda env create -f environment.yml
    pause
    exit /b 1
)

set "WEIGHTS=runs\phase1\e2\weights\best.pt"
if not "%~1"=="" set "WEIGHTS=%~1"
if not exist "%WEIGHTS%" (
    echo [错误] 找不到模型权重：%WEIGHTS%
    echo        请先训练：python -m telecomsafe.train --exp e2
    pause
    exit /b 1
)

set PYTHONIOENCODING=utf-8
echo TelecomSafe Demo 启动中（模型：%WEIGHTS%）……
echo 就绪后会自动打开浏览器：http://127.0.0.1:7860
echo 关闭本窗口或按 Ctrl+C 即可停止服务。
echo.
"%PY%" -m telecomsafe.demo.app --weights "%WEIGHTS%" --open
if errorlevel 1 (
    echo.
    echo [错误] Demo 异常退出。若提示端口 7860 被占用，请先关闭已经在运行的 Demo 窗口。
)
pause
