@echo off
echo ========================================
echo Port Configuration Verification
echo ========================================
echo.

echo Checking if ports are available...
echo.

echo [Backend - Port 8000]
netstat -ano | findstr ":8000" >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  Port 8000 is IN USE
) else (
    echo ✅ Port 8000 is AVAILABLE
)
echo.

echo [Admin Backend - Port 8001]
netstat -ano | findstr ":8001" >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  Port 8001 is IN USE
) else (
    echo ✅ Port 8001 is AVAILABLE
)
echo.

echo [Frontend - Port 3000]
netstat -ano | findstr ":3000" >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  Port 3000 is IN USE
) else (
    echo ✅ Port 3000 is AVAILABLE
)
echo.

echo [Admin Frontend - Port 3001]
netstat -ano | findstr ":3001" >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  Port 3001 is IN USE
) else (
    echo ✅ Port 3001 is AVAILABLE
)
echo.

echo ========================================
echo Configuration Files Check
echo ========================================
echo.

echo [Backend Config]
findstr /C:"PORT: int = 8000" backend\app\core\config.py >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend configured for port 8000
) else (
    echo ❌ Backend port configuration ERROR
)

echo [Admin Backend Config]
findstr /C:"PORT: int = 8001" admin_backend\app\core\config.py >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Admin Backend configured for port 8001
) else (
    echo ❌ Admin Backend port configuration ERROR
)

echo [Frontend Proxy]
findstr /C:"target: 'http://localhost:8000'" frontend\src\setupProxy.js >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Frontend proxy points to port 8000
) else (
    echo ❌ Frontend proxy configuration ERROR
)

echo [Admin Frontend API]
findstr /C:"'http://localhost:8001'" admin_frontend\src\services\api.js >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Admin Frontend points to port 8001
) else (
    echo ❌ Admin Frontend API configuration ERROR
)

echo.
echo ========================================
echo Summary
echo ========================================
echo.
echo Dice Game Backend:  http://localhost:8000
echo Admin Backend:      http://localhost:8001
echo Dice Game Frontend: http://localhost:3000
echo Admin Frontend:     http://localhost:3001
echo.

pause
