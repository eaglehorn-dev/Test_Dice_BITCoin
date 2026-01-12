@echo off
echo ========================================
echo Killing Servers on Ports 8000 and 8001
echo ========================================
echo.

echo Finding processes on ports 8000 and 8001...
netstat -ano | findstr ":8000 :8001"
echo.

echo Attempting to kill processes...
echo.

REM Kill port 8001
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001"') do (
    if not "%%a"=="0" (
        echo Killing process %%a on port 8001...
        taskkill /F /PID %%a 2>nul
    )
)

REM Kill port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do (
    if not "%%a"=="0" (
        echo Killing process %%a on port 8000...
        taskkill /F /PID %%a 2>nul
    )
)

echo.
echo Waiting for processes to close...
timeout /t 2 /nobreak >nul

echo.
echo Checking if ports are now free...
netstat -ano | findstr ":8000 :8001"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [WARNING] Some processes could not be killed.
    echo This usually means they require Administrator privileges.
    echo.
    echo To kill them:
    echo   1. Right-click this file
    echo   2. Select "Run as Administrator"
    echo.
) else (
    echo.
    echo [SUCCESS] All processes on ports 8000 and 8001 have been killed!
    echo.
)

pause
