# Testing Guide

Comprehensive testing guide for Bitcoin Dice Game on Testnet3.

## 🎯 Overview

This guide covers:
- Local development testing
- Testnet3 setup and funding
- Component testing
- Integration testing
- Multi-layer transaction detection testing
- Provably fair verification
- Performance testing

## 🔧 Prerequisites

### 1. Get Testnet Bitcoin

#### Option A: Testnet Faucets

```bash
# Visit these faucets to get testnet BTC:
# https://testnet-faucet.mempool.co/
# https://coinfaucet.eu/en/btc-testnet/
# https://testnet.help/en/btcfaucet/testnet
```

#### Option B: Bitcoin Core Testnet

```bash
# Install Bitcoin Core
# Download from: https://bitcoin.org/en/download

# Run in testnet mode
bitcoin-cli -testnet getbalance

# Generate testnet address
bitcoin-cli -testnet getnewaddress

# Get private key
bitcoin-cli -testnet dumpprivkey <address>
```

### 2. BlockCypher API Token

```bash
# Sign up at: https://accounts.blockcypher.com/
# Get your API token
# Free tier: 200 requests/hour
```

### 3. Setup Local Environment

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install pytest pytest-asyncio

# Create .env from template
cp env.example.txt .env
# Edit .env with your actual credentials

# Initialize database
python -c "from app.database import init_db; init_db()"

# Frontend
cd ../frontend
npm install
```

## 🧪 Backend Testing

### 1. Test Provably Fair Logic

```bash
cd backend
source venv/bin/activate

# Test dice roll calculation
python -c "
from app.provably_fair import ProvablyFair, roll_dice

# Generate seeds
server_seed = ProvablyFair.generate_server_seed()
client_seed = 'test_client_seed'
nonce = 0

# Roll dice
result = roll_dice(server_seed, client_seed, nonce, 10000, 2.0)
print(f'Roll: {result[\"roll\"]}')
print(f'Win: {result[\"is_win\"]}')
print(f'Payout: {result[\"payout\"]}')

# Verify
is_valid = ProvablyFair.verify_roll(
    server_seed, client_seed, nonce, result['roll']
)
print(f'Verification: {is_valid}')
"

# Run built-in test
python -m app.provably_fair
```

### 2. Test Database Operations

```bash
# Test database creation
python -c "
from app.database import SessionLocal, init_db, User, Seed
from app.provably_fair import generate_new_seed_pair

# Initialize
init_db()

# Create test user
db = SessionLocal()
user = User(address='test_address_12345')
db.add(user)
db.commit()

# Create seed
server_seed, server_seed_hash, client_seed = generate_new_seed_pair()
seed = Seed(
    user_id=user.id,
    server_seed=server_seed,
    server_seed_hash=server_seed_hash,
    client_seed=client_seed
)
db.add(seed)
db.commit()

print(f'User ID: {user.id}')
print(f'Seed ID: {seed.id}')
db.close()
"
```

### 3. Test BlockCypher Integration

```bash
python -c "
from blockcypher import get_address_details
import os

# Test API connection
address = 'n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi'  # Test address
try:
    details = get_address_details(
        address,
        coin_symbol='btc-testnet',
        api_key=os.getenv('BLOCKCYPHER_API_TOKEN')
    )
    print(f'Balance: {details.get(\"balance\", 0)} satoshis')
    print(f'Total TX: {details.get(\"n_tx\", 0)}')
    print('✅ BlockCypher API working')
except Exception as e:
    print(f'❌ BlockCypher error: {e}')
"
```

### 4. Start Backend Server

```bash
# Terminal 1: Start API
cd backend
source venv/bin/activate
python -m app.main

# Should see:
# ✅ Configuration validated
# ✅ Database initialized
# ✅ Transaction monitor started
# INFO: Uvicorn running on http://0.0.0.0:8000
```

### 5. Test API Endpoints

```bash
# Terminal 2: Test endpoints

# Health check
curl http://localhost:8000/

# Get stats
curl http://localhost:8000/api/stats

# Connect user
curl -X POST "http://localhost:8000/api/user/connect?user_address=n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi"

# Create deposit address
curl -X POST http://localhost:8000/api/deposit/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_address": "n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi",
    "multiplier": 2.0
  }'

# Get recent bets
curl http://localhost:8000/api/bets/recent
```

## 🎨 Frontend Testing

### 1. Start Frontend

```bash
# Terminal 3: Start frontend
cd frontend
npm start

# Opens browser at http://localhost:3000
```

### 2. Manual UI Testing

#### Test Wallet Connection

1. Click "Connect Wallet"
2. Enter a testnet address or click "Enter Address"
3. Input: `n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi` (or your address)
4. Click "Connect"
5. ✅ Verify: Shows connected address

#### Test Dice Game

1. Navigate to "Play" tab
2. Adjust multiplier slider (try 2.0x)
3. Check win chance updates correctly
4. Set bet amount (e.g., 10000 sats)
5. Click "Create Bet"
6. ✅ Verify: Deposit address displayed
7. Copy deposit address

#### Test Bet History

1. Navigate to "History" tab
2. ✅ Verify: Shows "No bets yet" or previous bets
3. Check refresh button works

#### Test Fairness Verifier

1. Navigate to "Verify" tab
2. Enter a bet ID (if you have one)
3. Click "Verify"
4. ✅ Verify: Shows verification data

#### Test Stats Page

1. Navigate to "Stats" tab
2. ✅ Verify: Shows platform statistics
3. ✅ Verify: Recent bets displayed (if any)

## 🔄 Integration Testing

### Full End-to-End Bet Flow

#### 1. Setup

```bash
# Ensure both backend and frontend are running
# Have testnet BTC ready
# Have a testnet wallet (Electrum, Bitcoin Core, etc.)
```

#### 2. Create Bet

1. Connect wallet in frontend
2. Set multiplier to 2.0x
3. Click "Create Bet"
4. Copy the deposit address shown
5. Note the expected amount (e.g., 10000 sats)

#### 3. Send Transaction

Using Bitcoin Core:
```bash
bitcoin-cli -testnet sendtoaddress <deposit_address> 0.0001
# Returns txid
```

Using Electrum:
- Send 0.0001 BTC to deposit address
- Copy transaction ID

#### 4. Submit Transaction

1. Paste txid in frontend
2. Click "Submit"
3. Wait for processing (watch backend logs)

#### 5. Verify Processing

Backend logs should show:
```
✅ New transaction detected: <txid>
✅ Created bet <bet_id>
🎲 Bet <bet_id> rolled: <roll> (WIN/LOSE)
✅ Payout <payout_id> broadcast: <payout_txid> (if win)
```

Frontend should show:
- Processing spinner
- Then bet result with dice animation
- Win/lose message
- Payout details

#### 6. Verify Payout (if win)

```bash
# Check payout transaction on explorer
# https://blockstream.info/testnet/tx/<payout_txid>
```

## 🧪 Multi-Layer Transaction Detection Testing

### Test Layer 1: Webhook

```bash
# This tests automatic detection via BlockCypher webhook

# 1. Ensure WEBHOOK_CALLBACK_URL is configured
# 2. Create bet and get deposit address
# 3. Send transaction
# 4. Backend should detect within seconds via webhook
# 5. Check logs for: "📥 Webhook received"
```

### Test Layer 2: Polling

```bash
# This tests backup polling detection

# 1. Create bet
# 2. Send transaction
# 3. Wait 30 seconds (POLLING_INTERVAL_SECONDS)
# 4. Check logs for: "📥 Polling found X new tx(s)"
```

### Test Layer 3: Fallback APIs

```bash
# This tests public API fallback

# 1. Temporarily set invalid BlockCypher token
# 2. Create bet and send transaction
# 3. System should fall back to Blockstream/Mempool APIs
# 4. Check logs for: "📥 Fallback APIs found X new tx(s)"
```

### Test Layer 4: User-Submitted TXID

```bash
# This tests manual submission

# 1. Create bet
# 2. Send transaction
# 3. Don't wait for auto-detection
# 4. Manually submit txid via frontend
# 5. Should process immediately
# 6. Check logs for: "✅ User-submitted transaction"
```

### Test Duplicate Prevention

```bash
# Ensure system doesn't process same transaction twice

# 1. Create bet
# 2. Send transaction
# 3. Submit same txid multiple times
# 4. Check database: should only have ONE transaction record
# 5. Verify: is_duplicate flag or detection_count increments
```

## 🔐 Security Testing

### Test Bet Validation

```python
# Test invalid bets are rejected
python -c "
from app.provably_fair import ProvablyFair

# Test bet amount validation
valid, error = ProvablyFair.validate_bet_params(5000, 2.0)  # Too low
print(f'Low bet: {error}')

valid, error = ProvablyFair.validate_bet_params(2000000, 2.0)  # Too high
print(f'High bet: {error}')

valid, error = ProvablyFair.validate_bet_params(10000, 0.5)  # Invalid multiplier
print(f'Invalid multiplier: {error}')

valid, error = ProvablyFair.validate_bet_params(10000, 2.0)  # Valid
print(f'Valid bet: {valid}')
"
```

### Test Seed Security

```python
# Verify server seed is hidden until after bet
python -c "
from app.database import SessionLocal, Seed

db = SessionLocal()
seeds = db.query(Seed).all()

for seed in seeds:
    if seed.is_active:
        assert seed.revealed_at is None, 'Active seed should not be revealed!'
    print(f'Seed {seed.id}: active={seed.is_active}, revealed={seed.revealed_at is not None}')
"
```

### Test Double-Payment Prevention

```bash
# Verify system won't pay twice for same bet

# 1. Manually check database after win
# 2. Bet should have status='paid'
# 3. Payout should exist with status='broadcast' or 'confirmed'
# 4. Triggering payout again should be rejected
```

## 📊 Performance Testing

### Concurrent Bets

```bash
# Test multiple simultaneous bets

# Create 5 bets quickly
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/deposit/create \
    -H "Content-Type: application/json" \
    -d "{\"user_address\": \"test$i\", \"multiplier\": 2.0}" &
done

# All should succeed without errors
```

### Database Load

```python
# Test with many bets
python -c "
from app.database import SessionLocal, Bet, User, Seed
from datetime import datetime
import random

db = SessionLocal()

# Create test user
user = db.query(User).first()
if not user:
    user = User(address='load_test_user')
    db.add(user)
    db.commit()

# Create test seed
seed = db.query(Seed).filter(Seed.user_id == user.id).first()

# Create 1000 test bets
for i in range(1000):
    bet = Bet(
        user_id=user.id,
        seed_id=seed.id,
        bet_amount=10000,
        target_multiplier=2.0,
        win_chance=49.0,
        nonce=i,
        roll_result=random.uniform(0, 100),
        is_win=random.choice([True, False]),
        status='paid',
        created_at=datetime.utcnow()
    )
    db.add(bet)
    
    if i % 100 == 0:
        db.commit()
        print(f'Created {i} bets')

db.commit()
print('✅ Created 1000 test bets')
"

# Test query performance
python -c "
from app.database import SessionLocal, Bet
import time

db = SessionLocal()

start = time.time()
bets = db.query(Bet).limit(50).all()
elapsed = time.time() - start

print(f'Query took {elapsed:.3f}s for {len(bets)} bets')
"
```

## 🐛 Debugging Guide

### Enable Debug Logging

```bash
# Edit .env
LOG_LEVEL=DEBUG

# Restart backend
sudo systemctl restart dice-api

# View debug logs
sudo journalctl -u dice-api -f
```

### Common Issues

#### Transaction Not Detected

```bash
# Check BlockCypher API status
curl https://api.blockcypher.com/v1/btc/test3

# Check transaction on explorer
# https://blockstream.info/testnet/tx/<txid>

# Manually trigger processing
curl -X POST http://localhost:8000/api/tx/submit \
  -H "Content-Type: application/json" \
  -d '{"txid": "<your_txid>", "deposit_address": "<deposit_addr>"}'
```

#### Payout Fails

```bash
# Check house wallet balance
python -c "
from blockcypher import get_address_details
import os

details = get_address_details(
    os.getenv('HOUSE_ADDRESS'),
    coin_symbol='btc-testnet',
    api_key=os.getenv('BLOCKCYPHER_API_TOKEN')
)
print(f'House balance: {details[\"balance\"]} satoshis')
"

# Check payout errors in database
python -c "
from app.database import SessionLocal, Payout

db = SessionLocal()
failed = db.query(Payout).filter(Payout.status == 'failed').all()

for p in failed:
    print(f'Payout {p.id}: {p.error_message}')
"
```

#### Database Corruption

```bash
# Backup current database
cp dice_game.db dice_game.db.backup

# Recreate database
python -c "from app.database import drop_all, init_db; drop_all(); init_db()"
```

## ✅ Test Checklist

### Pre-Deployment

- [ ] All backend tests pass
- [ ] Frontend loads without errors
- [ ] API endpoints respond correctly
- [ ] Wallet connection works
- [ ] Deposit address generation works
- [ ] Transaction detection works (all 4 layers)
- [ ] Bet processing works
- [ ] Dice roll calculation is correct
- [ ] Payouts are sent successfully
- [ ] Verification page validates correctly
- [ ] No duplicate transactions processed
- [ ] No double payments
- [ ] Rate limiting works
- [ ] Error handling works
- [ ] Logs are comprehensive
- [ ] Database queries are efficient

### Post-Deployment

- [ ] SSL certificate valid
- [ ] Frontend loads over HTTPS
- [ ] API accessible via reverse proxy
- [ ] Webhooks receive notifications
- [ ] Background polling works
- [ ] Database backups configured
- [ ] Log rotation works
- [ ] Monitoring alerts configured
- [ ] Performance acceptable under load
- [ ] Security headers present

## 📝 Test Reports

Keep track of your testing:

```bash
# Create test log
cat > test_log.md << EOF
# Test Session: $(date)

## Environment
- Backend: Running
- Frontend: Running
- Network: Testnet3
- BlockCypher: Connected

## Tests Performed
1. [ ] Provably fair logic
2. [ ] Database operations
3. [ ] API endpoints
4. [ ] Wallet connection
5. [ ] Full bet flow
6. [ ] Transaction detection (all layers)
7. [ ] Payout processing
8. [ ] Verification

## Results
- Tests Passed: X/Y
- Issues Found: 
- Notes:

## Sample Transactions
- Test TX 1: <txid>
- Test TX 2: <txid>
EOF
```

## 🎓 Learning Resources

- [Bitcoin Testnet Faucets](https://en.bitcoin.it/wiki/Testnet)
- [BlockCypher API Docs](https://www.blockcypher.com/dev/bitcoin/)
- [Provably Fair Gaming](https://en.wikipedia.org/wiki/Provably_fair_algorithm)
- [HMAC-SHA512](https://en.wikipedia.org/wiki/HMAC)

---

**Happy Testing! 🎲**

Remember: Test thoroughly on testnet before considering any mainnet deployment. This is educational software only.
