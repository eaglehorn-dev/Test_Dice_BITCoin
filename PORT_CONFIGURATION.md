# 🔌 Port Configuration Guide

**Correct Port Assignment for All Services**

---

## 📊 **PORT ASSIGNMENTS**

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **Dice Game Backend** | `8000` | `http://localhost:8000` | Main game API |
| **Dice Game Frontend** | `3000` | `http://localhost:3000` | Public game UI |
| **Admin Backend** | `8001` | `http://localhost:8001` | Admin API (secured) |
| **Admin Frontend** | `3001` | `http://localhost:3001` | Admin dashboard UI |

---

## ✅ **VERIFIED CONFIGURATIONS**

### **1. Dice Game Backend** (Port 8000)

**File:** `backend/app/core/config.py`
```python
PORT: int = 8000
```

**File:** `backend/env.example.txt`
```env
PORT=8000
```

### **2. Dice Game Frontend** (Port 3000)

**File:** `frontend/package.json`
```json
{
  "proxy": "http://localhost:8000"
}
```

**File:** `frontend/src/utils/api.js`
```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

**File:** `frontend/src/setupProxy.js`
```javascript
target: 'http://localhost:8000'
```

**File:** `frontend/.env` (or `.env.example`)
```env
PORT=3000
REACT_APP_API_URL=http://localhost:8000
```

### **3. Admin Backend** (Port 8001)

**File:** `admin_backend/app/core/config.py`
```python
PORT: int = 8001
```

**File:** `admin_backend/.env.example`
```env
PORT=8001
```

### **4. Admin Frontend** (Port 3001)

**File:** `admin_frontend/package.json`
```json
{
  "proxy": "http://localhost:8001"
}
```

**File:** `admin_frontend/src/services/api.js`
```javascript
const API_BASE_URL = process.env.REACT_APP_ADMIN_API_URL || 'http://localhost:8001';
```

**File:** `admin_frontend/.env`
```env
PORT=3001
REACT_APP_ADMIN_API_URL=http://localhost:8001
REACT_APP_ADMIN_API_KEY=your-admin-api-key
```

---

## 🚀 **STARTUP ORDER**

### **For Development:**

1. **Start Dice Game Backend** (Port 8000):
   ```bash
   cd backend
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Start Admin Backend** (Port 8001):
   ```bash
   cd admin_backend
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
   ```

3. **Start Dice Game Frontend** (Port 3000):
   ```bash
   cd frontend
   npm start
   # Opens at http://localhost:3000
   ```

4. **Start Admin Frontend** (Port 3001):
   ```bash
   cd admin_frontend
   npm start
   # Opens at http://localhost:3001
   ```

### **Using Start Scripts:**

**Windows:**
```cmd
:: Start backends
cd backend && start-backend.bat
cd admin_backend && start-admin-backend.bat

:: Start frontends
cd frontend && npm start
cd admin_frontend && npm start
```

**Linux/Mac:**
```bash
# Start backends
cd backend && ./start-backend.sh &
cd admin_backend && ./start-admin-backend.sh &

# Start frontends
cd frontend && npm start &
cd admin_frontend && npm start &
```

---

## 🔍 **VERIFICATION**

### **Check if Ports are in Use:**

**Windows:**
```cmd
netstat -ano | findstr :8000
netstat -ano | findstr :8001
netstat -ano | findstr :3000
netstat -ano | findstr :3001
```

**Linux/Mac:**
```bash
lsof -i :8000
lsof -i :8001
lsof -i :3000
lsof -i :3001
```

### **Test API Endpoints:**

**Dice Game Backend (8000):**
```bash
curl http://localhost:8000/
curl http://localhost:8000/api/stats
```

**Admin Backend (8001):**
```bash
curl -H "X-Admin-API-Key: YOUR_KEY" http://localhost:8001/admin/health
```

**Dice Game Frontend (3000):**
```
http://localhost:3000
```

**Admin Frontend (3001):**
```
http://localhost:3001
```

---

## 🛠️ **TROUBLESHOOTING**

### **Issue: Port Already in Use**

**Error Message:**
```
OSError: [Errno 98] Address already in use
```

**Solution:**

**Windows:**
```cmd
:: Find process using port
netstat -ano | findstr :8000

:: Kill process (replace PID with actual process ID)
taskkill /F /PID <PID>
```

**Linux/Mac:**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9
```

### **Issue: Frontend Can't Connect to Backend**

**Symptoms:**
- API calls fail
- Network errors in browser console
- CORS errors

**Solution:**
1. Check backend is running: `curl http://localhost:8000/`
2. Check `.env` file has correct `REACT_APP_API_URL=http://localhost:8000`
3. Restart frontend: `npm start`
4. Check `setupProxy.js` target is `http://localhost:8000`

### **Issue: Admin Frontend Can't Connect**

**Symptoms:**
- 401 Unauthorized
- 403 Forbidden
- Connection refused

**Solution:**
1. Verify admin backend running: `curl http://localhost:8001/admin/health`
2. Check `.env` has `REACT_APP_ADMIN_API_URL=http://localhost:8001`
3. Verify `REACT_APP_ADMIN_API_KEY` matches backend
4. Check IP is whitelisted in admin backend

---

## 🌐 **PRODUCTION DEPLOYMENT**

### **Reverse Proxy (Nginx):**

```nginx
# Dice Game
server {
    listen 443 ssl;
    server_name yourgame.com;

    location / {
        proxy_pass http://localhost:3000;
    }

    location /api/ {
        proxy_pass http://localhost:8000/api/;
    }

    location /ws/ {
        proxy_pass http://localhost:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Admin Dashboard
server {
    listen 443 ssl;
    server_name admin.yourgame.com;

    location / {
        proxy_pass http://localhost:3001;
    }

    location /admin/ {
        proxy_pass http://localhost:8001/admin/;
        # IP whitelist
        allow YOUR_OFFICE_IP;
        deny all;
    }
}
```

### **Firewall Rules:**

```bash
# Public access to dice game
sudo ufw allow 8000/tcp
sudo ufw allow 3000/tcp

# Restricted access to admin
sudo ufw allow from YOUR_OFFICE_IP to any port 8001
sudo ufw allow from YOUR_OFFICE_IP to any port 3001
sudo ufw deny 8001/tcp
sudo ufw deny 3001/tcp
```

---

## 📋 **QUICK REFERENCE**

### **Development URLs:**
- Dice Game: http://localhost:3000
- Admin Dashboard: http://localhost:3001
- Dice API: http://localhost:8000
- Admin API: http://localhost:8001

### **API Endpoints:**
- Dice Game API: http://localhost:8000/api/*
- Dice Game WebSocket: ws://localhost:8000/ws/bets
- Admin API: http://localhost:8001/admin/*

### **Health Checks:**
- Dice Backend: http://localhost:8000/
- Admin Backend: http://localhost:8001/admin/health

---

## ✅ **CONFIGURATION CHECKLIST**

### **Backend (.env):**
- [ ] `PORT=8000`
- [ ] `FRONTEND_URL=http://localhost:3000`

### **Frontend (.env):**
- [ ] `PORT=3000`
- [ ] `REACT_APP_API_URL=http://localhost:8000`

### **Admin Backend (.env):**
- [ ] `PORT=8001`
- [ ] `FRONTEND_URL=http://localhost:3001`

### **Admin Frontend (.env):**
- [ ] `PORT=3001`
- [ ] `REACT_APP_ADMIN_API_URL=http://localhost:8001`
- [ ] `REACT_APP_ADMIN_API_KEY=<your-key>`

---

**All port configurations verified and documented!** ✅
