@echo off
echo ========================================
echo Starting Admin Frontend
echo ========================================
echo.

cd /d "%~dp0"

if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)

echo.
echo Starting Admin Frontend on port 3001...
echo.
echo IMPORTANT: Make sure to configure your .env file!
echo.

npm start

pause
