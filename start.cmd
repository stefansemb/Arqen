@echo off
rem Starts Arqen without a console window.
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Arqen is not installed yet. Run install.cmd first.
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" -m arqen.ui
