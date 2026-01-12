@echo off
echo ========================================
echo Bitcoin Dice Frontend Setup
echo ========================================
echo.

cd /d "%~dp0frontend"

REM Check Node.js installation
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH!
    echo Please install Node.js 16+ from https://nodejs.org/
    pause
    exit /b 1
)

REM Check npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm is not available!
    pause
    exit /b 1
)

echo [1/2] Installing dependencies...
echo This may take a few minutes...
echo.
npm install

echo.
echo [2/2] Setting up configuration...
if exist ".env" (
    echo .env already exists, skipping...
) else (
    echo Creating .env file...
    (
        echo REACT_APP_API_URL=http://localhost:8000
        echo DANGEROUSLY_DISABLE_HOST_CHECK=true
        echo FAST_REFRESH=true
    ) > .env
    echo .env file created with default configuration
)

echo.
echo ========================================
echo Frontend Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Run start-frontend.bat to start the dev server
echo   2. Or use start-all.bat to start everything
echo.
pause
