@echo off
echo ================================
echo  RetroFlight - Setup
echo ================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation!
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

:: Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
) else (
    echo Virtual environment already exists.
)

:: Activate and install
echo Installing dependencies...
call .venv\Scripts\activate
pip install -e .

echo.
echo ================================
echo  Setup complete! Run run.bat to start the simulation.
echo ================================
pause
