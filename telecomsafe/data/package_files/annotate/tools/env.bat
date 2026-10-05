@echo off
rem Makes sure uv and the Python environment with Label Studio exist, and sets VENV.
rem The environment lives in a short path outside the package: deep paths break on Windows
rem (260-character limit) and a 1 GB folder should not be synced by OneDrive.
set "VENV=%LOCALAPPDATA%\TelecomEval\venv-ls1.23.1"
where uv >nul 2>nul
if errorlevel 1 set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>nul
if errorlevel 1 (
  echo [setup] Installing uv, a small Python installer ...
  powershell -NoProfile -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
)
where uv >nul 2>nul
if errorlevel 1 (
  echo [setup] uv could not be installed. See README.md, FAQ.
  exit /b 1
)
if exist "%VENV%\Scripts\label-studio.exe" exit /b 0
echo [setup] First run: installing Python 3.12 and Label Studio into %VENV%
echo [setup] This takes 5-10 minutes ...
uv venv "%VENV%" --python 3.12 --allow-existing
if errorlevel 1 exit /b 1
uv pip install --python "%VENV%\Scripts\python.exe" label-studio==1.23.1
if errorlevel 1 exit /b 1
exit /b 0
