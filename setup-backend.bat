@echo off
echo ========================================
echo Bitcoin Dice Backend Setup
echo ========================================
echo.

cd /d "%~dp0backend"

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
if exist "venv\" (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    echo Virtual environment created!
)

echo.
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [3/4] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [4/4] Setting up configuration...
if exist ".env" (
    echo .env already exists, skipping...
) else (
    if exist "env.example.txt" (
        copy env.example.txt .env >nul
        echo .env file created from template
        echo.
        echo ========================================
        echo IMPORTANT: Edit .env file now!
        echo ========================================
        echo You must configure:
        echo   - BLOCKCYPHER_API_TOKEN
        echo   - HOUSE_PRIVATE_KEY
        echo   - HOUSE_ADDRESS
        echo.
    ) else (
        echo [WARNING] env.example.txt not found
    )
)

echo.
echo [5/5] Initializing database...
python -c "from app.database import init_db; init_db()"

echo.
echo ========================================
echo Backend Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Edit backend\.env with your credentials
echo   2. Run start-backend.bat to start the server
echo.
pause
