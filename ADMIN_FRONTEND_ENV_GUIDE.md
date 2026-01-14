# 🎨 Admin Frontend .env Configuration

## ✅ **Admin Frontend .env Created**

**Location:** `D:\Dice2\admin_frontend\.env`

---

## 📋 **Your Admin Frontend Environment:**

```env
REACT_APP_API_URL=http://localhost:8001
REACT_APP_ADMIN_API_KEY=d4ce002055be58b0adfc5d674221e4c6f23d5c9a501e08c9bff3cc6e09f6fdc4
PORT=3001
REACT_APP_WS_URL=ws://localhost:8001
REACT_APP_TITLE=Bitcoin Dice - Admin Dashboard
REACT_APP_DESCRIPTION=Admin Management System
BROWSER=none
SKIP_PREFLIGHT_CHECK=true
```

---

## 🔑 **Environment Variables Explained:**

| Variable | Value | Purpose |
|----------|-------|---------|
| `REACT_APP_API_URL` | `http://localhost:8001` | Admin backend API endpoint |
| `REACT_APP_ADMIN_API_KEY` | `d4ce00...` | Admin API key for authentication |
| `PORT` | `3001` | Admin frontend port (different from main game) |
| `REACT_APP_WS_URL` | `ws://localhost:8001` | WebSocket for real-time updates |
| `BROWSER` | `none` | Don't auto-open browser on start |

---

## 🚀 **How to Start Admin Frontend:**

```bash
cd D:\Dice2\admin_frontend
npm start
```

**Expected Output:**
```
Compiled successfully!

You can now view bitcoin-dice-admin in the browser.

  Local:            http://localhost:3001
  On Your Network:  http://192.168.x.x:3001
```

---

## 🌐 **Access Points:**

- **Admin Dashboard:** `http://localhost:3001`
- **Admin Backend API:** `http://localhost:8001`
- **Main Game Frontend:** `http://localhost:3000` (different)
- **Main Game Backend:** `http://localhost:8000` (different)

---

## 🔐 **Authentication:**

The admin frontend automatically uses the API key from the `.env` file:

```javascript
// In your API calls (automatic)
headers: {
  'X-API-Key': 'd4ce002055be58b0adfc5d674221e4c6f23d5c9a501e08c9bff3cc6e09f6fdc4'
}
```

---

## ⚙️ **Port Configuration:**

### **Complete System Ports:**

| Service | Port | URL |
|---------|------|-----|
| MongoDB | 27017 | Database |
| Main Backend | 8000 | `http://localhost:8000` |
| **Admin Backend** | **8001** | `http://localhost:8001` |
| Main Frontend | 3000 | `http://localhost:3000` |
| **Admin Frontend** | **3001** | `http://localhost:3001` |

---

## 📝 **To Edit Configuration:**

```bash
cd D:\Dice2\admin_frontend
notepad .env
```

**Remember to restart the frontend after editing:**
```bash
# Ctrl+C to stop
npm start  # Start again
```

---

## 🆕 **For Production:**

Update the `.env` file with production values:

```env
# Production Configuration
REACT_APP_API_URL=https://admin-api.yourdomain.com
REACT_APP_ADMIN_API_KEY=your-production-key-here
PORT=3001
REACT_APP_WS_URL=wss://admin-api.yourdomain.com
```

---

## 🧪 **Testing the Setup:**

### **1. Check if admin backend is running:**
```bash
curl http://localhost:8001/admin/health
```

### **2. Start admin frontend:**
```bash
cd D:\Dice2\admin_frontend
npm start
```

### **3. Open browser:**
```
http://localhost:3001
```

**Expected:** Admin dashboard loads with charts and wallet grid

---

## 🛠️ **Troubleshooting:**

### **Error: "Cannot connect to backend"**
- ✅ Make sure admin backend is running on port 8001
- ✅ Check `REACT_APP_API_URL` in `.env`

### **Error: "API key required"**
- ✅ Check `REACT_APP_ADMIN_API_KEY` matches admin_backend/.env
- ✅ Make sure it's at least 32 characters

### **Error: "Port 3001 already in use"**
- ✅ Another process is using port 3001
- ✅ Change `PORT` in `.env` to 3002 or another port

---

## 📚 **React Environment Variables:**

**Important Rules:**
- ✅ Must start with `REACT_APP_`
- ✅ Restart frontend after changing
- ✅ Don't include sensitive data (API keys are OK for admin-only apps)

---

## 🎯 **Quick Start Checklist:**

- [x] Admin backend `.env` created
- [x] Admin frontend `.env` created
- [x] API key configured
- [x] Ports configured (8001, 3001)
- [ ] Start admin backend
- [ ] Start admin frontend
- [ ] Access dashboard

---

**Your admin frontend is now fully configured!** 🎉
