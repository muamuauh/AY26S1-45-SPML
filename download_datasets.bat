@echo off
rem TelecomSafe - download every training dataset in one go (double-click to run).
rem Roboflow datasets need ROBOFLOW_API_KEY in .env; APD (private) is extracted from
rem APD.v1i.yolov8.zip if you put it in this folder or in your Downloads folder.
rem Datasets already present are skipped, so it is safe to run again.
rem Keep this file ASCII-only: cmd.exe misparses lines with multi-byte UTF-8 text.
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

rem API key: create .env from the template and let the user fill it in.
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo Created .env from .env.example.
)
findstr /R /C:"^ROBOFLOW_API_KEY=..*" ".env" >nul
if errorlevel 1 if "%ROBOFLOW_API_KEY%"=="" (
    echo.
    echo ROBOFLOW_API_KEY is empty. Get it at app.roboflow.com - Settings - API Keys,
    echo paste it after ROBOFLOW_API_KEY= in the Notepad window that opens, save and close it.
    echo Never commit .env.
    start /wait notepad ".env"
)

echo.
echo Downloading datasets into data\raw\ ...
echo.
"%PY%" -m telecomsafe.data.download
set "RESULT=%ERRORLEVEL%"

echo.
echo ---------------------------------------------------------------------------
echo Status (a tick means present):
"%PY%" -m telecomsafe.data.download --list
echo.
echo Phase 1 needs six of these: construction_site_safety, construction_ppe,
echo body_harness, work_at_height, construction_safety_v2 and apd.
echo shel5k, chv and telecom_eval are optional or built separately.
if not "%RESULT%"=="0" (
    echo.
    echo [Error] Some downloads failed - see the messages above. Check ROBOFLOW_API_KEY in .env
    echo         and your network, then run this script again: finished datasets are skipped.
)
pause
