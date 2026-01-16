# Per-Multiplier Bet Amount Range Implementation Plan

## Overview
Implement per-multiplier bet amount ranges, allowing administrators to set different min/max bet limits for each multiplier. The frontend will dynamically adjust bet amount controls based on the selected multiplier, and display the bet amount in the QR code.

## Current State

### Backend
- Global bet limits: `MIN_BET_SATOSHIS` and `MAX_BET_SATOSHIS` in `config.py`
- Wallet model stores: `multiplier`, `chance`, `address`, but no bet range fields
- API returns wallet info without bet range data

### Frontend
- Single `minBet` and `maxBet` state (from `/api/stats/house`)
- Bet amount slider uses global limits
- QR code shows only address, not bet amount

## Implementation Plan

### Phase 1: Backend Changes

#### 1.1 Database Schema Update
**File**: `backend/app/models/database.py` or wallet model

Add fields to wallet document:
```python
min_bet_sats: Optional[int] = None  # Minimum bet in satoshis for this multiplier
max_bet_sats: Optional[int] = None  # Maximum bet in satoshis for this multiplier
```

**Migration Strategy**:
- Add fields as optional (default to `None`)
- If `None`, fall back to global `MIN_BET_SATOSHIS` / `MAX_BET_SATOSHIS`
- Ensure backward compatibility

#### 1.2 Admin Backend DTOs
**File**: `admin_backend/app/dtos/admin_dtos.py`

Update DTOs:
```python
class GenerateWalletRequest(BaseModel):
    multiplier: int
    address_type: str
    chance: float
    min_bet_sats: Optional[int] = None  # NEW: Per-multiplier min bet
    max_bet_sats: Optional[int] = None  # NEW: Per-multiplier max bet

class UpdateWalletRequest(BaseModel):
    multiplier: Optional[int] = None
    chance: Optional[float] = None
    label: Optional[str] = None
    is_active: Optional[bool] = None
    min_bet_sats: Optional[int] = None  # NEW: Update min bet
    max_bet_sats: Optional[int] = None  # NEW: Update max bet

class WalletInfo(BaseModel):
    # ... existing fields ...
    min_bet_sats: Optional[int] = None  # NEW
    max_bet_sats: Optional[int] = None  # NEW
```

#### 1.3 Admin Backend Service
**File**: `admin_backend/app/services/wallet_service.py`

Update `generate_wallet()`:
- Accept `min_bet_sats` and `max_bet_sats` parameters
- Validate: `min_bet_sats < max_bet_sats` if both provided
- Store in wallet document
- If not provided, set to `None` (will use global defaults)

Update `update_wallet()`:
- Accept `min_bet_sats` and `max_bet_sats` parameters
- Validate ranges
- Update wallet document

#### 1.4 Admin Backend Routes
**File**: `admin_backend/app/api/admin_routes.py`

Update routes:
- `POST /admin/wallet/generate`: Accept `min_bet_sats`, `max_bet_sats` in request body
- `PUT /admin/wallet/{wallet_id}`: Accept `min_bet_sats`, `max_bet_sats` in request body
- `GET /admin/wallets`: Return `min_bet_sats`, `max_bet_sats` in response

#### 1.5 Main Backend Wallet Routes
**File**: `backend/app/api/wallet_routes.py`

Update `WalletAddressResponse`:
```python
class WalletAddressResponse(BaseModel):
    multiplier: int
    chance: float
    address: str
    label: str
    is_active: bool
    network: str
    min_bet_sats: Optional[int] = None  # NEW
    max_bet_sats: Optional[int] = None  # NEW
```

Update `get_wallet_address()` and `get_all_wallets()`:
- Fetch `min_bet_sats` and `max_bet_sats` from wallet document
- If `None`, use global config values:
  ```python
  min_bet = wallet.get("min_bet_sats") or config.MIN_BET_SATOSHIS
  max_bet = wallet.get("max_bet_sats") or config.MAX_BET_SATOSHIS
  ```
- Return in response

#### 1.6 Bet Validation
**File**: `backend/app/services/bet_service.py`

Update bet validation in `process_detected_transaction()`:
- Get wallet's `min_bet_sats` and `max_bet_sats`
- Use wallet-specific limits if available, otherwise global limits
- Validate bet amount against wallet-specific range

### Phase 2: Admin Frontend Changes

#### 2.1 Wallet Modal Component
**File**: `admin_frontend/src/components/WalletModal.js`

Add input fields:
```jsx
<div className="form-group">
  <label>Min Bet (Satoshis)</label>
  <input
    type="number"
    value={minBetSats}
    onChange={(e) => setMinBetSats(e.target.value ? parseInt(e.target.value) : '')}
    placeholder="Leave empty for global default"
    min="1"
  />
  <small>Minimum bet amount for this multiplier (in satoshis)</small>
</div>

<div className="form-group">
  <label>Max Bet (Satoshis)</label>
  <input
    type="number"
    value={maxBetSats}
    onChange={(e) => setMaxBetSats(e.target.value ? parseInt(e.target.value) : '')}
    placeholder="Leave empty for global default"
    min="1"
  />
  <small>Maximum bet amount for this multiplier (in satoshis)</small>
</div>
```

Validation:
- If both provided: `minBetSats < maxBetSats`
- Show BTC equivalent (satoshis / 100000000)
- Allow empty (will use global defaults)

#### 2.2 Wallet Grid Component
**File**: `admin_frontend/src/components/WalletGrid.js`

Add columns to table:
- "Min Bet" column (show BTC if available, else "Default")
- "Max Bet" column (show BTC if available, else "Default")

#### 2.3 API Service
**File**: `admin_frontend/src/services/api.js`

Update functions:
- `generateWallet()`: Include `min_bet_sats`, `max_bet_sats` in request
- `updateWallet()`: Include `min_bet_sats`, `max_bet_sats` in request
- `getAllWallets()`: Response will include new fields

### Phase 3: Main Frontend Changes

#### 3.1 Wallet Data Structure
**File**: `satoshi-dice-main/src/app/page.js`

Update state and data handling:
```javascript
// When wallets are fetched, store bet ranges
const [walletBetRanges, setWalletBetRanges] = useState({});

// Update when wallets are loaded
useEffect(() => {
  if (wallets.length > 0) {
    const ranges = {};
    wallets.forEach(wallet => {
      ranges[wallet.multiplier] = {
        min: wallet.min_bet_sats ? wallet.min_bet_sats / SATOSHIS_PER_BTC : minBet,
        max: wallet.max_bet_sats ? wallet.max_bet_sats / SATOSHIS_PER_BTC : maxBet
      };
    });
    setWalletBetRanges(ranges);
  }
}, [wallets, minBet, maxBet]);
```

#### 3.2 Dynamic Bet Limits
**File**: `satoshi-dice-main/src/app/page.js`

Update bet amount logic:
```javascript
// Get current wallet's bet range
const getCurrentBetRange = () => {
  if (!selectedWallet) return { min: minBet, max: maxBet };
  const range = walletBetRanges[selectedWallet.multiplier];
  return range || { min: minBet, max: maxBet };
};

// Update bet amount when multiplier changes
useEffect(() => {
  const range = getCurrentBetRange();
  // Clamp current bet amount to new range
  const clamped = Math.max(range.min, Math.min(range.max, betAmount));
  setBetAmount(clamped);
  setMinBet(range.min);
  setMaxBet(range.max);
}, [selectedWallet, walletBetRanges]);
```

#### 3.3 QR Code with Bet Amount
**File**: `satoshi-dice-main/src/app/page.js`

Update QR code generation:
```javascript
// Generate QR code data with bet amount
const getQRCodeData = () => {
  const betAmountSats = Math.round(betAmount * SATOSHIS_PER_BTC);
  // Format: "bitcoin:ADDRESS?amount=BTC_AMOUNT"
  return `bitcoin:${walletAddress}?amount=${betAmount.toFixed(8)}`;
};

// In JSX:
<QRCode
  value={getQRCodeData()}
  size={200}
  // ... other props
/>
```

**Alternative**: If using `react-qrcode-logo`, ensure it supports the `value` prop with Bitcoin URI format.

#### 3.4 Display Bet Amount in QR Section
**File**: `satoshi-dice-main/src/app/page.js`

Add bet amount display near QR code:
```jsx
<div className="qr-section">
  <QRCode value={getQRCodeData()} size={200} />
  <div className="bet-amount-display">
    <p className="label">Bet Amount</p>
    <p className="amount">{formatBTC(betAmount)} BTC</p>
    <p className="sats">({Math.round(betAmount * SATOSHIS_PER_BTC)} sats)</p>
  </div>
</div>
```

### Phase 4: API Updates

#### 4.1 Wallet API Response
**Endpoint**: `GET /api/wallets/all` and `GET /api/wallets/address/{multiplier}`

Response format:
```json
{
  "multiplier": 2,
  "chance": 49.5,
  "address": "tb1...",
  "min_bet_sats": 10000,  // NEW
  "max_bet_sats": 100000000  // NEW
}
```

If `min_bet_sats` or `max_bet_sats` is `null`, frontend should use global defaults.

### Phase 5: Testing Checklist

- [ ] Admin can set min/max bet for each multiplier
- [ ] Admin can leave fields empty (uses global defaults)
- [ ] Admin can update bet ranges for existing wallets
- [ ] Frontend displays correct bet range for selected multiplier
- [ ] Bet amount slider adjusts when multiplier changes
- [ ] QR code includes bet amount in Bitcoin URI format
- [ ] Bet amount is displayed near QR code
- [ ] Bet validation uses wallet-specific limits
- [ ] Backward compatibility: wallets without ranges use global defaults
- [ ] BTC conversion displays correctly (satoshis ↔ BTC)

## Implementation Order

1. **Backend Database & Models** (Phase 1.1)
2. **Admin Backend DTOs & Services** (Phase 1.2-1.4)
3. **Main Backend Wallet Routes** (Phase 1.5)
4. **Bet Validation** (Phase 1.6)
5. **Admin Frontend** (Phase 2)
6. **Main Frontend** (Phase 3)
7. **Testing** (Phase 5)

## Notes

- **Backward Compatibility**: All new fields are optional. Existing wallets without bet ranges will use global defaults.
- **Validation**: Ensure `min_bet_sats < max_bet_sats` when both are provided.
- **QR Code Format**: Bitcoin URI format: `bitcoin:ADDRESS?amount=BTC_AMOUNT`
- **Display**: Show bet amount in both BTC and satoshis for clarity.
- **Default Behavior**: If wallet has no custom range, use global `MIN_BET_SATOSHIS` / `MAX_BET_SATOSHIS`.
