# Main Page API Integration Plan

## Overview
Connect the Next.js main game page (`src/app/page.js`) to the backend API to replace all hardcoded data with real backend data. This includes multipliers, wallet addresses, chances, bet limits, and recent games.

## Current Hardcoded Data

### 1. Multipliers Array (Lines 16-28)
```javascript
const multipliers = [
  { label: "1000x", chance: "0.10%" },
  { label: "100x", chance: "0.97%" },
  // ... 11 hardcoded multipliers
];
```

### 2. Deposit Address (Lines 435, 440, 445)
- Hardcoded Bitcoin Cash address: `qz9cq5yfkyjpgq6xatlr6veyhmcartkyrg7wev9jzc`
- Uses `bitcoincash:` prefix
- Static QR code value

### 3. Currency (Line 37)
- Hardcoded: `'BCH'` (Bitcoin Cash)
- Should be `'BTC'` (Bitcoin)

### 4. Bet Amount Section (Lines 35-349)
- **Bet Limits**: Hardcoded `minBet = 0.001`, `maxBet = 7.5` (in BTC/BCH)
- **Currency**: Hardcoded `'BCH'` (should be `'BTC'`)
- **USD Rate**: Hardcoded `usdRate = 586.1` (should be removed or fetched)
- **Bet Slider**: Uses hardcoded min/max values
- **Game Info**: Shows hardcoded min/max bet values
- **Should fetch from**: `/api/stats/house` endpoint

### 5. USD Rate (Line 40)
- Hardcoded: `usdRate = 586.1`
- Should be fetched from backend or removed (as per previous decisions)

### 6. Total Bets Counter (Lines 357-371)
- Hardcoded: `["9", ",", "0", "9", "8", ",", "8", "3", "2"]`
- Should fetch from stats API

### 7. Recent Games (Lines 379-423)
- Hardcoded mock data (3 items)
- Should fetch from `/api/bets/recent`

## Backend API Endpoints Available

### 1. Get All Wallets
**Endpoint**: `GET /api/wallets/all`

**Response**:
```json
[
  {
    "multiplier": 2,
    "chance": 48.5,
    "address": "tb1q...",
    "label": "2x Wallet",
    "is_active": true,
    "network": "testnet"
  },
  // ... more wallets
]
```

### 2. Get Wallet Address for Multiplier
**Endpoint**: `GET /api/wallets/address/{multiplier}`

**Response**:
```json
{
  "multiplier": 2,
  "chance": 48.5,
  "address": "tb1q...",
  "label": "2x Wallet",
  "is_active": true,
  "network": "testnet"
}
```

### 3. Get Recent Bets (Optional)
**Endpoint**: `GET /api/bets/recent?limit=3`

**Response**:
```json
{
  "bets": [
    {
      "bet_id": "...",
      "bet_number": 123,
      "user_address": "...",
      "multiplier": 2,
      "result": "win",
      "bet_amount": 100000,
      "payout_amount": 200000,
      "roll": 1234,
      "created_at": "..."
    }
  ]
}
```

### 4. Get House Info (Bet Limits & Config)
**Endpoint**: `GET /api/stats/house`

**Response**:
```json
{
  "network": "testnet",
  "house_edge": 0.02,
  "min_bet": 600,           // in satoshis
  "max_bet": 1000000,       // in satoshis
  "min_multiplier": 1.1,
  "max_multiplier": 98.0,
  "vault_system": {
    "total_wallets": 5,
    "available_multipliers": [2, 3, 5, 10, 100],
    "wallets": [...]
  }
}
```

**Key Values**:
- `min_bet`: Minimum bet in **satoshis** (need to convert to BTC: divide by 100,000,000)
- `max_bet`: Maximum bet in **satoshis** (need to convert to BTC: divide by 100,000,000)
- `network`: Current network (testnet/mainnet)

### 5. Get Stats (Optional - for Total Bets)
**Endpoint**: `GET /api/stats/game`

**Response**:
```json
{
  "total_bets": 9098832,
  "total_wagered": 123456789,
  "total_payouts": 98765432,
  "win_rate": 48.5
}
```

## Implementation Steps

### Step 1: Update API Utility File
**File**: `satoshi-dice-main/src/utils/api.js`

**Add Functions**:
- `getAllWallets()` - Fetch all wallets
- `getWalletAddress(multiplier)` - Fetch address for specific multiplier
- `getHouseInfo()` - Fetch bet limits and game configuration
- `getRecentBets(limit)` - Fetch recent bets (optional)
- `getStats()` - Fetch game stats (optional)

### Step 2: Update Main Page Component
**File**: `satoshi-dice-main/src/app/page.js`

**Changes Required**:

1. **Add State Management**:
   - `wallets` state (replaces hardcoded `multipliers`)
   - `selectedWallet` state (current selected wallet)
   - `walletAddress` state (current address for QR code)
   - `minBet` state (from API, in BTC)
   - `maxBet` state (from API, in BTC)
   - `houseInfo` state (game configuration)
   - `loading` state
   - `error` state
   - `recentBets` state (optional)
   - `totalBets` state (optional)

2. **Add useEffect Hook**:
   - Fetch house info (bet limits) on component mount
   - Fetch all wallets on component mount
   - Set default selected wallet (first wallet or based on `selectedIndex`)
   - Fetch wallet address for selected multiplier
   - Optionally fetch recent bets and stats

3. **Transform API Response**:
   - Convert wallet data to match current UI structure
   - Format chance from decimal (48.5) to percentage string ("48.50%")
   - Map multiplier to label format ("2x", "3x", etc.)

4. **Update Multiplier Selection**:
   - When user selects multiplier, fetch/get wallet address
   - Update QR code with new address
   - Update address display

5. **Replace Hardcoded Values**:
   - Replace `multipliers` array with `wallets` from API
   - Replace hardcoded address with `walletAddress` from API
   - Replace `'BCH'` with `'BTC'` (or remove currency toggle if not needed)
   - Replace hardcoded `minBet` and `maxBet` with values from `/api/stats/house`
   - Convert satoshis to BTC (divide by 100,000,000)
   - Update bet slider to use dynamic min/max values
   - Update "Game Info" section to show dynamic min/max bet values
   - Replace hardcoded total bets with API data
   - Replace hardcoded recent games with API data

6. **Update QR Code**:
   - Change from `bitcoincash:` prefix to `bitcoin:` or remove prefix
   - Use dynamic `walletAddress` instead of hardcoded value

7. **Update Address Display**:
   - Show dynamic address from selected wallet
   - Update copy button to use dynamic address

### Step 3: Data Transformation Logic

**Current Structure**:
```javascript
{
  label: "2x",
  chance: "48.50%"
}
```

**API Response Structure**:
```javascript
{
  multiplier: 2,
  chance: 48.5,  // decimal, not percentage string
  address: "tb1q...",
  label: "2x Wallet",
  is_active: true,
  network: "testnet"
}
```

**Transformation**:
```javascript
const transformedWallets = apiWallets.map(wallet => ({
  label: `${wallet.multiplier}x`,
  chance: `${wallet.chance.toFixed(2)}%`,
  multiplier: wallet.multiplier,
  address: wallet.address,
  is_active: wallet.is_active
}));
```

### Step 4: Handle Multiplier Selection

**Current Behavior**:
- User selects multiplier by index
- Hardcoded address is always shown

**New Behavior**:
- User selects multiplier by index
- Find corresponding wallet from `wallets` array
- If wallet exists, use its address
- If not found, fetch address via `getWalletAddress(multiplier)`
- Update QR code and address display

### Step 5: Update Currency References

**Changes**:
- Change `'BCH'` to `'BTC'` throughout
- Update text: "Send BCH to Play" → "Send BTC to Play"
- Update address prefix: `bitcoincash:` → `bitcoin:` (or remove)
- Consider removing currency toggle if BTC-only

### Step 6: Bet Amount Section Integration

**API Endpoint**: `GET /api/stats/house`

**Implementation**:
1. Fetch house info on component mount
2. Extract `min_bet` and `max_bet` (in satoshis)
3. Convert to BTC: `minBetBTC = min_bet / 100000000`, `maxBetBTC = max_bet / 100000000`
4. Update state: `setMinBet(minBetBTC)`, `setMaxBet(maxBetBTC)`
5. Update bet slider to use dynamic values
6. Update "Game Info" display to show dynamic values
7. Remove hardcoded `usdRate` (or fetch from API if needed)

**Satoshis to BTC Conversion**:
```javascript
const SATOSHIS_PER_BTC = 100000000;
const minBetBTC = houseInfo.min_bet / SATOSHIS_PER_BTC;  // 600 / 100000000 = 0.000006
const maxBetBTC = houseInfo.max_bet / SATOSHIS_PER_BTC;  // 1000000 / 100000000 = 0.01
```

**Note**: Backend returns values in satoshis, but frontend displays in BTC. Conversion is required.

### Step 7: Recent Games Integration (Optional)

**If Implementing**:
- Fetch from `/api/bets/recent?limit=3`
- Transform to match current UI structure
- Handle loading/error states
- Format amounts (satoshis to BTC)
- Format dates

### Step 8: Total Bets Integration (Optional)

**If Implementing**:
- Fetch from `/api/stats`
- Extract `total_bets`
- Format number with commas
- Update display

## Files to Create/Modify

### Modified Files:
1. `satoshi-dice-main/src/utils/api.js` - Add wallet API functions
2. `satoshi-dice-main/src/app/page.js` - Main integration changes

### No New Files Required

## Code Structure Preview

### API Utility Functions (`src/utils/api.js`):
```javascript
export const getAllWallets = async () => {
  const response = await api.get('/api/wallets/all');
  return response.data;
};

export const getWalletAddress = async (multiplier) => {
  const response = await api.get(`/api/wallets/address/${multiplier}`);
  return response.data;
};

export const getHouseInfo = async () => {
  const response = await api.get('/api/stats/house');
  return response.data;
};

export const getRecentBets = async (limit = 3) => {
  const response = await api.get('/api/bets/recent', { params: { limit } });
  return response.data;
};

export const getStats = async () => {
  const response = await api.get('/api/stats/game');
  return response.data;
};
```

### Updated Page Component Structure:
```javascript
export default function App() {
  const [wallets, setWallets] = useState([]);
  const [selectedWallet, setSelectedWallet] = useState(null);
  const [walletAddress, setWalletAddress] = useState('');
  const [minBet, setMinBet] = useState(0.001);  // Default, will be updated from API
  const [maxBet, setMaxBet] = useState(7.5);    // Default, will be updated from API
  const [houseInfo, setHouseInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  
  const SATOSHIS_PER_BTC = 100000000;
  
  useEffect(() => {
    fetchHouseInfo();
    fetchWallets();
  }, []);
  
  useEffect(() => {
    if (wallets.length > 0 && selectedIndex < wallets.length) {
      const wallet = wallets[selectedIndex];
      setSelectedWallet(wallet);
      setWalletAddress(wallet.address);
    }
  }, [selectedIndex, wallets]);
  
  const fetchHouseInfo = async () => {
    try {
      const data = await getHouseInfo();
      setHouseInfo(data);
      // Convert satoshis to BTC
      setMinBet(data.min_bet / SATOSHIS_PER_BTC);
      setMaxBet(data.max_bet / SATOSHIS_PER_BTC);
    } catch (err) {
      console.error('Failed to fetch house info:', err);
      // Keep default values on error
    }
  };
  
  const fetchWallets = async () => {
    // Fetch and transform wallets
  };
  
  // Transform wallets to match UI structure
  const multipliers = wallets.map(w => ({
    label: `${w.multiplier}x`,
    chance: `${w.chance.toFixed(2)}%`,
    multiplier: w.multiplier
  }));
  
  // Update QR code to use walletAddress
  // Update address display
  // Update currency references
  // Bet slider now uses minBet and maxBet from state
  // Game Info section shows minBet and maxBet from state
}
```

## Key Considerations

### 1. **Bitcoin Cash vs Bitcoin**
- Current frontend uses BCH addresses and `bitcoincash:` prefix
- Backend uses BTC addresses
- **Action**: Change all BCH references to BTC, remove `bitcoincash:` prefix

### 2. **Multiplier Format**
- Backend returns integer multipliers (2, 3, 5, etc.)
- Frontend expects formatted labels ("2x", "3x", etc.)
- **Action**: Transform in component

### 3. **Chance Format**
- Backend returns decimal (48.5)
- Frontend expects percentage string ("48.50%")
- **Action**: Format in component

### 4. **Address Format**
- Backend returns Bitcoin address (testnet or mainnet)
- Frontend currently expects Bitcoin Cash address
- **Action**: Use address as-is, remove `bitcoincash:` prefix from QR code

### 5. **Loading States**
- Add loading spinner while fetching wallets
- Show error message if fetch fails
- Disable multiplier selection until wallets load

### 6. **Error Handling**
- Handle case where no wallets exist
- Handle case where selected multiplier has no wallet
- Graceful fallback for missing data

## Testing Checklist

- [ ] Wallets load correctly on page mount
- [ ] Multipliers display with correct labels and chances
- [ ] Selecting multiplier updates address and QR code
- [ ] QR code shows correct Bitcoin address
- [ ] Address copy button works
- [ ] Currency references changed from BCH to BTC
- [ ] Loading state displays properly
- [ ] Error handling works (test with wrong API URL)
- [ ] Empty state works (if no wallets)
- [ ] Recent games load (if implemented)
- [ ] Total bets display (if implemented)

## Dependencies

No new dependencies required - `axios` is already installed.

## Notes

1. **CORS**: Ensure backend CORS allows requests from Next.js frontend origin
2. **Error Handling**: Implement graceful error handling for network issues
3. **Performance**: Consider caching wallets to avoid repeated API calls
4. **Real-time Updates**: Consider WebSocket for real-time bet updates (future enhancement)
5. **Bet Limits**: Backend doesn't currently expose min/max bet via API - may need to add endpoint or use constants

## Expected Outcome

After implementation:
- Page fetches real wallet data from backend
- Multipliers and chances come from database
- QR code and address update dynamically based on selected multiplier
- Bet amount section uses dynamic min/max values from backend
- Bet slider adjusts to backend bet limits
- Game Info section shows real bet limits
- All BCH references changed to BTC
- Recent games show real data (if implemented)
- Total bets counter shows real data (if implemented)
- Loading and error states handled gracefully
- Maintains existing UI design and layout

## Implementation Priority

### Phase 1 (Essential):
1. Fetch house info (bet limits) from API
2. Convert satoshis to BTC and update bet amount section
3. Fetch wallets from API
4. Replace hardcoded multipliers array
5. Update address and QR code dynamically
6. Change BCH to BTC references
7. Update bet slider to use dynamic min/max values
8. Update Game Info section with dynamic bet limits

### Phase 2 (Optional):
1. Integrate recent games
2. Integrate total bets counter
3. Remove or fetch USD rate (if needed)
