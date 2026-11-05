@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo First-time setup: creating virtual environment...
  py -3.13 -m venv .venv
  if errorlevel 1 (
    echo Failed to create venv. Install Python 3.13+ from python.org and try again.
    pause
    exit /b 1
  )
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
  )
)

REM Use python.exe so crash messages stay visible; switch to pythonw when shipping.
".venv\Scripts\python.exe" "%~dp0main.py"
if errorlevel 1 (
  echo.
  echo Finviz Scanner Desktop exited with an error.
  pause
)
