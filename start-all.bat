@echo off
echo ========================================
echo Bitcoin Dice Game - Starting All Services
echo ========================================
echo.

REM Get the directory where this script is located
set "ROOT_DIR=%~dp0"

REM Check if backend is set up
if not exist "%ROOT_DIR%backend\venv\" (
    echo [ERROR] Backend not set up!
    echo Please run setup-backend.bat first
    echo.
    pause
    exit /b 1
)

REM Check if frontend is set up
if not exist "%ROOT_DIR%frontend\node_modules\" (
    echo [ERROR] Frontend not set up!
    echo Please run setup-frontend.bat first
    echo.
    pause
    exit /b 1
)

echo [1/2] Starting Backend in new window...
start "Bitcoin Dice - Backend" cmd /k "%ROOT_DIR%start-backend.bat"

REM Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend in new window...
start "Bitcoin Dice - Frontend" cmd /k "%ROOT_DIR%start-frontend.bat"

echo.
echo ========================================
echo All services started!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Two new windows have been opened:
echo   1. Backend (FastAPI) - Don't close this
echo   2. Frontend (React) - Don't close this
echo.
echo Press any key to exit this launcher...
echo (The services will keep running in their windows)
echo.
pause >nul
