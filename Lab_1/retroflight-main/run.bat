@echo off
echo ================================
echo  RetroFlight - Starting...
echo ================================
echo.

:: Check if setup has been run
if not exist ".venv" (
    echo ERROR: No virtual environment found.
    echo Please run setup.bat first!
    pause
    exit /b 1
)

call .venv\Scripts\activate
set PYTHONPATH=src

python -m retroflight.main
