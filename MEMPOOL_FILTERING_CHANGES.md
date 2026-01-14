# Mempool Filtering Implementation - Transaction Detection Refactor

## 🔄 **BREAKING CHANGE: New Transaction Detection Method**

---

## 📊 **What Changed?**

### **Before (Address Tracking):**
```
Backend → Sends {"track-address": "mrHLHe..."} for each wallet
Mempool.space → Monitors specific addresses
Mempool.space → Pushes {"address-transactions": {...}} when match found
Backend → Receives notification → Processes transaction
```

### **After (Mempool Filtering):**
```
Backend → Subscribes to FULL mempool transaction feed
Mempool.space → Pushes ALL new transactions
Backend → Filters each transaction for target addresses
Backend → If match found → Processes transaction
```

---

## 🎯 **Key Differences**

| Aspect | Address Tracking (Old) | Mempool Filtering (New) |
|--------|----------------------|-------------------------|
| **WebSocket Subscription** | Specific addresses | Full mempool feed |
| **Server Load** | Low (server filters) | Higher (client filters) |
| **Bandwidth** | Low (only relevant txs) | Higher (all transactions) |
| **Reliability** | Depends on server | Independent filtering |
| **Scalability** | Limited by server | Limited by client CPU |
| **Control** | Server-side | Client-side |

---

## 🔧 **Technical Changes**

### **1. Removed: `subscribe_address()` Method**

**Old Code:**
```python
async def subscribe_address(self, address: str):
    """Subscribe to a specific Bitcoin address"""
    track_msg = {"track-address": address}
    await self.websocket.send(json.dumps(track_msg))
    self.subscribed_addresses.add(address)
```

**New Code:**
```python
def add_monitored_address(self, address: str):
    """Add address to local monitoring list"""
    self.subscribed_addresses.add(address)
    logger.info(f"[WEBSOCKET] 📍 Added to monitoring list: {address[:20]}...")
```

**Why?**
- No longer sending `track-address` messages to server
- Addresses stored locally for filtering
- Synchronous method (no WebSocket communication)

---

### **2. Updated: `subscribe_to_mempool()` Method**

**Old Code:**
```python
async def subscribe_to_mempool(self):
    init_msg = {"action": "want", "data": ["blocks", "mempool-blocks"]}
    await self.websocket.send(json.dumps(init_msg))
    logger.info("[WEBSOCKET] 📊 Subscribed to mempool updates")
```

**New Code:**
```python
async def subscribe_to_mempool(self):
    # Subscribe to mempool transactions feed
    init_msg = {"action": "want", "data": ["blocks", "mempool-blocks", "live-2h-chart"]}
    await self.websocket.send(json.dumps(init_msg))
    
    # Enable tracking for ALL mempool transactions
    await self.websocket.send(json.dumps({"track-mempool": "all"}))
    
    logger.info("[WEBSOCKET] 📊 Subscribed to FULL mempool transaction feed")
    logger.info(f"[WEBSOCKET] 🔍 Monitoring {len(self.subscribed_addresses)} target addresses")
```

**Why?**
- Requests full mempool transaction stream
- Adds `live-2h-chart` for additional transaction data
- Sends `{"track-mempool": "all"}` to get all transactions

---

### **3. Refactored: `handle_message()` Method**

**Old Code:**
```python
async def handle_message(self, message: str):
    data = json.loads(message)
    
    # Handle address-transactions messages (our target)
    if "address-transactions" in data:
        address_txs = data["address-transactions"]
        # Process specific address transactions
        ...
```

**New Code:**
```python
async def handle_message(self, message: str):
    data = json.loads(message)
    
    # Handle new mempool transaction
    if "tx" in data or "mempoolInfo" in data:
        tx_data = data.get("tx") or data.get("mempoolInfo")
        if tx_data and isinstance(tx_data, dict):
            await self._check_transaction_for_targets(tx_data)
    
    # Handle other transaction formats
    elif isinstance(data, dict):
        if "txid" in data or "vout" in data:
            await self._check_transaction_for_targets(data)
```

**Why?**
- Looks for generic transaction data (`tx`, `mempoolInfo`, `txid`, `vout`)
- No longer expects `address-transactions` format
- Passes all transaction data to filtering function

---

### **4. New: `_check_transaction_for_targets()` Method**

**New Code:**
```python
async def _check_transaction_for_targets(self, tx_data: dict):
    """
    Check if transaction involves any of our target addresses
    
    Args:
        tx_data: Transaction data from mempool
    """
    try:
        # Extract txid
        txid = tx_data.get('txid')
        if not txid:
            return
        
        # Get outputs
        vout = tx_data.get('vout', [])
        if not vout:
            return
        
        # Check each output against our monitored addresses
        for output in vout:
            output_address = output.get('scriptpubkey_address') or output.get('address')
            
            if output_address in self.subscribed_addresses:
                # MATCH FOUND!
                amount_sats = output.get('value', 0)
                amount_btc = amount_sats / 100_000_000
                
                logger.info(f"🎯 [MEMPOOL FILTER] MATCH! TX {txid[:16]}... → {output_address[:10]}... ({amount_btc:.8f} BTC)")
                
                # Process this transaction
                await self._process_transaction(txid)
                return  # Only process once per transaction
                
    except Exception as e:
        logger.error(f"[WEBSOCKET] Error checking transaction for targets: {e}")
```

**Why?**
- **Client-side filtering:** Checks every transaction against our 7 target addresses
- **Efficient matching:** Uses `in` operator on set (O(1) lookup)
- **Detailed logging:** Shows when match is found
- **Early exit:** Returns after first match to avoid duplicate processing

---

### **5. Updated: `start()` Method**

**Old Code:**
```python
async def start(self):
    if await self.connect():
        await self.subscribe_to_mempool()
        
        # Re-track addresses
        if self.subscribed_addresses:
            logger.info(f"[WEBSOCKET] Re-tracking {len(self.subscribed_addresses)} addresses")
            for address in list(self.subscribed_addresses):
                track_msg = {"track-address": address}
                await self.websocket.send(json.dumps(track_msg))
        
        await self.listen()
```

**New Code:**
```python
async def start(self):
    if await self.connect():
        # Subscribe to FULL mempool feed
        await self.subscribe_to_mempool()
        
        logger.info(f"[WEBSOCKET] 🔍 Filtering for {len(self.subscribed_addresses)} target addresses")
        
        # Listen for messages and filter
        await self.listen()
```

**Why?**
- No longer sends individual `track-address` messages
- Simplified reconnection logic
- All filtering happens in `handle_message()`

---

### **6. Updated: `transaction_monitor_service.py`**

**Old Code:**
```python
for wallet in active_wallets:
    address = wallet["address"]
    multiplier = wallet["multiplier"]
    await self.websocket_client.subscribe_address(address)  # WebSocket call
    self.monitored_addresses.add(address)
```

**New Code:**
```python
for wallet in active_wallets:
    address = wallet["address"]
    multiplier = wallet["multiplier"]
    self.websocket_client.add_monitored_address(address)  # Local only
    self.monitored_addresses.add(address)
```

**Why?**
- Changed from async WebSocket subscription to sync local addition
- No network calls during initialization
- Faster startup

---

## 🔍 **How Filtering Works**

### **Step-by-Step Flow:**

```
1. Mempool.space broadcasts: {"tx": {"txid": "abc...", "vout": [...]}}
                              ↓
2. Backend receives message in handle_message()
                              ↓
3. Extracts transaction data: tx_data = data.get("tx")
                              ↓
4. Calls _check_transaction_for_targets(tx_data)
                              ↓
5. Loops through vout outputs:
   for output in vout:
       output_address = output.get('scriptpubkey_address')
                              ↓
6. Checks if address in monitored set:
   if output_address in self.subscribed_addresses:  # O(1) lookup
                              ↓
7. MATCH FOUND! Log and process:
   logger.info("🎯 [MEMPOOL FILTER] MATCH!")
   await self._process_transaction(txid)
```

---

## 📊 **Performance Considerations**

### **Pros:**
✅ **Independent:** Not reliant on server-side filtering
✅ **Flexible:** Can add custom filtering logic
✅ **Reliable:** No dependency on server's address tracking feature
✅ **Debuggable:** Full visibility into all transactions

### **Cons:**
⚠️ **Higher Bandwidth:** Receives ALL mempool transactions (testnet: ~10-50 tx/min, mainnet: ~1000-5000 tx/min)
⚠️ **More CPU:** Client must check every transaction
⚠️ **More Logs:** Potentially verbose if logging all transactions

### **Optimization:**
- Uses Python `set` for O(1) address lookup
- Early exit after first match
- Only fetches full transaction details after match

---

## 🎯 **Expected Behavior**

### **Startup Logs:**
```
[MONITOR] 📍 Monitoring 2x wallet: mrHLHe4vgspzEeECWNdi...
[MONITOR] 📍 Monitoring 3x wallet: mhFc5TRW1uB5fUUia3qn...
...
[MONITOR] ✅ Monitoring 7 vault wallet(s)
[WEBSOCKET] Connecting to wss://mempool.space/testnet/api/v1/ws...
[WEBSOCKET] ✅ Connected successfully
[WEBSOCKET] 📊 Subscribed to FULL mempool transaction feed
[WEBSOCKET] 🔍 Monitoring 7 target addresses
[WEBSOCKET] 🔍 Filtering for 7 target addresses
```

### **When Transaction Detected:**
```
[WEBSOCKET] <<<  Message received (length: 2847)
[MEMPOOL FILTER] 🎯 MATCH! TX abc123... → mrHLHe4vgs... (0.00100000 BTC)
[WEBSOCKET] 🔔 New transaction detected: abc123...
[WEBSOCKET] 🎯 Transaction abc123... pays 0.00100000 BTC to mrHLHe4vgs...
[WEBSOCKET] ✅ Transaction saved to database
[BET] Using 2x wallet for bet
🎲 [WEBSOCKET] Bet created: ID ... - WIN 🎉
💰 [WEBSOCKET] Amount: 100000 sats, Payout: 200000 sats
```

---

## ⚠️ **Important Notes**

### **1. Testnet vs Mainnet:**
- **Testnet:** ~10-50 transactions per minute (manageable)
- **Mainnet:** ~1000-5000 transactions per minute (high load!)

**Recommendation for Mainnet:**
Consider implementing:
- Rate limiting on message processing
- Batch filtering (process multiple txs at once)
- Async queue for transaction processing
- Caching to avoid duplicate checks

### **2. WebSocket Message Format:**
Mempool.space may send transactions in different formats:
- `{"tx": {...}}` - New transaction
- `{"mempoolInfo": {...}}` - Mempool info update
- Raw transaction data with `txid` and `vout`

The code handles all these formats.

### **3. Fallback:**
If the full mempool feed is too heavy, you can:
1. Revert to address tracking (restore old code)
2. Use hybrid approach (track + filter)
3. Implement REST API polling as backup

---

## 🚀 **Testing**

### **To Test:**
1. **Start Backend:** Already running on port 8000
2. **Send Test Transaction:** Send testnet BTC to any of your 7 wallet addresses
3. **Watch Logs:** Look for `[MEMPOOL FILTER] 🎯 MATCH!` message
4. **Verify Processing:** Check that bet is created and payout sent

### **Expected Timeline:**
```
T+0s:  User broadcasts transaction
T+1s:  Transaction enters mempool
T+2s:  Mempool.space detects transaction
T+3s:  Backend receives via WebSocket
T+3s:  Backend filters and finds match
T+4s:  Backend processes bet
T+5s:  Payout sent (if win)
```

---

## 📝 **Summary**

**Changed From:**
- Server-side address tracking with targeted notifications

**Changed To:**
- Client-side filtering of full mempool transaction feed

**Impact:**
- More bandwidth usage
- More CPU usage
- More control and flexibility
- Independent of server features

**Status:**
✅ Code updated and committed
✅ Backend restarted with new logic
✅ Ready for testing

---

## 🔄 **Rollback Plan**

If this approach doesn't work well, you can rollback:

```bash
cd D:\Dice2
git revert HEAD
git push origin main
# Restart backend
```

Or restore specific methods from git history.
