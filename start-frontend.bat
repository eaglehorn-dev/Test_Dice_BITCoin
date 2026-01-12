@echo off
echo ========================================
echo Starting Bitcoin Dice Frontend
echo ========================================
echo.

cd /d "%~dp0frontend"

REM Check if node_modules exists
if not exist "node_modules\" (
    echo [ERROR] node_modules not found!
    echo Please run setup-frontend.bat first
    pause
    exit /b 1
)

echo Starting React development server...
echo This will open http://localhost:3000 in your browser
echo Press Ctrl+C to stop
echo.

npm start

pause
