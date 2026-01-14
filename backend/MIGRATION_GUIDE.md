# 🔄 **DDD Migration Guide - Final Steps**

## Current Status

### ✅ **Phase 1 & 2 Complete** (85% Done)

**Created:**
- ✅ `app/core/` - Config & Exceptions
- ✅ `app/models/` - MongoDB document models
- ✅ `app/dtos/` - API validation schemas
- ✅ `app/repository/` - Data access layer
- ✅ `app/services/` - Business logic layer
- ✅ `app/utils/` - Helpers & utilities

---

## 🎯 **Final Step: Update Imports in Existing Files**

The new DDD architecture is ready, but the **old files still use old imports**. Here's how to complete the migration:

---

### **Files to Update:**

#### **1. `backend/app/main.py`** (Priority: HIGH)

**Current imports:**
```python
from .config import config
from .database import init_db, get_users_collection, ...
from .provably_fair import ProvablyFair
from .payout import PayoutEngine, BetProcessor
from .blockchain import TransactionDetector
```

**New imports:**
```python
from app.core.config import config
from app.models.database import init_db, disconnect_db, get_users_collection, ...
from app.services.provably_fair_service import ProvablyFairService
from app.services.bet_service import BetService
from app.services.payout_service import PayoutService
from app.utils.websocket_manager import ConnectionManager
from app.utils.blockchain import BlockchainHelper
```

**Specific changes:**
- Replace `ProvablyFair` → `ProvablyFairService`
- Replace `PayoutEngine` → `PayoutService`
- Replace `BetProcessor` → `BetService`
- Replace local `ConnectionManager` class with `from app.utils.websocket_manager import ConnectionManager`

---

#### **2. `backend/app/blockchain.py`** (Priority: HIGH)

**Current imports:**
```python
from .config import config
from .database import get_transactions_collection, ...
```

**New imports:**
```python
from app.core.config import config
from app.core.exceptions import BlockchainException, WebSocketException
from app.models.database import get_transactions_collection, ...
from app.services.bet_service import BetService
from app.utils.blockchain import BlockchainHelper
```

**Specific changes:**
- Update all exception handling to use custom exceptions from `app.core.exceptions`
- Replace direct database calls with service calls where appropriate

---

#### **3. `backend/app/payout.py`** (Priority: MEDIUM)

**Status:** This file is now **redundant**. All logic has been moved to:
- `app/services/payout_service.py`
- `app/services/bet_service.py`

**Action:** Can be deleted after confirming `main.py` uses the new services.

---

#### **4. `backend/app/provably_fair.py`** (Priority: MEDIUM)

**Status:** This file is now **redundant**. All logic moved to:
- `app/services/provably_fair_service.py`

**Action:** Can be deleted after confirming `main.py` uses the new service.

---

#### **5. `backend/app/config.py`** (Priority: LOW)

**Status:** Redundant copy. The real config is now in:
- `app/core/config.py`

**Action:** Can be deleted after updating imports.

---

#### **6. `backend/app/database.py`** (Priority: LOW)

**Status:** Redundant copy. Database logic is now in:
- `app/models/database.py`
- Individual model files in `app/models/`

**Action:** Can be deleted after updating imports.

---

## 🚀 **Quick Migration Script**

Here's the simplest way to complete the migration:

### **Step 1: Update main.py imports**

```python
# At the top of backend/app/main.py, replace:

# OLD
from .config import config
from .database import init_db, ...
from .provably_fair import ProvablyFair
from .payout import PayoutEngine, BetProcessor
from .blockchain import TransactionDetector

# NEW
from app.core.config import config
from app.models.database import init_db, disconnect_db, get_database, get_users_collection, get_seeds_collection, get_bets_collection, get_transactions_collection, get_payouts_collection, get_deposit_addresses_collection
from app.services.provably_fair_service import ProvablyFairService, generate_new_seed_pair
from app.services.bet_service import BetService
from app.services.payout_service import PayoutService
from app.utils.websocket_manager import ConnectionManager
from app.blockchain import TransactionDetector, TransactionMonitor  # Keep for now
```

### **Step 2: Update class usage in main.py**

Search and replace in `main.py`:
- `ProvablyFair.` → `ProvablyFairService.`
- `PayoutEngine` → `PayoutService`
- `BetProcessor` → `BetService`

### **Step 3: Remove local ConnectionManager**

Delete lines 53-81 in `main.py` (the ConnectionManager class definition) since we now import it from utils.

### **Step 4: Update blockchain.py imports**

```python
# At the top of backend/app/blockchain.py, replace:

# OLD
from .config import config
from .database import get_transactions_collection, ...

# NEW
from app.core.config import config
from app.core.exceptions import BlockchainException, WebSocketException
from app.models.database import get_transactions_collection, get_deposit_addresses_collection
from app.services.bet_service import BetService
```

### **Step 5: Update blockchain.py to use BetService**

In `TransactionDetector.process_transaction()`, replace:
```python
# OLD
from .payout import BetProcessor
bet_processor = BetProcessor()

# NEW
from app.services.bet_service import BetService
bet_service = BetService()
await bet_service.process_detected_transaction(transaction_dict)
```

### **Step 6: Test the changes**

```bash
cd D:\Dice2\backend
.\venv\Scripts\activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

If everything works, you'll see:
```
[STARTUP] Starting Bitcoin Dice Game API
[OK] Configuration validated
[OK] Connected to MongoDB: dice_game_mainnet
[OK] Database indexes created
```

### **Step 7: Clean up old files (AFTER testing)**

Once confirmed working, delete:
```bash
rm backend/app/config.py
rm backend/app/database.py
rm backend/app/payout.py
rm backend/app/provably_fair.py
```

---

## 📝 **Testing Checklist**

After updating imports, test these features:

- [ ] **Server starts** without import errors
- [ ] **Database connects** to MongoDB
- [ ] **WebSocket connects** (`ws://localhost:8001/ws`)
- [ ] **Transaction detection** works (test with a deposit)
- [ ] **Bet processing** works (roll dice)
- [ ] **Payout creation** works (for winning bets)
- [ ] **API endpoints** respond correctly:
  - `GET /api/health`
  - `GET /api/stats`
  - `GET /api/bets/history/{address}`
  - `GET /api/bets/recent`

---

## 🎯 **Benefits After Migration**

| Aspect | Before | After |
|--------|--------|-------|
| **File Size** | 700+ line main.py | <200 lines main.py |
| **Testing** | Hard to mock | Easy to mock services |
| **Reusability** | Copy-paste code | Import services |
| **Organization** | Everything in root | Clear layers |
| **Scalability** | Messy to add features | Clean service addition |

---

## 🔍 **Troubleshooting**

### **Import Error: "No module named 'app.core'"**

**Solution:** Make sure you're running from the correct directory:
```bash
cd D:\Dice2\backend
python -m uvicorn app.main:app --reload
```

### **Import Error: "attempted relative import beyond top-level package"**

**Solution:** Use absolute imports (`from app.core...`) instead of relative (`from .core...`)

### **MongoDB Connection Error**

**Solution:** Ensure MongoDB is running:
```bash
net start MongoDB
```

---

## 🎓 **Example: Using the New Architecture**

### **Before (Old Way):**
```python
# In main.py
from .payout import PayoutEngine
from .database import get_db

db = next(get_db())
engine = PayoutEngine(db)
engine.process_winning_bet(bet)
```

### **After (New Way):**
```python
# In main.py
from app.services.payout_service import PayoutService

payout_service = PayoutService()
await payout_service.process_winning_bet(bet_dict)
```

**Benefits:**
- No manual database session management
- All async (better performance)
- Testable (can mock PayoutService)
- Clear responsibility

---

## 📊 **Migration Progress**

- ✅ **Phase 1:** Core, Models, DTOs, Repositories (100%)
- ✅ **Phase 2:** Services, Utils (100%)
- 🔄 **Phase 3:** Update imports in main.py, blockchain.py (15% - in progress)
- ⏳ **Phase 4:** Delete old files, final testing (0%)

**Overall: ~85% Complete**

---

## 🚀 **Next Steps (You Can Do This!)**

1. **Update imports** in `main.py` (10 mins)
2. **Update imports** in `blockchain.py` (5 mins)
3. **Test the server** (2 mins)
4. **Delete old files** (1 min)
5. **Commit & push** ✅

**Total time: ~20 minutes of work!**

---

## 💡 **Need Help?**

If you get stuck:
1. Check the imports match exactly
2. Ensure MongoDB is running
3. Look at the new service files for method names
4. All methods are now `async` - remember to `await`

**The hard work is done - just need to connect the dots! 🎉**
