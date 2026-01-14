# 🔑 Admin API Key - Complete Guide

## 📍 **Where to Find Your Admin API Key**

### **Option 1: Check Your `.env` File**

```bash
# Open the .env file
cd D:\Dice2\backend
notepad .env
```

**Look for this line:**
```env
ADMIN_API_KEY=d4ce002055be58b0adfc5d674221e4c6f23d5c9a501e08c9bff3cc6e09f6fdc4
```

**Your API Key:**
```
d4ce002055be58b0adfc5d674221e4c6f23d5c9a501e08c9bff3cc6e09f6fdc4
```

---

## 🔒 **How to Use the Admin API Key**

### **Method 1: Frontend Login (Recommended)**

When you open the admin frontend, you'll be prompted to enter the API key:

1. **Start Admin Frontend:**
   ```bash
   cd D:\Dice2\admin_frontend
   npm start
   ```

2. **Open:** `http://localhost:3001`

3. **Enter API Key when prompted:**
   ```
   d4ce002055be58b0adfc5d674221e4c6f23d5c9a501e08c9bff3cc6e09f6fdc4
   ```

4. **Access Dashboard** ✅

---

### **Method 2: Direct API Calls (For Testing)**

Use the API key in the HTTP header:

**Using curl:**
```bash
curl -H "X-API-Key: d4ce002055be58b0adfc5d674221e4c6f23d5c9a501e08c9bff3cc6e09f6fdc4" \
  http://localhost:8001/admin/dashboard
```

**Using Postman:**
1. Add Header: `X-API-Key`
2. Value: `d4ce002055be58b0adfc5d674221e4c6f23d5c9a501e08c9bff3cc6e09f6fdc4`

**Using JavaScript (fetch):**
```javascript
fetch('http://localhost:8001/admin/dashboard', {
  headers: {
    'X-API-Key': 'd4ce002055be58b0adfc5d674221e4c6f23d5c9a501e08c9bff3cc6e09f6fdc4'
  }
})
```

---

## 🆕 **How to Generate a New API Key**

### **Step 1: Generate New Key**

**Using Python:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Example Output:**
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

### **Step 2: Update `.env` File**

```bash
cd D:\Dice2\backend
notepad .env
```

**Find and replace:**
```env
# OLD
ADMIN_API_KEY=d4ce002055be58b0adfc5d674221e4c6f23d5c9a501e08c9bff3cc6e09f6fdc4

# NEW
ADMIN_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

### **Step 3: Restart Admin Backend**

```bash
cd D:\Dice2\admin_backend
.\start-admin-backend.bat
```

**Done!** New API key is active.

---

## 📋 **Quick Reference**

### **Your Current API Key:**
```
d4ce002055be58b0adfc5d674221e4c6f23d5c9a501e08c9bff3cc6e09f6fdc4
```

### **Location:**
```
D:\Dice2\backend\.env
```

### **Environment Variable:**
```
ADMIN_API_KEY
```

### **Header Name:**
```
X-API-Key
```

---

## 🔐 **Security Best Practices**

### ✅ **DO:**
- ✅ Store in `.env` file (already done)
- ✅ Use HTTPS in production
- ✅ Keep it secret (never commit to Git)
- ✅ Use password manager to save it
- ✅ Change it regularly in production

### ❌ **DON'T:**
- ❌ Share in public repos
- ❌ Hardcode in frontend code
- ❌ Send over unencrypted channels
- ❌ Use weak keys (use 32+ chars)

---

## 🧪 **Testing the API Key**

### **1. Test Health Endpoint (No Auth Required):**
```bash
curl http://localhost:8001/admin/health
```

**Expected:**
```json
{
  "status": "healthy",
  "service": "admin-backend"
}
```

### **2. Test Protected Endpoint:**
```bash
# Without API Key (Should FAIL)
curl http://localhost:8001/admin/wallets

# With API Key (Should SUCCEED)
curl -H "X-API-Key: d4ce002055be58b0adfc5d674221e4c6f23d5c9a501e08c9bff3cc6e09f6fdc4" \
  http://localhost:8001/admin/wallets
```

**Without Key:**
```json
{
  "detail": "Admin API key required"
}
```

**With Key:**
```json
[
  {
    "wallet_id": "...",
    "multiplier": 2,
    "address": "bc1q...",
    ...
  }
]
```

---

## 🌐 **Admin Endpoints**

All these require the `X-API-Key` header:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/health` | GET | Health check (no auth) |
| `/admin/dashboard` | GET | Full dashboard data |
| `/admin/wallets` | GET | All vault wallets |
| `/admin/wallet/generate` | POST | Generate new wallet |
| `/admin/treasury/withdraw` | POST | Withdraw to cold storage |
| `/admin/stats/{period}` | GET | Statistics (today/week/month) |
| `/admin/analytics/volume` | GET | Volume by multiplier |
| `/admin/analytics/daily` | GET | Daily stats |

---

## 🚀 **Quick Start**

### **1. Copy Your API Key:**
```
d4ce002055be58b0adfc5d674221e4c6f23d5c9a501e08c9bff3cc6e09f6fdc4
```

### **2. Start Admin Backend:**
```bash
cd D:\Dice2\admin_backend
.\start-admin-backend.bat
```

### **3. Start Admin Frontend:**
```bash
cd D:\Dice2\admin_frontend
npm start
```

### **4. Open Browser:**
```
http://localhost:3001
```

### **5. Login with API Key**
Paste the key when prompted.

---

## 🆘 **Troubleshooting**

### **Error: "Admin API key required"**
- ✅ Check if key is in `backend/.env`
- ✅ Restart admin backend after adding key
- ✅ Make sure header name is `X-API-Key` (case-sensitive)

### **Error: "Invalid admin API key"**
- ✅ Check for typos in the key
- ✅ Make sure no extra spaces
- ✅ Verify key in `.env` matches the one you're using

### **Error: "ADMIN_API_KEY must be at least 32 characters"**
- ✅ Key too short
- ✅ Generate new one with `secrets.token_hex(32)`

---

## 📝 **Save This Information**

**Recommended: Save in Password Manager**

```
Service: Bitcoin Dice - Admin Backend
URL: http://localhost:8001
API Key: d4ce002055be58b0adfc5d674221e4c6f23d5c9a501e08c9bff3cc6e09f6fdc4
Header: X-API-Key
Notes: For admin dashboard access
```

---

## ⚙️ **For Production**

When deploying to production:

1. **Generate a NEW key** (don't use this test key)
2. **Use environment variables** on your server
3. **Enable HTTPS** for secure transmission
4. **Add IP whitelist** for extra security
5. **Rotate keys** every 90 days

---

**That's it! You now have full access to the admin backend.** 🎉
