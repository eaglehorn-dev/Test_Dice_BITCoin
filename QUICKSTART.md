# Quick Start Guide

Get the Bitcoin Dice Game running in 10 minutes.

## 🪟 Windows Users

**Super Quick Start:**

1. Double-click `setup-all.bat`
2. Edit `backend\.env` with your credentials
3. Double-click `start-all.bat`
4. Done! Visit http://localhost:3000

See [WINDOWS_GUIDE.md](WINDOWS_GUIDE.md) for complete Windows instructions.

---

## 🚀 Prerequisites

- Python 3.9+ installed
- Node.js 16+ installed
- Bitcoin testnet address
- BlockCypher API token (free at https://accounts.blockcypher.com/)

## ⚡ Quick Setup

### 1. Clone and Setup Backend (5 minutes)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp env.example.txt .env

# Edit .env with your credentials (use any text editor)
# Minimum required:
# - BLOCKCYPHER_API_TOKEN=your_token_here
# - HOUSE_PRIVATE_KEY=your_testnet_private_key
# - HOUSE_ADDRESS=your_testnet_address

# Initialize database
python -c "from app.database import init_db; init_db()"

# Start backend
python -m app.main
```

You should see:
```
✅ Configuration validated
✅ Database initialized
✅ Transaction monitor started
INFO: Uvicorn running on http://0.0.0.0:8000
```

### 2. Setup Frontend (5 minutes)

Open a new terminal:

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Browser opens at `http://localhost:3000`

## 🎮 First Bet

### 1. Get Testnet Bitcoin

Visit a testnet faucet:
- https://testnet-faucet.mempool.co/
- https://coinfaucet.eu/en/btc-testnet/

Request testnet BTC to your address.

### 2. Connect Wallet

1. Click "Connect Wallet" in the app
2. Choose "Enter Address"
3. Paste your testnet address
4. Click "Connect"

### 3. Place a Bet

**Option A: With Unisat Wallet (Easiest - One Click!)**

1. Install [Unisat Wallet](https://unisat.io) extension
2. Switch Unisat to Testnet
3. Get testnet BTC from faucet to your Unisat address
4. Click "Play" tab in game
5. Set multiplier (e.g., 2.0x)
6. Click **"Bet & Send with Unisat"**
7. Approve transaction in Unisat popup
8. Done! Wait for result automatically

**Option B: Manual Method (No Wallet Extension)**

1. Click "Play" tab
2. Set multiplier (e.g., 2.0x)
3. Click "Create Bet"
4. Copy the deposit address shown
5. Send testnet BTC to that address (e.g., 0.0001 BTC = 10000 sats)
6. Paste your transaction ID
7. Click "Submit"
8. Wait for result (may take 1-2 minutes)

**Recommended:** Use Option A with Unisat for fastest, easiest betting!

See [UNISAT_WALLET_GUIDE.md](UNISAT_WALLET_GUIDE.md) for detailed Unisat setup.

## 🎲 What Happens Next

The system will:
1. ✅ Detect your transaction (multiple detection layers)
2. ✅ Wait for confirmation
3. ✅ Roll the dice using provably fair HMAC-SHA512
4. ✅ Display the result
5. ✅ Send payout if you win (automatic)

## 🔍 Verify Fairness

1. Click "Verify" tab
2. Enter your bet ID (shown in result)
3. Click "Verify"
4. See complete cryptographic proof

## 📊 View Stats

1. Click "Stats" tab
2. See platform statistics
3. View recent bets from all players

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check .env file exists
ls -la backend/.env

# Check Python version
python --version  # Should be 3.9+

# Try manual database init
cd backend
python -c "from app.database import init_db; init_db()"
```

### Transaction not detected
```bash
# Check BlockCypher API token in .env
# Wait 30 seconds for polling
# Or manually submit transaction ID in frontend
```

### Payout not received
```bash
# Check house wallet has funds
# Check logs: backend console
# Wait for confirmations (testnet can be slow)
```

## 📚 Next Steps

- Read [TESTING.md](docs/TESTING.md) for comprehensive testing
- Read [DEPLOYMENT.md](docs/DEPLOYMENT.md) for production deployment
- Read [ARCHITECTURE.md](docs/ARCHITECTURE.md) for system details

## 🎯 Key Features to Try

1. **Multiple Bets**: Place several bets to see history
2. **Different Multipliers**: Try 1.5x, 5x, 10x
3. **Verification**: Verify any bet's fairness
4. **Bet History**: Check your complete history
5. **Recent Feed**: Watch other bets in real-time

## ⚠️ Important Notes

- **Testnet Only**: Never use mainnet keys
- **Educational**: For learning purposes only
- **Free Testnet BTC**: Use faucets, don't buy
- **Keep Keys Safe**: Never commit .env to git

## 🎉 You're Ready!

The complete provably fair Bitcoin dice game is now running locally. Have fun testing!

## 🆘 Need Help?

Check the logs:
- Backend: Terminal where you ran `python -m app.main`
- Frontend: Browser console (F12)
- Network: Browser DevTools Network tab

Review documentation:
- README.md - Overview
- docs/TESTING.md - Comprehensive testing guide
- docs/DEPLOYMENT.md - Production deployment
- docs/ARCHITECTURE.md - Technical details

---

**Quick Reference:**

- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs (auto-generated)
- Health Check: http://localhost:8000/

**Default Settings:**
- House Edge: 2%
- Min Bet: 10,000 sats
- Max Bet: 1,000,000 sats
- Min Multiplier: 1.1x
- Max Multiplier: 98x
