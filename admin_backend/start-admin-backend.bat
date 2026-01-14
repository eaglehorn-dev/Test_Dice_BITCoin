@echo off
echo ========================================
echo Starting Admin Backend Server
echo ========================================
echo.

cd /d "%~dp0"

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing/Updating dependencies...
pip install -r requirements.txt

echo.
echo Starting Admin Backend on port 8001...
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

pause
