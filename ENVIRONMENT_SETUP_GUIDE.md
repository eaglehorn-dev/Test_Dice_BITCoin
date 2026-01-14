# 🔧 Environment Setup Guide

**Complete guide for configuring Production and Test environments**

---

## 📋 **QUICK START**

### **For Testing/Development:**
```bash
cd backend
cp .env.test.example .env
# Edit .env and set TEST_MASTER_KEY
python -m uvicorn app.main:app
# Should see: 🧪 RUNNING IN TEST MODE 🧪
```

### **For Production:**
```bash
cd backend
cp .env.production.example .env
# Edit .env and set PROD_MASTER_KEY and other production values
python -m uvicorn app.main:app
# Should see: 🚨 RUNNING IN PRODUCTION MODE 🚨
# System will verify you're on Bitcoin mainnet
```

---

## 🎯 **ENVIRONMENT COMPARISON**

| Setting | Test Environment | Production Environment |
|---------|------------------|------------------------|
| **ENV_CURRENT** | `false` | `true` |
| **Database** | `dice_test` | `dice_prod` |
| **Bitcoin Network** | Testnet (fake BTC) | Mainnet (real BTC) |
| **Mempool API** | `/testnet/api` | `/api` |
| **Min Bet** | 100 sats (~$0.05) | 600 sats (~$0.30) |
| **Max Bet** | 100,000 sats (~$50) | 10,000,000 sats (~$5,000) |
| **Confirmations** | 0 (instant) | 1 (safer) |
| **TX Fee** | 100 sats | 500 sats |
| **Rate Limit** | 600/min (relaxed) | 120/min |
| **Reload** | `true` (hot reload) | `false` (stable) |
| **Debug** | `true` (verbose logs) | `false` (errors only) |
| **Log Level** | `DEBUG` | `INFO` |
| **Frontend URL** | `http://localhost:3000` | `https://yourdomain.com` |

---

## 🔐 **CRITICAL DIFFERENCES**

### **Test Environment:**
✅ **Safe for development**
- Uses Bitcoin **testnet** (fake BTC)
- No real money at risk
- Faster confirmations (0 required)
- Lower fees
- Debug mode enabled
- Hot reload for development

### **Production Environment:**
⚠️ **REAL MONEY - BE CAREFUL**
- Uses Bitcoin **mainnet** (real BTC)
- **Network validation** enforced
- Higher fees for reliability
- Confirmations required
- Debug mode disabled
- No hot reload (stable)
- **System exits if network mismatch detected**

---

## 📝 **STEP-BY-STEP SETUP**

### **1. Generate Encryption Keys**

**For Test:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Copy output to TEST_MASTER_KEY
```

**For Production:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Copy output to PROD_MASTER_KEY
# ⚠️  KEEP THIS SECRET AND BACKED UP!
```

### **2. Generate Secret Key**

```bash
openssl rand -hex 32
# Copy output to SECRET_KEY
```

### **3. Configure Database**

**Test:**
```env
MONGODB_URL_TEST=mongodb://localhost:27017
MONGODB_DB_NAME_TEST=dice_test
```

**Production:**
```env
MONGODB_URL_PROD=mongodb://your-prod-server:27017
MONGODB_DB_NAME_PROD=dice_prod
```

### **4. Set Environment Toggle**

**Test:**
```env
ENV_CURRENT=false
```

**Production:**
```env
ENV_CURRENT=true
```

---

## 🚀 **SWITCHING ENVIRONMENTS**

### **From Test to Production:**

**Option 1: Change ENV_CURRENT**
```env
# In .env file
ENV_CURRENT=true  # Change from false to true
```

**Option 2: Use Different .env Files**
```bash
# Save current .env as .env.test
mv .env .env.test

# Copy production template
cp .env.production.example .env

# Edit production values
nano .env
```

### **From Production to Test:**

```env
# In .env file
ENV_CURRENT=false  # Change from true to false
```

**⚠️  WARNING:** Always verify the banner on startup!
```
🧪 RUNNING IN TEST MODE 🧪     ← Safe
🚨 RUNNING IN PRODUCTION MODE 🚨  ← Real money!
```

---

## 🔍 **VERIFICATION**

### **Check Current Environment:**

**1. Look for startup banner:**
```bash
python -m uvicorn app.main:app
# Yellow banner = Test
# Red banner = Production
```

**2. Check logs:**
```
[CONFIG] Environment: TEST
[CONFIG] Database: dice_test
[CONFIG] Bitcoin Network: testnet
```

**3. Network validation (Production only):**
```
[VALIDATION] Running in PRODUCTION mode - verifying network...
[VALIDATION] ✓ Bitcoin network verified as MAINNET
```

---

## 🛡️ **SECURITY CHECKLIST**

### **Production Deployment:**

- [ ] `ENV_CURRENT=true`
- [ ] Strong `PROD_MASTER_KEY` (32+ chars)
- [ ] Strong `SECRET_KEY` (64 chars hex)
- [ ] Production MongoDB with authentication
- [ ] `DEBUG=false`
- [ ] `RELOAD=false`
- [ ] HTTPS frontend (`https://` not `http://`)
- [ ] Network validation passes
- [ ] Firewall configured
- [ ] SSL/TLS enabled
- [ ] `.env` file never committed to Git
- [ ] `.env` file backed up securely (encrypted)
- [ ] API keys from production services
- [ ] Monitoring and alerting configured

### **Test Environment:**

- [ ] `ENV_CURRENT=false`
- [ ] Separate test database
- [ ] Testnet APIs configured
- [ ] Lower bet limits
- [ ] Confirmations = 0 for speed
- [ ] Debug mode enabled
- [ ] Test API keys (or no keys)

---

## 🧪 **TESTING WORKFLOW**

### **1. Get Testnet BTC:**
```
https://testnet-faucet.mempool.co/
https://coinfaucet.eu/en/btc-testnet/
```

### **2. Generate Test Wallets:**
```bash
cd backend
python scripts/generate_wallets.py --generate-wallets 2 3 5
```

### **3. Test Deposits:**
- Send testnet BTC to wallet addresses
- Watch logs for transaction detection
- Verify bet processing

### **4. Test Payouts:**
- Check winning rolls trigger payouts
- Verify transactions on testnet explorer

### **5. Verify Everything Works:**
```bash
# Run verification script
./verify-ports.sh  # or verify-ports.bat on Windows
```

---

## 🔄 **MIGRATION WORKFLOW**

### **Test → Staging → Production**

**Step 1: Test Everything**
```bash
ENV_CURRENT=false
# Run full test suite
# Test all features
# Verify all integrations
```

**Step 2: Staging (Optional)**
```bash
# Use production settings but separate environment
ENV_CURRENT=true
MONGODB_DB_NAME_PROD=dice_staging
# Test with real mainnet but isolated
```

**Step 3: Production**
```bash
# Final production deployment
ENV_CURRENT=true
MONGODB_DB_NAME_PROD=dice_prod
# Monitor closely after deployment
```

---

## 📊 **MONITORING**

### **Production Monitoring:**

**1. System Health:**
```bash
# Check backend is running
curl https://yourdomain.com/api/stats

# Check admin
curl -H "X-Admin-API-Key: KEY" https://admin.yourdomain.com/admin/health
```

**2. Log Monitoring:**
```bash
tail -f dice_game_prod.log | grep ERROR
tail -f dice_game_prod.log | grep CRITICAL
```

**3. Database Monitoring:**
```bash
# Check bet volume
mongo dice_prod --eval "db.bets.count()"

# Check recent activity
mongo dice_prod --eval "db.bets.find().sort({created_at:-1}).limit(5).pretty()"
```

---

## 🆘 **TROUBLESHOOTING**

### **Issue: Wrong Environment**

**Symptoms:**
- Banner shows wrong mode
- Wrong database being used
- Wrong Bitcoin network

**Solution:**
```bash
# Check .env file
cat .env | grep ENV_CURRENT

# Should be:
ENV_CURRENT=false  # for test
ENV_CURRENT=true   # for production
```

### **Issue: Network Validation Failed**

**Error:**
```
[VALIDATION] FATAL: ENV_CURRENT=True but API is TESTNET!
```

**Solution:**
- Your API URLs are still pointing to testnet
- Check `MEMPOOL_API_PROD` is set correctly
- Should be `https://mempool.space/api` (no /testnet/)

### **Issue: Database Connection Failed**

**Solution:**
```bash
# Check MongoDB is running
systemctl status mongodb  # Linux
brew services list         # Mac
net start MongoDB          # Windows

# Check connection string
mongo "your-connection-string"
```

---

## 📋 **QUICK REFERENCE**

### **Test Environment (.env):**
```env
ENV_CURRENT=false
MONGODB_DB_NAME_TEST=dice_test
TEST_MASTER_KEY=your-test-key
BTC_NETWORK_TEST=testnet
DEBUG=true
RELOAD=true
```

### **Production Environment (.env):**
```env
ENV_CURRENT=true
MONGODB_DB_NAME_PROD=dice_prod
PROD_MASTER_KEY=your-prod-key
BTC_NETWORK_PROD=mainnet
DEBUG=false
RELOAD=false
```

---

## ✅ **FINAL CHECKLIST**

### **Before Going to Production:**

- [ ] All features tested in test environment
- [ ] Database backed up
- [ ] Encryption keys secured and backed up
- [ ] SSL/TLS certificates installed
- [ ] Firewall rules configured
- [ ] Monitoring and alerts set up
- [ ] Admin dashboard accessible and secured
- [ ] Emergency shutdown procedure documented
- [ ] Team trained on admin tools
- [ ] Legal compliance verified
- [ ] Customer support ready

---

**Ready to deploy!** 🚀
