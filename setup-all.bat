@echo off
echo ========================================
echo Bitcoin Dice Game - Complete Setup
echo ========================================
echo.
echo This will set up both backend and frontend
echo.

set "ROOT_DIR=%~dp0"

echo [1/2] Setting up Backend...
echo ========================================
call "%ROOT_DIR%setup-backend.bat"

echo.
echo.
echo [2/2] Setting up Frontend...
echo ========================================
call "%ROOT_DIR%setup-frontend.bat"

echo.
echo.
echo ========================================
echo Complete Setup Finished!
echo ========================================
echo.
echo IMPORTANT: Before starting the application:
echo   1. Edit backend\.env with your BlockCypher token and Bitcoin keys
echo   2. Make sure you have testnet Bitcoin for testing
echo.
echo Then run: start-all.bat
echo.
pause
