#!/bin/bash

echo "========================================"
echo "Starting Admin Frontend"
echo "========================================"
echo ""

cd "$(dirname "$0")"

if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo ""
echo "Starting Admin Frontend on port 3001..."
echo ""
echo "IMPORTANT: Make sure to configure your .env file!"
echo ""

npm start
