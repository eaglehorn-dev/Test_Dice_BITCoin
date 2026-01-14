# 🔐 Bitcoin Dice Game - Admin Backend

**Secure Admin Management System**

A separate, isolated backend for managing your Bitcoin dice game. This runs on a different port (8001) and is protected by API key authentication + IP whitelisting for maximum security.

---

## 🚀 **Quick Start**

### **1. Setup Environment**

```bash
cp .env.example .env
nano .env  # Configure your settings
```

**Critical Environment Variables:**
- `ADMIN_API_KEY`: 32+ character secret key
- `ADMIN_IP_WHITELIST`: Comma-separated IPs (e.g., `127.0.0.1,192.168.1.100`)
- `MASTER_ENCRYPTION_KEY`: Same key from main backend (to decrypt wallets)
- `COLD_STORAGE_ADDRESS`: Your secure offline Bitcoin wallet
- `MONGODB_URL`: Same MongoDB connection as main backend

### **2. Start Server**

**Windows:**
```cmd
start-admin-backend.bat
```

**Linux/Mac:**
```bash
chmod +x start-admin-backend.sh
./start-admin-backend.sh
```

Server will run on: `http://localhost:8001`

---

## 🔒 **Security Features**

### **API Key Authentication**
All `/admin/*` endpoints require `X-Admin-API-Key` header:

```bash
curl -H "X-Admin-API-Key: YOUR_SECRET_KEY" http://localhost:8001/admin/dashboard
```

### **IP Whitelisting**
Only requests from whitelisted IPs are allowed. Configure in `.env`:

```env
ADMIN_IP_WHITELIST=127.0.0.1,::1,YOUR_OFFICE_IP
```

### **Encrypted Vault**
Private keys are never exposed. They're decrypted in memory only during withdrawals.

---

## 📊 **API Endpoints**

### **Dashboard**
`GET /admin/dashboard`
- Total treasury balance (BTC + USD)
- Today/Week/Month/All-time stats
- All wallets with live balances
- Volume by multiplier

### **Wallet Management**
- `POST /admin/wallet/generate` - Generate new wallet
- `GET /admin/wallets?include_balance=true` - List all wallets

### **Treasury**
- `POST /admin/treasury/withdraw` - Withdraw to cold storage

```json
{
  "wallet_id": "507f1f77bcf86cd799439011",
  "amount_sats": 1000000
}
```

### **Analytics**
- `GET /admin/stats/{period}` - Income/Outcome stats (today, week, month, year, all)
- `GET /admin/analytics/volume` - Bet volume by multiplier
- `GET /admin/analytics/daily?days=30` - Daily stats

---

## 🎯 **Features**

### **Wallet Vault**
- Generate Bitcoin wallets dynamically
- Assign multipliers (2x, 3x, 5x, etc.)
- Private keys encrypted with AES-256
- Track usage statistics per wallet

### **Treasury Management**
- View real-time wallet balances
- Withdraw funds to cold storage
- Secure transaction signing
- Fee estimation and optimization

### **Analytics Engine**
- MongoDB aggregation pipelines
- Income vs. Outcome tracking
- Profit/Loss by period
- Bet volume by multiplier
- Win rate calculations

### **Price Conversion**
- Live BTC/USD from CoinGecko
- Auto-convert satoshis to USD
- Cached for 60s to avoid rate limits

---

## 🗂️ **Project Structure**

```
admin_backend/
├── app/
│   ├── api/
│   │   └── admin_routes.py         # API endpoints
│   ├── core/
│   │   └── config.py                # Configuration
│   ├── dtos/
│   │   └── admin_dtos.py            # Request/Response models
│   ├── middleware/
│   │   └── auth.py                  # API key + IP auth
│   ├── services/
│   │   ├── analytics_service.py     # MongoDB aggregations
│   │   ├── crypto_service.py        # AES-256 encryption
│   │   ├── price_service.py         # BTC/USD price
│   │   ├── treasury_service.py      # Withdrawals
│   │   └── wallet_service.py        # Wallet management
│   ├── utils/
│   │   └── database.py              # MongoDB connection
│   └── main.py                      # FastAPI app
├── .env                              # Your configuration
├── .env.example                      # Example config
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

---

## 🔐 **Setup Checklist**

- [ ] Copy `.env.example` to `.env`
- [ ] Set `ADMIN_API_KEY` (32+ characters, random)
- [ ] Configure `ADMIN_IP_WHITELIST` with your IPs
- [ ] Set `MASTER_ENCRYPTION_KEY` (same as main backend)
- [ ] Set `COLD_STORAGE_ADDRESS` (your secure wallet)
- [ ] Set `MONGODB_URL` (same database as main backend)
- [ ] Run `start-admin-backend.bat` (or `.sh` on Linux)
- [ ] Test health: `curl http://localhost:8001/admin/health`
- [ ] Deploy frontend: `cd ../admin_frontend && npm start`

---

## 🛡️ **Production Deployment**

### **Firewall Rules**
```bash
# Only allow specific IPs
sudo ufw allow from YOUR_OFFICE_IP to any port 8001
sudo ufw deny 8001
```

### **Nginx Reverse Proxy**
```nginx
location /admin-api/ {
    proxy_pass http://127.0.0.1:8001/;
    allow YOUR_OFFICE_IP;
    deny all;
}
```

### **Environment Variables**
- Use environment-specific `.env` files
- Never commit `.env` to version control
- Rotate `ADMIN_API_KEY` regularly

---

## 📈 **Usage Examples**

### **Generate a 10x Wallet**
```bash
curl -X POST http://localhost:8001/admin/wallet/generate \
  -H "X-Admin-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"multiplier": 10}'
```

### **Get Dashboard Data**
```bash
curl http://localhost:8001/admin/dashboard \
  -H "X-Admin-API-Key: YOUR_KEY"
```

### **Withdraw to Cold Storage**
```bash
curl -X POST http://localhost:8001/admin/treasury/withdraw \
  -H "X-Admin-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_id": "507f1f77bcf86cd799439011",
    "amount_sats": 1000000
  }'
```

---

## 🆘 **Troubleshooting**

### **401 Unauthorized**
- Check `X-Admin-API-Key` header matches `.env`
- Verify key is 32+ characters

### **403 Forbidden**
- Your IP not in whitelist
- Add your IP to `ADMIN_IP_WHITELIST` in `.env`

### **500 Server Error**
- Check MongoDB connection
- Verify `MASTER_ENCRYPTION_KEY` is correct
- Check logs: `tail -f admin_backend.log`

---

## 📝 **License**

Same as main project.

---

**Built with FastAPI + MongoDB + AES-256 Encryption**
