# Transaction Detection Flow Analysis - Main Backend

## 📊 **Complete Transaction Detection System**

---

## 🔄 **High-Level Overview**

```
1. Startup → Monitor Service loads all vault wallets
2. WebSocket → Connects to Mempool.space
3. Subscription → Tracks all vault wallet addresses
4. Detection → Receives real-time transaction notifications
5. Verification → Fetches full transaction details
6. Processing → Creates bet and calculates result
7. Payout → Sends winnings if user wins
8. Broadcast → Notifies frontend via WebSocket
```

---

## 🚀 **Step 1: System Initialization (On Startup)**

### **File:** `backend/app/services/transaction_monitor_service.py`

```python
async def start(self):
    # 1.1: Get all active vault wallets from database
    active_wallets = await self.wallet_service.get_active_wallets()
    
    # 1.2: Subscribe to each wallet address
    for wallet in active_wallets:
        address = wallet["address"]
        multiplier = wallet["multiplier"]
        await self.websocket_client.subscribe_address(address)
        self.monitored_addresses.add(address)
        logger.info(f"[MONITOR] 📍 Monitoring {multiplier}x wallet: {address[:20]}...")
    
    # 1.3: Start WebSocket client in background
    self.monitor_task = asyncio.create_task(self.websocket_client.start())
```

**What Happens:**
- ✅ Connects to MongoDB `dice_test` database
- ✅ Fetches all wallets where `is_active=True` and `network="testnet"`
- ✅ Creates a subscription list with all 7 vault wallet addresses
- ✅ Starts WebSocket connection to Mempool.space

**Your Current Monitored Addresses:**
```
[MONITOR] 📍 Monitoring 2x wallet: mrHLHe4vgspzEeECWNdi...
[MONITOR] 📍 Monitoring 3x wallet: mhFc5TRW1uB5fUUia3qn...
[MONITOR] 📍 Monitoring 4x wallet: mhqvLh1eRpc53t1RB6RN...
[MONITOR] 📍 Monitoring 5x wallet: mnKrcHoyV8Q7zqYtenQQ...
[MONITOR] 📍 Monitoring 95x wallet: moDMNVHPibT27Ziqg4hz...
[MONITOR] 📍 Monitoring 99x wallet: mx4z3WYdGiT2MQmE8SjJ...
[MONITOR] 📍 Monitoring 100x wallet: mo1vF8P1YyZXyYHva1zC...
[MONITOR] ✅ Monitoring 7 vault wallet(s)
```

---

## 🌐 **Step 2: WebSocket Connection**

### **File:** `backend/app/utils/mempool_websocket.py`

```python
async def connect(self) -> bool:
    # 2.1: Connect to Mempool.space WebSocket
    self.websocket = await websockets.connect(
        config.MEMPOOL_WEBSOCKET_URL,  # wss://mempool.space/testnet/api/v1/ws
        ping_interval=config.WS_PING_INTERVAL,  # 30 seconds
        ping_timeout=config.WS_PING_TIMEOUT      # 20 seconds
    )
    
    logger.info("[WEBSOCKET] ✅ Connected successfully")
    return True
```

**Connection Details:**
- **URL:** `wss://mempool.space/testnet/api/v1/ws`
- **Protocol:** WebSocket (bidirectional, persistent)
- **Ping:** Every 30 seconds to keep connection alive
- **Auto-Reconnect:** If connection drops, reconnects automatically with exponential backoff

---

## 📡 **Step 3: Address Subscription**

### **File:** `backend/app/utils/mempool_websocket.py`

```python
async def subscribe_address(self, address: str):
    # 3.1: Send track-address message to Mempool.space
    track_msg = {"track-address": address}
    await self.websocket.send(json.dumps(track_msg))
    
    # 3.2: Add to subscribed set
    self.subscribed_addresses.add(address)
    
    logger.info(f"[WEBSOCKET] 📍 Tracking address: {address[:20]}...")
```

**WebSocket Message Sent:**
```json
{"track-address": "mrHLHe4vgspzEeECWNdiRmEFwVgHzfhNE7"}
{"track-address": "mhFc5TRW1uB5fUUia3qnscvavhuHaaQFiH"}
{"track-address": "mhqvLh1eRpc53t1RB6RNP9f7BxwXnFN34z"}
... (for each vault wallet)
```

**Result:**
- Mempool.space server now monitors these addresses
- When ANY transaction involves these addresses, server pushes notification

---

## 🔔 **Step 4: Real-Time Transaction Detection**

### **File:** `backend/app/utils/mempool_websocket.py`

```python
async def handle_message(self, message: str):
    data = json.loads(message)
    
    # 4.1: Check for address-transactions messages
    if "address-transactions" in data:
        address_txs = data["address-transactions"]
        
        # 4.2: Handle both list and dict formats
        if isinstance(address_txs, list):
            for tx in address_txs:
                if isinstance(tx, dict):
                    txid = tx.get('txid')
                    if txid:
                        await self._process_transaction(txid)
        elif isinstance(address_txs, dict):
            txid = address_txs.get('txid')
            if txid:
                await self._process_transaction(txid)
```

**WebSocket Message Received (Example):**
```json
{
  "address-transactions": {
    "txid": "abc123...",
    "address": "mrHLHe4vgspzEeECWNdiRmEFwVgHzfhNE7"
  }
}
```

**Trigger:**
- Someone sends Bitcoin to ANY of your 7 monitored addresses
- Mempool.space instantly pushes notification via WebSocket
- Backend receives `address-transactions` message with `txid`

---

## 🔍 **Step 5: Transaction Verification**

### **File:** `backend/app/utils/mempool_websocket.py` → `backend/app/services/transaction_service.py`

```python
async def _process_transaction(self, txid: str):
    logger.info(f"[WEBSOCKET] 🔔 New transaction detected: {txid[:16]}...")
    
    # 5.1: Fetch full transaction details from Mempool.space REST API
    tx_service = TransactionService()
    tx_details = await tx_service.get_transaction_details(txid)
    
    # 5.2: Check and process transaction
    await self._check_and_process_tx_from_data(txid, tx_details)
```

**REST API Call:**
```
GET https://mempool.space/testnet/api/tx/{txid}
```

**Response (Simplified):**
```json
{
  "txid": "abc123...",
  "vin": [...],  // Inputs (where BTC came from)
  "vout": [      // Outputs (where BTC is going)
    {
      "scriptpubkey_address": "mrHLHe4vgspzEeECWNdiRmEFwVgHzfhNE7",
      "value": 100000  // 100,000 satoshis
    }
  ],
  "status": {
    "confirmed": false,
    "block_height": null
  }
}
```

---

## 🎯 **Step 6: Target Address Matching**

### **File:** `backend/app/utils/mempool_websocket.py`

```python
async def _check_and_process_tx_from_data(self, txid: str, tx_data: dict):
    # 6.1: Get transaction outputs
    vout = tx_data.get('vout', [])
    
    # 6.2: Check if transaction pays to any of our subscribed addresses
    for addr in list(self.subscribed_addresses):
        for output in vout:
            if output.get('scriptpubkey_address') == addr:
                # 6.3: Calculate amount
                amount_sats = output.get('value', 0)
                amount_btc = amount_sats / 100000000
                
                logger.info(f"🎯 [WEBSOCKET] Transaction {txid[:16]}... pays {amount_btc:.8f} BTC to {addr[:10]}...")
                
                # 6.4: Process using transaction service
                tx_service = TransactionService()
                tx = await tx_service.verify_user_submitted_tx(txid, addr)
                
                if tx:
                    logger.info(f"✅ [WEBSOCKET] Transaction saved to database")
                    # Continue to bet processing...
```

**Matching Logic:**
```
FOR each output in transaction.vout:
    IF output.scriptpubkey_address == "mrHLHe4vgspzEeECWNdi..." (2x wallet):
        ✅ MATCH FOUND!
        → Extract amount: 100,000 sats
        → Save to database
        → Continue to bet processing
```

---

## 💾 **Step 7: Save Transaction to Database**

### **File:** `backend/app/services/transaction_service.py`

```python
async def verify_user_submitted_tx(self, txid: str, expected_address: str):
    # 7.1: Check if already in database
    existing_tx = await self.tx_repo.get_by_txid(txid)
    if existing_tx:
        logger.info(f"Transaction {txid[:16]}... already in database")
        return existing_tx
    
    # 7.2: Fetch from Mempool.space (already done)
    tx_data = await self.get_transaction_details(txid)
    
    # 7.3: Save to MongoDB 'transactions' collection
    return await self._process_mempool_tx(txid, expected_address, source="websocket")
```

**MongoDB Document Created:**
```json
{
  "_id": ObjectId("..."),
  "txid": "abc123...",
  "to_address": "mrHLHe4vgspzEeECWNdiRmEFwVgHzfhNE7",
  "from_address": "sender's address",
  "amount": 100000,
  "confirmations": 0,
  "is_processed": false,
  "detected_by": "websocket",
  "detected_at": "2026-01-14T22:00:00Z"
}
```

---

## 🎲 **Step 8: Create Bet and Calculate Result**

### **File:** `backend/app/services/bet_service.py`

```python
async def process_detected_transaction(self, transaction_dict: Dict):
    # 8.1: Get target wallet by address
    target_address = transaction_dict["to_address"]  # "mrHLHe4vgspzEeECWNdi..."
    wallet = await self.wallet_service.get_wallet_by_address(target_address)
    
    # 8.2: Extract multiplier from wallet
    multiplier_int = wallet["multiplier"]  # 2
    multiplier_float = float(multiplier_int)  # 2.0
    
    logger.info(f"[BET] Using {multiplier_int}x wallet for bet")
    
    # 8.3: Calculate win chance
    win_chance = self.fair_service.calculate_win_chance(multiplier_float)  # 50%
    
    # 8.4: Generate provably fair result
    roll_result = self.fair_service.generate_roll_result(
        server_seed, client_seed, nonce
    )  # Random number 0-99.99
    
    # 8.5: Determine if win or loss
    is_win = roll_result < win_chance  # If roll < 50, user wins!
    
    # 8.6: Calculate payout
    if is_win:
        payout_amount = int(bet_amount * multiplier_float)  # 100k * 2 = 200k sats
    else:
        payout_amount = 0
    
    # 8.7: Save bet to database
    bet_doc = {
        "user_id": user_id,
        "bet_amount": 100000,
        "target_multiplier": 2.0,
        "multiplier": 2,
        "target_address": "mrHLHe4vgspzEeECWNdiRmEFwVgHzfhNE7",
        "win_chance": 50.0,
        "roll_result": roll_result,
        "is_win": is_win,
        "payout_amount": payout_amount,
        "status": "win" if is_win else "loss",
        "deposit_txid": "abc123...",
        "created_at": datetime.utcnow()
    }
    await self.bet_repo.create(bet_doc)
```

**Result Calculation:**
```
User sends: 100,000 sats to 2x wallet
→ Win Chance: 50%
→ Roll: 35.67 (random)
→ 35.67 < 50? YES!
→ Result: WIN 🎉
→ Payout: 100,000 * 2 = 200,000 sats
```

---

## 💰 **Step 9: Send Payout (If Win)**

### **File:** `backend/app/services/payout_service.py`

```python
async def send_payout(self, bet: Dict, target_wallet: Dict):
    # 9.1: Decrypt private key (in memory only)
    private_key_wif = self.wallet_service.decrypt_private_key(target_wallet)
    
    # 9.2: Get UTXOs from target wallet
    utxos = await self._fetch_utxos(target_wallet["address"])
    
    # 9.3: Build transaction
    # Input: UTXO from target wallet (e.g., 100,000 sats)
    # Output 1: User's payout (200,000 sats)
    # Output 2: Change back to target wallet
    tx_hex = await self._build_transaction(
        utxos, user_address, payout_amount, private_key_wif
    )
    
    # 9.4: Broadcast to Bitcoin network
    txid = await self._broadcast_transaction(tx_hex)
    
    logger.info(f"💸 [PAYOUT] Sent {payout_amount} sats to {user_address[:10]}...")
```

**Transaction Flow:**
```
Input:  Target Wallet has 100,000 sats
Output: Send 200,000 sats to user
        (Requires funding from other bets/deposits in the wallet)
```

---

## 📡 **Step 10: Broadcast to Frontend**

### **File:** `backend/app/utils/mempool_websocket.py`

```python
async def _broadcast_bet_result(self, bet: Dict):
    from app.utils.websocket_manager import manager
    
    # 10.1: Create bet response data
    bet_data = {
        "id": str(bet["_id"]),
        "bet_amount": bet["bet_amount"],
        "target_multiplier": bet["target_multiplier"],
        "roll_result": bet.get("roll_result"),
        "is_win": bet.get("is_win"),
        "payout_amount": bet.get("payout_amount"),
        "status": bet["status"],
        ...
    }
    
    # 10.2: Broadcast via WebSocket to all connected frontend clients
    await manager.broadcast({
        "type": "new_bet",
        "bet": bet_data
    })
    
    logger.info(f"📡 [WEBSOCKET] Broadcast bet result to frontend clients")
```

**WebSocket Message Sent to Frontend:**
```json
{
  "type": "new_bet",
  "bet": {
    "id": "...",
    "bet_amount": 100000,
    "target_multiplier": 2.0,
    "roll_result": 35.67,
    "is_win": true,
    "payout_amount": 200000,
    "status": "win"
  }
}
```

---

## 📊 **Complete Flow Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. STARTUP                                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ • Load 7 vault wallets from MongoDB                     │ │
│ │ • Connect to Mempool.space WebSocket                    │ │
│ │ • Subscribe to all 7 addresses                          │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. USER SENDS BITCOIN                                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ User → Sends 100k sats → mrHLHe...E7 (2x wallet)       │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. MEMPOOL.SPACE DETECTS                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Mempool.space sees transaction in mempool               │ │
│ │ Checks: Does it involve mrHLHe...E7?  YES!             │ │
│ │ Sends: {"address-transactions": {"txid": "abc123..."}} │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. BACKEND RECEIVES NOTIFICATION                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [WEBSOCKET] 🔔 New transaction detected: abc123...     │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. FETCH FULL TRANSACTION DETAILS                           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ GET /api/tx/abc123...                                   │ │
│ │ Response: {vout: [{address: mrHLHe..., value: 100k}]} │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. VERIFY TARGET ADDRESS                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Check: Does vout pay to mrHLHe...E7? YES!              │ │
│ │ Amount: 100,000 sats                                    │ │
│ │ [WEBSOCKET] 🎯 Transaction pays to 2x wallet           │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. SAVE TO DATABASE                                         │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ MongoDB 'transactions' collection                       │ │
│ │ {txid, to_address, amount, detected_by: "websocket"}   │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. CREATE BET & CALCULATE                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ • Find wallet by address → multiplier = 2x              │ │
│ │ • Calculate win chance → 50%                            │ │
│ │ • Generate roll → 35.67                                 │ │
│ │ • Check if win → 35.67 < 50? YES! WIN 🎉              │ │
│ │ • Calculate payout → 100k * 2 = 200k sats              │ │
│ │ • Save bet to MongoDB 'bets' collection                 │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. SEND PAYOUT (If Win)                                     │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ • Decrypt 2x wallet private key (in memory)             │ │
│ │ • Fetch UTXOs from 2x wallet                            │ │
│ │ • Build & sign transaction: 200k sats → user           │ │
│ │ • Broadcast to Bitcoin network                          │ │
│ │ [PAYOUT] 💸 Sent 200k sats to user                     │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 10. BROADCAST TO FRONTEND                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Send WebSocket message to all connected clients:        │ │
│ │ {type: "new_bet", bet: {...result...}}                 │ │
│ │ [WEBSOCKET] 📡 Broadcast bet result                    │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 **Key Technical Points**

### **1. Why WebSocket Instead of Polling?**
- ✅ **Real-time:** Instant notification when transaction enters mempool (0-2 seconds)
- ✅ **Efficient:** No repeated API calls, server pushes updates
- ✅ **Scalable:** Can monitor unlimited addresses with single connection

### **2. How Does Address Matching Work?**
```python
# Transaction has multiple outputs (vout)
for output in transaction.vout:
    if output.address in subscribed_addresses:
        # MATCH! This is a deposit to one of our wallets
        process_transaction(output.address, output.value)
```

### **3. Multiplier Detection Logic:**
```python
# Step 1: Transaction detected to address "mrHLHe4vgspzEeECWNdiRmEFwVgHzfhNE7"
# Step 2: Query MongoDB wallets collection
wallet = db.wallets.find_one({"address": "mrHLHe4vgspzEeECWNdiRmEFwVgHzfhNE7"})
# Step 3: Extract multiplier from wallet document
multiplier = wallet["multiplier"]  # Result: 2
# Step 4: Use this multiplier for payout calculation
payout = deposit_amount * multiplier  # 100k * 2 = 200k
```

### **4. Security:**
- 🔒 Private keys stored encrypted in MongoDB
- 🔒 Decrypted only in memory during payout signing
- 🔒 Never logged, never sent to frontend
- 🔒 Each wallet isolated - compromise of one doesn't affect others

### **5. Reliability:**
- 🔄 Auto-reconnect with exponential backoff
- 🔄 Re-subscribe to all addresses after reconnect
- 🔄 Duplicate transaction check (prevents double-processing)
- 🔄 Transaction confirmations tracked

---

## ✅ **Summary**

**Your backend detects incoming transactions through:**

1. ✅ **Mempool.space WebSocket** - Real-time push notifications
2. ✅ **Address Subscription** - Monitors all 7 vault wallet addresses
3. ✅ **Output Matching** - Checks transaction outputs against subscribed addresses
4. ✅ **Multiplier Lookup** - Finds wallet in MongoDB by address to get multiplier
5. ✅ **Automatic Processing** - Creates bet, calculates result, sends payout
6. ✅ **Frontend Broadcast** - Notifies all connected users via WebSocket

**Current Status:**
- 🟢 **Active:** Monitoring 7 vault wallets
- 🟢 **Connected:** WebSocket to Mempool.space testnet
- 🟢 **Ready:** System will auto-process any incoming transaction

**No code changes needed - this is your current production system!** 🎉
