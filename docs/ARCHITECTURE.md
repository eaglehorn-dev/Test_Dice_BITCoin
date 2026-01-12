# Architecture Documentation

Complete technical architecture of the Bitcoin Dice Game.

## 🏗️ System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (React)                     │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │  Wallet  │   Dice   │ History  │  Verify  │   Stats  │  │
│  │ Connect  │   Game   │          │          │          │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS/REST API
┌──────────────────────┴──────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │   API    │ Provably │  Payout  │   Bet    │Transaction│
│  │ Routes   │   Fair   │  Engine  │Processor │ Detector  │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Database (SQLite/PostgreSQL)             │  │
│  │  Users | Bets | Seeds | Transactions | Payouts       │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│              Multi-Layer Transaction Detection              │
│  ┌──────────┬──────────┬──────────┬──────────────────────┐ │
│  │  Layer 1 │  Layer 2 │  Layer 3 │      Layer 4        │ │
│  │ Webhooks │ Polling  │ Fallback │  User-Submitted     │ │
│  └──────────┴──────────┴──────────┴──────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────────┐
│                   Bitcoin Testnet3 Network                   │
│  ┌──────────┬──────────┬──────────────┬─────────────────┐  │
│  │BlockCypher│Blockstream│ Mempool.space│  User Wallets  │  │
│  │    API    │    API    │     API      │                │  │
│  └──────────┴──────────┴──────────────┴─────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## 🎯 Core Components

### 1. Frontend (React)

**Location:** `/frontend`

**Purpose:** User interface for interacting with the dice game.

**Key Components:**

- **WalletConnect**: Handles wallet connection (Unisat-style)
  - Browser wallet detection
  - Manual address input fallback
  - User session management

- **DiceGame**: Main game interface
  - Multiplier/win chance selection
  - Deposit address generation
  - Transaction submission
  - Real-time result display

- **BetHistory**: User's bet history
  - Paginated list of bets
  - Filtering and sorting
  - Status tracking

- **FairnessVerifier**: Provably fair verification
  - Bet verification by ID
  - Cryptographic proof display
  - HMAC calculation breakdown

- **Stats**: Platform statistics
  - Total users, bets, wagered
  - Win rate and house edge
  - Real-time updates

- **RecentBets**: Live bet feed
  - Recent bets from all users
  - Auto-refresh every 15s
  - Win/lose indicators

**Technology Stack:**
- React 18
- CSS3 (no frameworks)
- Axios for API calls
- React Router for navigation

### 2. Backend (FastAPI)

**Location:** `/backend/app`

**Purpose:** API server and business logic.

**Architecture:**

```
app/
├── main.py              # FastAPI application, routes
├── config.py            # Configuration management
├── database.py          # SQLAlchemy models
├── provably_fair.py     # Dice logic and verification
├── blockchain.py        # Transaction detection
├── payout.py            # Payout processing
└── __init__.py
```

**Key Modules:**

#### main.py
- FastAPI app initialization
- REST API endpoints
- CORS configuration
- Background task management
- Webhook handler

**Endpoints:**
```
GET  /                          # Health check
GET  /api/stats                 # Platform statistics
POST /api/user/connect          # Connect user
POST /api/deposit/create        # Create deposit address
POST /api/tx/submit             # Submit transaction
GET  /api/bets/user/{address}   # User bet history
GET  /api/bet/{id}              # Get bet details
POST /api/bet/verify            # Verify bet fairness
GET  /api/bets/recent           # Recent bets
POST /api/webhook/tx            # BlockCypher webhook
GET  /api/admin/process-pending # Process pending bets
GET  /api/admin/retry-payouts   # Retry failed payouts
```

#### config.py
- Environment variable loading
- Configuration validation
- Type-safe config access
- Default values

#### database.py
- SQLAlchemy ORM models
- Database session management
- Table definitions:
  - **users**: User accounts
  - **seeds**: Server/client seeds
  - **bets**: Bet records
  - **transactions**: TX tracking
  - **payouts**: Payout records
  - **deposit_addresses**: Generated addresses

#### provably_fair.py
- HMAC-SHA512 dice roll calculation
- Seed generation and management
- Verification logic
- Win/lose determination
- Bet validation

**Dice Roll Algorithm:**
```python
# 1. Combine inputs
message = f"{client_seed}:{nonce}"

# 2. Calculate HMAC
hmac_result = hmac.new(
    server_seed.encode(),
    message.encode(),
    hashlib.sha512
).hexdigest()

# 3. Convert to roll (0.00-99.99)
hex_string = hmac_result[:8]
result_int = int(hex_string, 16)
roll = (result_int % 10000) / 100.0
```

#### blockchain.py
- Multi-layer transaction detection
- BlockCypher integration
- Fallback API support
- Webhook processing
- Polling mechanism
- Duplicate prevention

**Detection Layers:**
1. **Webhooks**: Instant notification from BlockCypher
2. **Polling**: 30-second interval checks
3. **Fallback**: Public APIs (Blockstream, Mempool.space)
4. **User-Submit**: Manual TXID verification

#### payout.py
- Automatic payout processing
- Bitcoin transaction creation
- Retry logic for failures
- Fee calculation
- Confirmation monitoring

### 3. Database Schema

```sql
-- Users
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    address VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP,
    last_seen TIMESTAMP,
    total_bets INTEGER DEFAULT 0,
    total_wagered INTEGER DEFAULT 0,
    total_won INTEGER DEFAULT 0,
    total_lost INTEGER DEFAULT 0
);

-- Seeds (Provably Fair)
CREATE TABLE seeds (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    server_seed VARCHAR(128) NOT NULL,
    server_seed_hash VARCHAR(128) NOT NULL,
    client_seed VARCHAR(128) NOT NULL,
    nonce INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    revealed_at TIMESTAMP NULL,
    created_at TIMESTAMP
);

-- Bets
CREATE TABLE bets (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    seed_id INTEGER REFERENCES seeds(id),
    bet_amount INTEGER NOT NULL,
    target_multiplier FLOAT NOT NULL,
    win_chance FLOAT NOT NULL,
    nonce INTEGER NOT NULL,
    roll_result FLOAT NULL,
    is_win BOOLEAN NULL,
    payout_amount INTEGER NULL,
    profit INTEGER NULL,
    deposit_txid VARCHAR(64),
    deposit_address VARCHAR(64),
    payout_txid VARCHAR(64),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP,
    confirmed_at TIMESTAMP NULL,
    rolled_at TIMESTAMP NULL,
    paid_at TIMESTAMP NULL
);

-- Transactions (Detection)
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    txid VARCHAR(64) UNIQUE NOT NULL,
    bet_id INTEGER REFERENCES bets(id),
    from_address VARCHAR(64),
    to_address VARCHAR(64) NOT NULL,
    amount INTEGER NOT NULL,
    fee INTEGER,
    detected_by VARCHAR(50) NOT NULL,
    detection_count INTEGER DEFAULT 1,
    confirmations INTEGER DEFAULT 0,
    block_height INTEGER NULL,
    block_hash VARCHAR(64) NULL,
    is_processed BOOLEAN DEFAULT FALSE,
    is_duplicate BOOLEAN DEFAULT FALSE,
    detected_at TIMESTAMP,
    confirmed_at TIMESTAMP NULL,
    processed_at TIMESTAMP NULL,
    raw_data TEXT
);

-- Payouts
CREATE TABLE payouts (
    id INTEGER PRIMARY KEY,
    bet_id INTEGER REFERENCES bets(id),
    amount INTEGER NOT NULL,
    to_address VARCHAR(64) NOT NULL,
    txid VARCHAR(64) UNIQUE,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT NULL,
    network_fee INTEGER NULL,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP,
    broadcast_at TIMESTAMP NULL,
    confirmed_at TIMESTAMP NULL
);

-- Deposit Addresses
CREATE TABLE deposit_addresses (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    address VARCHAR(64) UNIQUE NOT NULL,
    derivation_path VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    is_used BOOLEAN DEFAULT FALSE,
    expected_multiplier FLOAT NULL,
    expected_amount_min INTEGER NULL,
    expected_amount_max INTEGER NULL,
    created_at TIMESTAMP,
    used_at TIMESTAMP NULL,
    expires_at TIMESTAMP NULL
);
```

**Indexes:**
```sql
CREATE INDEX idx_user_active ON seeds(user_id, is_active);
CREATE INDEX idx_user_created ON bets(user_id, created_at);
CREATE INDEX idx_status ON bets(status);
CREATE INDEX idx_deposit_txid ON bets(deposit_txid);
CREATE INDEX idx_txid ON transactions(txid);
CREATE INDEX idx_to_address ON transactions(to_address);
CREATE INDEX idx_processed ON transactions(is_processed);
```

## 🔄 Data Flow

### Complete Bet Lifecycle

```
1. USER CONNECTS
   ├─> Frontend: WalletConnect component
   ├─> POST /api/user/connect
   ├─> Backend: Create/get User and Seed
   └─> Response: User data + server seed hash

2. CREATE BET
   ├─> Frontend: DiceGame - set multiplier
   ├─> POST /api/deposit/create
   ├─> Backend: Generate deposit address
   ├─> Backend: Setup webhook (Layer 1)
   └─> Response: Deposit address

3. SEND BITCOIN
   ├─> User sends BTC from wallet
   └─> Transaction broadcast to Bitcoin network

4. DETECT TRANSACTION (Multi-Layer)
   ├─> Layer 1: BlockCypher webhook (instant)
   │   └─> POST /api/webhook/tx
   ├─> Layer 2: Polling (30s interval)
   │   └─> TransactionMonitor background task
   ├─> Layer 3: Fallback APIs
   │   └─> Blockstream/Mempool.space APIs
   └─> Layer 4: User submit
       └─> POST /api/tx/submit

5. PROCESS TRANSACTION
   ├─> TransactionDetector processes TX
   ├─> Store in transactions table
   ├─> Check for duplicates
   ├─> Link to deposit address
   └─> Create Bet record

6. WAIT FOR CONFIRMATIONS
   ├─> Monitor confirmations
   ├─> Update transaction.confirmations
   └─> When confirmations >= MIN_CONFIRMATIONS_PAYOUT

7. ROLL DICE
   ├─> Get active seed for user
   ├─> Calculate HMAC-SHA512
   ├─> Determine roll result (0.00-99.99)
   ├─> Compare to win chance
   ├─> Update bet with result
   ├─> Increment seed nonce
   └─> Update user statistics

8. PAYOUT (if win)
   ├─> Create Payout record
   ├─> Calculate payout amount
   ├─> Determine recipient address
   ├─> Create Bitcoin transaction
   ├─> Broadcast to network
   ├─> Store payout txid
   └─> Update bet status to 'paid'

9. DISPLAY RESULT
   ├─> Frontend polls for result
   ├─> GET /api/bet/{id}
   ├─> Display dice animation
   ├─> Show win/lose
   └─> Show payout txid (if applicable)

10. VERIFICATION (anytime later)
    ├─> POST /api/bet/verify
    ├─> Reveal server seed
    ├─> Recalculate roll
    ├─> Verify hash matches
    └─> Return verification proof
```

## 🔐 Security Architecture

### 1. Seed Management

**Server Seed Security:**
- Generated with cryptographically secure random
- SHA256 hash shown to user BEFORE bet
- Hidden until after bet completion
- Revealed only after roll
- Proves house couldn't manipulate result

**Client Seed:**
- User's wallet address by default
- User can provide custom seed
- Combined with server seed via HMAC

**Nonce:**
- Increments for each bet
- Prevents result prediction
- Ensures uniqueness

### 2. Transaction Security

**Duplicate Prevention:**
- Unique constraint on txid
- detection_count tracks multiple detections
- is_processed flag prevents reprocessing
- is_duplicate flag marks duplicates

**Double-Payment Prevention:**
- Bet status state machine
- Payout linked to bet (one-to-one)
- Status checks before payout
- Transaction idempotency

**Status Flow:**
```
pending -> confirmed -> rolled -> paid
                              -> failed
```

### 3. API Security

**Rate Limiting:**
- 60 requests/minute global
- 100 bets/hour per user
- Nginx rate limiting

**Input Validation:**
- Pydantic models
- Type checking
- Range validation
- SQL injection protection (ORM)

**Authentication:**
- Address-based auth
- No passwords stored
- Message signing (future)

### 4. Private Key Security

**Storage:**
- Environment variables only
- Never in code
- File permissions: 600
- Access restricted to app user

**Usage:**
- Only for payouts
- Never exposed via API
- Logged but redacted

## ⚡ Performance Optimization

### 1. Database

**Indexes:**
- Primary keys on all tables
- Foreign key indexes
- Composite indexes for queries
- Index on frequently queried columns

**Query Optimization:**
- Limit result sets
- Pagination for large datasets
- Eager loading for relationships
- Connection pooling

### 2. Caching

**Frontend:**
- Static asset caching (1 year)
- Browser caching headers
- Build optimization

**Backend:**
- In-memory seed cache
- Address lookup cache
- Stats caching (30s)

### 3. Background Tasks

**Transaction Monitor:**
- Async polling
- Batch processing
- Configurable intervals
- Error recovery

**Payout Processor:**
- Retry logic
- Exponential backoff
- Max retry limits
- Failed payout tracking

## 🔍 Monitoring & Observability

### Logging

**Levels:**
- DEBUG: Detailed trace
- INFO: Key events
- WARNING: Potential issues
- ERROR: Failures

**Events Logged:**
- All API requests
- Transaction detections
- Bet creations and results
- Payout broadcasts
- Errors and exceptions

**Log Format:**
```
2024-01-12 10:30:45 - app.blockchain - INFO - ✅ New transaction detected: abc123... amount=10000 conf=0
```

### Metrics

**Key Metrics:**
- Total users
- Total bets
- Total wagered
- Win rate
- Average bet size
- Transaction detection rate by layer
- Payout success rate
- API response times

### Health Checks

**Endpoints:**
- `GET /` - Basic health
- `GET /api/stats` - Database health
- Background task status

**Monitoring:**
- Systemd service status
- Process monitoring
- Disk space
- Memory usage
- Network connectivity

## 🚀 Scalability Considerations

### Horizontal Scaling

**Frontend:**
- Stateless React app
- Can run multiple instances
- CDN distribution
- Load balancer ready

**Backend:**
- Stateless API design
- Database connection pooling
- Can run multiple workers
- Shared database

### Vertical Scaling

**Database:**
- SQLite for small scale (<1000 bets/day)
- PostgreSQL for production
- Read replicas for scaling
- Connection pooling

**API:**
- Uvicorn workers
- Async request handling
- Background task queue

### Bottlenecks

**BlockCypher API:**
- Rate limits: 200 req/hour (free)
- Solution: Fallback APIs
- Solution: Caching

**Payout Broadcasting:**
- Sequential processing
- Solution: Batch payouts
- Solution: Queue system

## 📊 Reliability & Fault Tolerance

### Transaction Detection Reliability

**Multi-Layer Approach:**
1. Primary: Webhooks (instant, but unreliable)
2. Backup: Polling (30s delay, reliable)
3. Fallback: Public APIs (slower, very reliable)
4. Final: User submission (manual, always works)

**Guarantees:**
- Eventually consistent
- No transaction permanently missed
- Duplicate detection and handling
- State recovery on restart

### Payout Reliability

**Retry Logic:**
- Max 3 retries per payout
- Exponential backoff
- Error logging
- Manual retry endpoint

**Failure Handling:**
- Failed payouts tracked
- Admin notification (logs)
- Manual intervention possible
- Retry endpoint available

### Data Integrity

**Database:**
- Foreign key constraints
- Unique constraints
- Not null constraints
- Transaction atomicity

**State Machine:**
- Well-defined states
- State transition validation
- Rollback on errors
- Audit trail via timestamps

## 🧪 Testing Strategy

**Unit Tests:**
- Provably fair logic
- Bet validation
- Roll calculation
- Verification

**Integration Tests:**
- API endpoints
- Database operations
- Transaction detection
- Payout processing

**End-to-End Tests:**
- Complete bet flow
- Multi-layer detection
- Payout delivery
- Verification

**Performance Tests:**
- Concurrent bets
- Database load
- API throughput
- Memory usage

## 📚 Design Patterns

**Patterns Used:**

1. **Repository Pattern**
   - Database access abstraction
   - SessionLocal dependency injection

2. **Factory Pattern**
   - Seed generation
   - Address generation

3. **Strategy Pattern**
   - Multi-layer transaction detection
   - Different detection strategies

4. **State Pattern**
   - Bet status lifecycle
   - Payout status transitions

5. **Observer Pattern**
   - Transaction monitoring
   - Real-time updates

## 🔮 Future Enhancements

**Possible Improvements:**

1. **HD Wallet Integration**
   - Unique address per bet
   - Better privacy
   - Automated address generation

2. **WebSocket Support**
   - Real-time bet updates
   - Live transaction notifications
   - Instant result delivery

3. **Advanced Analytics**
   - User statistics dashboard
   - Platform analytics
   - Win/loss tracking

4. **Multiple Games**
   - Different dice variants
   - Other provably fair games
   - Game selection

5. **Enhanced Security**
   - 2FA for withdrawals
   - Message signing for auth
   - Hardware wallet support

6. **Performance**
   - Redis caching
   - Message queue (RabbitMQ)
   - Database sharding

---

**Architecture Version:** 1.0.0
**Last Updated:** 2024-01-12
