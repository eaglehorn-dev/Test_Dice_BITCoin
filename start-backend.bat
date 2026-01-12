@echo off
echo ========================================
echo Starting Bitcoin Dice Backend
echo ========================================
echo.

cd /d "%~dp0backend"

REM Check if virtual environment exists
if not exist "venv\" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup-backend.bat first
    pause
    exit /b 1
)

REM Check if .env exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Please copy env.example.txt to .env and configure it
    pause
    exit /b 1
)

REM Activate virtual environment and start backend
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting FastAPI backend on http://localhost:8000
echo Press Ctrl+C to stop
echo.

python -m app.main

pause
