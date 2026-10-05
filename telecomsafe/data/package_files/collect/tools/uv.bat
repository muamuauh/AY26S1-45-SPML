@echo off
rem Makes sure uv (a small Python installer) is available.
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
exit /b 0
