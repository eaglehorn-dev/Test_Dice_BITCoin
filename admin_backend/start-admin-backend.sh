#!/bin/bash

echo "========================================"
echo "Starting Admin Backend Server"
echo "========================================"
echo ""

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing/Updating dependencies..."
pip install -r requirements.txt

echo ""
echo "Starting Admin Backend on port 8001..."
echo ""
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
