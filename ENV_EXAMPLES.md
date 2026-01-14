# 📝 Environment Configuration Examples

**Complete .env file examples for Production and Test environments**

---

## 🚨 **PRODUCTION ENVIRONMENT (.env)**

**Copy this to `backend/.env` for production deployment:**

```env
# ============================================================
# PRODUCTION ENVIRONMENT CONFIGURATION
# ============================================================
# ⚠️  CRITICAL: This is for REAL MONEY on Bitcoin MAINNET
# ⚠️  NEVER commit this file with real values to version control!
# ============================================================

# ============================================================
# ENVIRONMENT TOGGLE
# ============================================================
# TRUE = Production (Mainnet, real money, prod database)
ENV_CURRENT=true

# ============================================================
# PRODUCTION DATABASE
# ============================================================
MONGODB_URL_PROD=mongodb://localhost:27017
MONGODB_DB_NAME_PROD=dice_prod

# ============================================================
# PRODUCTION ENCRYPTION KEY
# ============================================================
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# ⚠️  KEEP THIS SECRET! If lost, wallet private keys are unrecoverable!
PROD_MASTER_KEY=your-production-fernet-key-32-chars-or-more-here

# ============================================================
# PRODUCTION BITCOIN NETWORK
# ============================================================
BTC_NETWORK_PROD=mainnet
MEMPOOL_API_PROD=https://mempool.space/api
MEMPOOL_WS_PROD=wss://mempool.space/api/v1/ws
BLOCKSTREAM_API_PROD=https://blockstream.info/api

# ============================================================
# PRODUCTION API KEYS
# ============================================================
# CoinGecko Pro API (for BTC/USD price - MAINNET ONLY)
# Note: USD conversion is automatically disabled for testnet
COINGECKO_API_KEY_PROD=your-coingecko-pro-api-key-here
COINGECKO_API_URL=https://api.coingecko.com/api/v3

# ============================================================
# TEST ENVIRONMENT (Not used when ENV_CURRENT=true, but required)
# ============================================================
MONGODB_URL_TEST=mongodb://localhost:27017
MONGODB_DB_NAME_TEST=dice_test
TEST_MASTER_KEY=your-test-fernet-key-here
BTC_NETWORK_TEST=testnet
MEMPOOL_API_TEST=https://mempool.space/testnet/api
MEMPOOL_WS_TEST=wss://mempool.space/testnet/api/v1/ws
BLOCKSTREAM_API_TEST=https://blockstream.info/testnet/api
COINGECKO_API_KEY_TEST=

# ============================================================
# GAME SETTINGS
# ============================================================
HOUSE_EDGE=0.02
MIN_BET_SATOSHIS=600
MAX_BET_SATOSHIS=10000000
MIN_MULTIPLIER=1.1
MAX_MULTIPLIER=98.0
DEFAULT_WIN_CHANCE=50.0

# ============================================================
# TRANSACTION SETTINGS
# ============================================================
CONFIRMATIONS_REQUIRED=1
MIN_CONFIRMATIONS_PAYOUT=1
TX_DETECTION_TIMEOUT_MINUTES=60
DEFAULT_TX_FEE_SATOSHIS=500
FEE_BUFFER_SATOSHIS=2000
DUST_LIMIT_SATOSHIS=546

# ============================================================
# API TIMEOUTS
# ============================================================
API_REQUEST_TIMEOUT=15
BROADCAST_TIMEOUT=20

# ============================================================
# WEBSOCKET SETTINGS
# ============================================================
WS_PING_INTERVAL=30
WS_PING_TIMEOUT=20
WS_RECONNECT_DELAY=5
WS_MAX_RECONNECT_DELAY=60

# ============================================================
# SECURITY
# ============================================================
# Generate with: openssl rand -hex 32
SECRET_KEY=your-production-secret-key-64-chars-hex-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ============================================================
# RATE LIMITING
# ============================================================
MAX_REQUESTS_PER_MINUTE=120
MAX_BETS_PER_USER_PER_HOUR=200

# ============================================================
# LOGGING
# ============================================================
ENABLE_LOGGING=true
LOG_LEVEL=INFO
LOG_FILE=dice_game_prod.log

# ============================================================
# SERVER CONFIGURATION
# ============================================================
HOST=0.0.0.0
PORT=8000
RELOAD=false
DEBUG=false
FRONTEND_URL=https://yourdomain.com
```

---

## 🧪 **TEST ENVIRONMENT (.env)**

**Copy this to `backend/.env` for development/testing:**

```env
# ============================================================
# TEST ENVIRONMENT CONFIGURATION
# ============================================================
# ✅ Safe for development/testing on Bitcoin TESTNET
# ✅ No real money involved
# ============================================================

# ============================================================
# ENVIRONMENT TOGGLE
# ============================================================
# FALSE = Test (Testnet, fake money, test database)
ENV_CURRENT=false

# ============================================================
# TEST DATABASE
# ============================================================
MONGODB_URL_TEST=mongodb://localhost:27017
MONGODB_DB_NAME_TEST=dice_test

# ============================================================
# TEST ENCRYPTION KEY
# ============================================================
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# This is for test wallets only - safe to use a simple key for testing
TEST_MASTER_KEY=your-test-fernet-key-can-be-simple-for-testing

# ============================================================
# TEST BITCOIN NETWORK
# ============================================================
BTC_NETWORK_TEST=testnet
MEMPOOL_API_TEST=https://mempool.space/testnet/api
MEMPOOL_WS_TEST=wss://mempool.space/testnet/api/v1/ws
BLOCKSTREAM_API_TEST=https://blockstream.info/testnet/api

# ============================================================
# TEST API KEYS
# ============================================================
# CoinGecko Free API (NOT USED - testnet BTC has no USD value)
# USD conversion is automatically disabled for testnet
COINGECKO_API_KEY_TEST=
COINGECKO_API_URL=https://api.coingecko.com/api/v3

# ============================================================
# PRODUCTION ENVIRONMENT (Not used when ENV_CURRENT=false, but required)
# ============================================================
MONGODB_URL_PROD=mongodb://localhost:27017
MONGODB_DB_NAME_PROD=dice_prod
PROD_MASTER_KEY=not-used-in-test-mode
BTC_NETWORK_PROD=mainnet
MEMPOOL_API_PROD=https://mempool.space/api
MEMPOOL_WS_PROD=wss://mempool.space/api/v1/ws
BLOCKSTREAM_API_PROD=https://blockstream.info/api
COINGECKO_API_KEY_PROD=

# ============================================================
# LEGACY/SHARED CONFIGURATION
# ============================================================
# House wallet (optional, for backward compatibility)
HOUSE_PRIVATE_KEY=
HOUSE_ADDRESS=
HOUSE_MNEMONIC=

# ============================================================
# GAME SETTINGS (Relaxed for testing)
# ============================================================
HOUSE_EDGE=0.02
MIN_BET_SATOSHIS=100
MAX_BET_SATOSHIS=100000
MIN_MULTIPLIER=1.1
MAX_MULTIPLIER=98.0
DEFAULT_WIN_CHANCE=50.0

# ============================================================
# TRANSACTION SETTINGS (Fast for testing)
# ============================================================
CONFIRMATIONS_REQUIRED=0
MIN_CONFIRMATIONS_PAYOUT=0
TX_DETECTION_TIMEOUT_MINUTES=30
DEFAULT_TX_FEE_SATOSHIS=100
FEE_BUFFER_SATOSHIS=500
DUST_LIMIT_SATOSHIS=546

# ============================================================
# API TIMEOUTS
# ============================================================
API_REQUEST_TIMEOUT=10
BROADCAST_TIMEOUT=15

# ============================================================
# WEBSOCKET SETTINGS
# ============================================================
WS_PING_INTERVAL=30
WS_PING_TIMEOUT=20
WS_RECONNECT_DELAY=5
WS_MAX_RECONNECT_DELAY=60

# ============================================================
# SECURITY (Simple for testing)
# ============================================================
SECRET_KEY=test-secret-key-not-for-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ============================================================
# RATE LIMITING (Relaxed for testing)
# ============================================================
MAX_REQUESTS_PER_MINUTE=600
MAX_BETS_PER_USER_PER_HOUR=1000

# ============================================================
# LOGGING (Verbose for debugging)
# ============================================================
ENABLE_LOGGING=true
LOG_LEVEL=DEBUG
LOG_FILE=dice_game_test.log

# ============================================================
# SERVER CONFIGURATION (Dev mode)
# ============================================================
HOST=0.0.0.0
PORT=8000
RELOAD=true
DEBUG=true
FRONTEND_URL=http://localhost:3000
```

---

## 📊 **COMPARISON TABLE**

| Setting | Test | Production |
|---------|------|------------|
| **ENV_CURRENT** | `false` | `true` |
| **Database** | `dice_test` | `dice_prod` |
| **Network** | testnet | mainnet |
| **API** | `/testnet/api` | `/api` |
| **Min Bet** | 100 sats | 600 sats |
| **Max Bet** | 100,000 sats | 10,000,000 sats |
| **Confirmations** | 0 | 1 |
| **TX Fee** | 100 sats | 500 sats |
| **DEBUG** | `true` | `false` |
| **RELOAD** | `true` | `false` |
| **LOG_LEVEL** | `DEBUG` | `INFO` |
| **Frontend** | `http://localhost:3000` | `https://yourdomain.com` |

---

## 🚀 **QUICK SETUP**

### **For Testing:**
```bash
# 1. Generate test key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 2. Create .env file
nano backend/.env

# 3. Copy test config from above
# 4. Set TEST_MASTER_KEY to generated key
# 5. Set ENV_CURRENT=false

# 6. Start backend
cd backend
python -m uvicorn app.main:app

# Should see: 🧪 RUNNING IN TEST MODE 🧪
```

### **For Production:**
```bash
# 1. Generate production key (KEEP SECRET!)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 2. Generate secret key
openssl rand -hex 32

# 3. Create .env file
nano backend/.env

# 4. Copy production config from above
# 5. Set PROD_MASTER_KEY to generated key
# 6. Set SECRET_KEY to generated secret
# 7. Set ENV_CURRENT=true
# 8. Update FRONTEND_URL to your domain

# 9. Start backend
cd backend
python -m uvicorn app.main:app

# Should see: 🚨 RUNNING IN PRODUCTION MODE 🚨
# And: [VALIDATION] ✓ Bitcoin network verified as MAINNET
```

---

## ⚠️ **IMPORTANT NOTES**

### **For Production:**
- ✅ Use **strong** encryption keys (32+ characters)
- ✅ **Never** commit `.env` file to Git
- ✅ **Backup** PROD_MASTER_KEY securely (encrypted)
- ✅ Use **HTTPS** for frontend
- ✅ Set **DEBUG=false**
- ✅ Set **RELOAD=false**
- ✅ Monitor logs regularly
- ✅ Set up firewall rules
- ✅ Use production MongoDB with authentication

### **For Testing:**
- ✅ Get testnet BTC from faucets
- ✅ Use separate test database
- ✅ Confirmations = 0 for faster testing
- ✅ Debug mode for detailed logs
- ✅ Hot reload for development

---

## 🔐 **SECURITY CHECKLIST**

### **Before Going Live:**
- [ ] `ENV_CURRENT=true` set
- [ ] Strong `PROD_MASTER_KEY` (32+ chars)
- [ ] Strong `SECRET_KEY` (64 chars)
- [ ] Production database configured
- [ ] `DEBUG=false`
- [ ] `RELOAD=false`
- [ ] HTTPS enabled
- [ ] Network validation passes
- [ ] `.env` file in `.gitignore`
- [ ] Backup of encryption keys
- [ ] Monitoring configured

---

**See `ENVIRONMENT_SETUP_GUIDE.md` for complete setup instructions!**
