@echo off
setlocal
set "PYTHONPATH="
set "PYTHONHOME="
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONUTF8=1"
if not exist "%~dp0runtime\venv\Scripts\python.exe" (
  echo Runtime unavailable. Run bootstrap\bootstrap.ps1 first. 1>&2
  exit /b 2
)
"%~dp0runtime\venv\Scripts\python.exe" -B "%~dp0bootstrap\launch.py" security-master %*
exit /b %errorlevel%