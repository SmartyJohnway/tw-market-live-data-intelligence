@echo off
setlocal
set "PYTHONPATH="
set "PYTHONHOME="
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONUTF8=1"
powershell.exe -NoLogo -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0launcher\tw-market-launcher.ps1" %*
exit /b %errorlevel%
