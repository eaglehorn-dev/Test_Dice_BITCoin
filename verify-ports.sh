#!/bin/bash

echo "========================================"
echo "Port Configuration Verification"
echo "========================================"
echo ""

echo "Checking if ports are available..."
echo ""

echo "[Backend - Port 8000]"
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 8000 is IN USE"
else
    echo "✅ Port 8000 is AVAILABLE"
fi
echo ""

echo "[Admin Backend - Port 8001]"
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 8001 is IN USE"
else
    echo "✅ Port 8001 is AVAILABLE"
fi
echo ""

echo "[Frontend - Port 3000]"
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 3000 is IN USE"
else
    echo "✅ Port 3000 is AVAILABLE"
fi
echo ""

echo "[Admin Frontend - Port 3001]"
if lsof -Pi :3001 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 3001 is IN USE"
else
    echo "✅ Port 3001 is AVAILABLE"
fi
echo ""

echo "========================================"
echo "Configuration Files Check"
echo "========================================"
echo ""

echo "[Backend Config]"
if grep -q "PORT: int = 8000" backend/app/core/config.py 2>/dev/null; then
    echo "✅ Backend configured for port 8000"
else
    echo "❌ Backend port configuration ERROR"
fi

echo "[Admin Backend Config]"
if grep -q "PORT: int = 8001" admin_backend/app/core/config.py 2>/dev/null; then
    echo "✅ Admin Backend configured for port 8001"
else
    echo "❌ Admin Backend port configuration ERROR"
fi

echo "[Frontend Proxy]"
if grep -q "target: 'http://localhost:8000'" frontend/src/setupProxy.js 2>/dev/null; then
    echo "✅ Frontend proxy points to port 8000"
else
    echo "❌ Frontend proxy configuration ERROR"
fi

echo "[Admin Frontend API]"
if grep -q "'http://localhost:8001'" admin_frontend/src/services/api.js 2>/dev/null; then
    echo "✅ Admin Frontend points to port 8001"
else
    echo "❌ Admin Frontend API configuration ERROR"
fi

echo ""
echo "========================================"
echo "Summary"
echo "========================================"
echo ""
echo "Dice Game Backend:  http://localhost:8000"
echo "Admin Backend:      http://localhost:8001"
echo "Dice Game Frontend: http://localhost:3000"
echo "Admin Frontend:     http://localhost:3001"
echo ""
