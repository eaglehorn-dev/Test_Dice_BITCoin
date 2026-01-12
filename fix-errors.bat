@echo off
echo ========================================
echo Bitcoin Dice - Error Fix Script
echo ========================================
echo.

echo This will fix common errors:
echo   1. Backend: 'await' outside async function
echo   2. Frontend: Dev Server configuration error
echo.
pause

echo [1/2] Fixing Frontend...
cd /d "%~dp0frontend"

echo Installing http-proxy-middleware...
npm install http-proxy-middleware@2.0.6

echo Creating .env file...
(
    echo REACT_APP_API_URL=http://localhost:8000
    echo DANGEROUSLY_DISABLE_HOST_CHECK=true
    echo FAST_REFRESH=true
) > .env

echo Frontend fixed!
echo.

cd /d "%~dp0"

echo [2/2] Backend...
echo The backend syntax errors have been fixed in the code.
echo If you still see errors, make sure you have the latest version.
echo.

echo ========================================
echo Fixes Applied!
echo ========================================
echo.
echo Now try running: start-all.bat
echo.
pause
