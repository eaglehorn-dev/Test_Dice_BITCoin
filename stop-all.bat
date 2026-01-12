@echo off
echo ========================================
echo Stopping Bitcoin Dice Services
echo ========================================
echo.

echo Stopping backend (Python)...
taskkill /FI "WINDOWTITLE eq Bitcoin Dice - Backend*" /F >nul 2>&1

echo Stopping frontend (Node.js)...
taskkill /FI "WINDOWTITLE eq Bitcoin Dice - Frontend*" /F >nul 2>&1

REM Also kill by process if windows were closed
taskkill /FI "IMAGENAME eq python.exe" /FI "MEMUSAGE gt 50000" >nul 2>&1
taskkill /FI "IMAGENAME eq node.exe" /FI "MEMUSAGE gt 50000" >nul 2>&1

echo.
echo All services stopped!
echo.
pause
