# Bitcoin Provably Fair Dice Game

A production-grade Satoshi-style dice game with provably fair mechanics, multi-layer transaction detection, and robust BlockCypher integration.

## 🎯 Features

- **Provably Fair**: HMAC-SHA512 based dice rolls with seed reveal system
- **Multi-Layer TX Detection**: Handles BlockCypher testnet3 reliability issues
- **Unisat Wallet Integration**: One-click betting with automatic Bitcoin sending
- **Auto-Send Betting**: Automatic transaction submission when Unisat is installed
- **Real-time Monitoring**: Multiple fallback layers for transaction detection
- **Casino UI**: Clean, responsive interface with animations
- **Security**: No double-payments, proper key management, hostile environment ready

## 🏗️ Architecture

### Backend (Python/FastAPI)
- FastAPI REST API
- SQLite database (upgradeable to PostgreSQL)
- BlockCypher Python SDK
- Multi-threaded transaction monitoring
- Automated payout system

### Frontend (React)
- React 18 with hooks
- Wallet connection flow
- Real-time bet tracking
- Fairness verification page
- Responsive casino-style UI

### Transaction Detection Layers

1. **Primary**: BlockCypher Webhooks
2. **Backup**: BlockCypher API Polling (30s intervals)
3. **Fallback**: Public mempool explorer APIs
4. **Final**: User-submitted TXID verification

## 📁 Project Structure

```
Dice2/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── database.py          # DB models
│   │   ├── provably_fair.py     # Dice logic
│   │   ├── blockchain.py        # Multi-layer TX detection
│   │   ├── payout.py            # Payout engine
│   │   └── config.py            # Configuration
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── utils/
│   │   └── App.js
│   ├── package.json
│   └── README.md
├── docs/
│   ├── DEPLOYMENT.md
│   ├── TESTING.md
│   └── ARCHITECTURE.md
└── README.md
```

## 🚀 Quick Start

### 🪟 Windows Users (Easiest!)

1. Double-click `setup-all.bat` (first time only)
2. Edit `backend\.env` with your credentials
3. Double-click `start-all.bat`
4. Done! Visit http://localhost:3000

See [WINDOWS_GUIDE.md](WINDOWS_GUIDE.md) for details.

### 🐧 Linux/Mac Users

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example.txt .env
# Edit .env with your BlockCypher API token
python -c "from app.database import init_db; init_db()"
python -m app.main
```

#### Frontend Setup

```bash
cd frontend
npm install
npm start
```

## 🔧 Configuration

Create `backend/.env`:

```env
BLOCKCYPHER_API_TOKEN=your_token_here
HOUSE_PRIVATE_KEY=your_testnet_private_key
DATABASE_URL=sqlite:///./dice_game.db
HOUSE_EDGE=0.02
MIN_BET_SATOSHIS=10000
MAX_BET_SATOSHIS=1000000
CONFIRMATIONS_REQUIRED=1
```

## 🎲 How It Works

1. **Player connects wallet** (Unisat-style)
2. **System generates unique deposit address** (HD derivation)
3. **Player sends BTC** with chosen multiplier
4. **Multi-layer detection** catches transaction
5. **Provably fair roll** calculated using:
   - Server seed (hidden)
   - Client seed (from player address/tx)
   - Nonce (bet counter)
6. **Automatic payout** if player wins
7. **Seed reveal** after bet completion

## 👛 Unisat Wallet Integration

The game supports **automatic betting** with Unisat wallet browser extension!

### With Unisat Installed (Recommended)

1. Install [Unisat Wallet](https://unisat.io) browser extension
2. Switch to Bitcoin Testnet
3. Connect wallet to the game
4. Click **"Bet & Send with Unisat"**
5. Approve transaction in wallet popup
6. **Done!** Transaction is sent and bet processes automatically

### Without Unisat (Manual Mode)

1. Click "Create Bet" to generate deposit address
2. Send Bitcoin manually from any wallet
3. Copy your transaction ID
4. Paste and submit the TXID
5. Wait for dice roll

### Features

- ✅ **One-Click Betting**: No manual address copying
- ✅ **Auto-Submit**: Transaction ID captured automatically
- ✅ **Network Detection**: Automatically switches to testnet
- ✅ **Error Handling**: Falls back to manual mode if needed
- ✅ **Security**: You approve every transaction in wallet

See [UNISAT_WALLET_GUIDE.md](UNISAT_WALLET_GUIDE.md) for detailed instructions.

## 🔐 Security Features

- Private keys in environment variables only
- No hardcoded secrets
- Transaction deduplication
- Double-payment protection
- State machine for bet lifecycle
- Input validation and sanitization
- Rate limiting
- SQL injection protection (ORM)

## 📊 Database Schema

- **users**: User accounts and wallet addresses
- **seeds**: Server/client seeds with reveal status
- **bets**: Complete bet history
- **transactions**: TX detection and state tracking
- **payouts**: Payout records

## 🧪 Testing

See [TESTING.md](docs/TESTING.md) for comprehensive testing guide.

## 📦 Deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for production deployment guide.

## 🏛️ License

MIT License - See LICENSE file

## ⚠️ Disclaimer

This is testnet-only software for educational purposes. Gambling may be illegal in your jurisdiction. Use at your own risk.
