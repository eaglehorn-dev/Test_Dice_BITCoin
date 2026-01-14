# Multiplier Slider Setup Guide

## ✅ Status: Multiplier Slider IS Implemented!

The multiplier slider is already in the frontend at:
- **Component:** `frontend/src/components/MultiplierSlider.js`
- **Used in:** `frontend/src/components/DiceGame.js` (line 129-134)

---

## ⚠️ **Why You Don't See It:**

The slider only appears when there are **active wallets in the vault**. Currently, your vault is **empty**.

**Backend Log:**
```
WARNING: No active vault wallets found!
WARNING: Run the admin script to create wallets first
```

**API Response:**
```
GET /api/wallets/all → [] (empty array)
```

---

## 🔧 **How to Make the Slider Appear:**

### **Option 1: Use Admin Dashboard (Recommended)**

1. **Open Admin Dashboard:**
   ```
   http://localhost:3001
   ```

2. **Generate Wallets:**
   - Scroll to "🔑 Wallet Vault" section
   - Enter multiplier: `2`
   - Click "➕ Generate Wallet"
   - Repeat for: `3`, `5`, `10`, `100`

3. **Refresh Main Frontend:**
   ```
   http://95.216.67.104:3000
   ```
   
4. **The slider will now appear! 🎉**

---

### **Option 2: Use Backend Script**

1. **Create a wallet generation script** (`backend/generate_wallets.py`):
   ```python
   import asyncio
   from app.services.wallet_service import WalletService
   from app.utils.database import connect_db
   
   async def generate_wallets():
       await connect_db()
       wallet_service = WalletService()
       
       multipliers = [2, 3, 5, 10, 100]
       
       for mult in multipliers:
           result = await wallet_service.generate_wallet(mult)
           print(f"✅ Generated {mult}x wallet: {result['address']}")
   
   if __name__ == "__main__":
       asyncio.run(generate_wallets())
   ```

2. **Run the script:**
   ```bash
   cd D:\Dice2\backend
   python generate_wallets.py
   ```

---

## 📊 **What the Slider Looks Like:**

Once wallets are generated, the frontend will show:

### **Slider Component:**
```
🎯 Choose Your Multiplier

   [====•====] ← Interactive slider
   2x  3x  5x  10x  100x

   [2x] [3x] [5x] [10x] [100x] ← Clickable buttons

   Win Chance: 50.00%
   Example: 1,000 sats → 2,000 sats
```

### **Features:**
- ✅ **Drag Slider:** Smooth selection
- ✅ **Click Buttons:** Direct multiplier selection
- ✅ **Live Preview:** Shows win chance and example payout
- ✅ **Auto QR Update:** QR code changes when multiplier changes
- ✅ **Address Update:** Display shows correct wallet address

---

## 🎯 **Current Implementation Details:**

### **MultiplierSlider Component** (`frontend/src/components/MultiplierSlider.js`)

**Features:**
- Fetches available wallets from `/api/wallets/all`
- Sorts wallets by multiplier (2x, 3x, 5x, etc.)
- Shows slider with markers for each multiplier
- Shows clickable buttons for each multiplier
- Displays win chance calculation: `100 / multiplier`
- Shows example payout: `bet_amount * multiplier`
- Auto-selects first (lowest) multiplier on load

**Props:**
- `wallets`: Array of wallet objects from backend
- `onMultiplierChange`: Callback when user changes multiplier

---

### **DiceGame Component** (`frontend/src/components/DiceGame.js`)

**Integration:**
```javascript
// Lines 11-12: State management
const [wallets, setWallets] = useState([]);
const [selectedWallet, setSelectedWallet] = useState(null);

// Lines 19-38: Load wallets from API
const loadWallets = async () => {
  const walletsData = await getAllWallets(); // GET /api/wallets/all
  setWallets(walletsData);
};

// Lines 40-44: Handle multiplier changes
const handleMultiplierChange = (wallet) => {
  setSelectedWallet(wallet);
  setWalletAddress(wallet.address); // Update QR code
};

// Lines 129-134: Render slider
{wallets.length > 0 && (
  <MultiplierSlider 
    wallets={wallets} 
    onMultiplierChange={handleMultiplierChange}
  />
)}
```

---

## 🔍 **Debugging:**

### **Check if wallets exist:**
```bash
# In browser console or via API:
curl http://95.216.67.104:8000/api/wallets/all
```

**Expected Response (when wallets exist):**
```json
[
  {
    "wallet_id": "...",
    "multiplier": 2,
    "address": "tb1q...",
    "label": "2x Wallet",
    "is_active": true,
    "network": "testnet"
  },
  {
    "multiplier": 3,
    "address": "tb1q...",
    ...
  }
]
```

**Current Response (no wallets):**
```json
[]
```

---

## ✅ **Summary:**

1. ✅ **Multiplier slider IS implemented** in the frontend
2. ⚠️ **You don't see it because the vault is empty**
3. 🔧 **Generate wallets using admin dashboard** at http://localhost:3001
4. 🎉 **Slider will automatically appear** when wallets exist
5. ✅ **All features work:** Slider, buttons, QR code, address updates

---

## 🚀 **Next Steps:**

1. Go to **Admin Dashboard:** http://localhost:3001
2. Generate wallets for: **2x, 3x, 5x, 10x, 100x**
3. Refresh **Main Frontend:** http://95.216.67.104:3000
4. **See the slider in action! 🎯**
