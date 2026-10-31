@echo off
setlocal
set "PYTHONPATH="
set "PYTHONHOME="
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONUTF8=1"
set "TW_MARKET_LAUNCHER=%~dp0launcher\tw-market-launcher.ps1"
if not exist "%TW_MARKET_LAUNCHER%" (
  echo.
  echo [TW-Market] This file is a Native package source template, not a runnable source-tree launcher.
  echo [TW-Market] Use Launch-TW-Market.cmd from the root of a built or extracted TW-Market Native bundle.
  echo [TW-Market] Expected packaged launcher: "%TW_MARKET_LAUNCHER%"
  echo.
  if /I not "%~1"=="--no-pause" pause
  exit /b 2
)
powershell.exe -NoLogo -NoProfile -STA -ExecutionPolicy Bypass -File "%TW_MARKET_LAUNCHER%" %*
exit /b %errorlevel%
