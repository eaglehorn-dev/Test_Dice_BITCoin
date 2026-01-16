# Recent Games WebSocket Integration Plan

## Overview
Replace the REST API polling for recent games with WebSocket real-time updates. The recent games section should show only the last 3 bets and update in real-time when new bets are processed.

## Current Implementation

### Backend
- **WebSocket Endpoint**: `/ws` and `/ws/bets` (FastAPI WebSocket)
- **WebSocket Manager**: `ConnectionManager` in `app/utils/websocket_manager.py`
- **Bet Broadcasting**: Already implemented in `bet_service.py` and `mempool_websocket.py`
- **Message Format**: `{"type": "new_bet", "bet": {...}}`

### Frontend (Current)
- **Data Fetching**: REST API call to `/api/bets/recent?limit=3` on component mount
- **Display**: Shows last 3 bets from API response
- **Updates**: No real-time updates (static data)

## Proposed Changes

### Backend Changes

#### 1. Verify Bet Broadcast Data Structure
**File**: `backend/app/services/bet_service.py` and `backend/app/utils/mempool_websocket.py`

**Current Broadcast Format**:
```python
{
    "type": "new_bet",
    "bet": {
        "bet_id": "...",
        "bet_number": 123,
        "user_address": "...",
        "bet_amount": 100000,
        "multiplier": 2,
        "roll_result": 1234,
        "is_win": True,
        "payout_amount": 200000,
        "profit": 100000,
        "created_at": "...",
        ...
    }
}
```

**Action**: Verify that the broadcast includes all fields needed for recent games display:
- ✅ `bet_id` or `bet_number` (for display)
- ✅ `bet_amount` (in satoshis)
- ✅ `payout_amount` (in satoshis)
- ✅ `is_win` (boolean)
- ✅ `roll_result` (for display)
- ✅ `created_at` (timestamp)

**Status**: Already includes all necessary fields ✅

#### 2. Ensure Broadcast Happens After Bet Processing
**File**: `backend/app/services/bet_service.py`

**Current Flow**:
1. Bet is processed and stored
2. Payout is executed (if win)
3. Bet result is broadcast via WebSocket

**Action**: Verify broadcast happens after `payout_txid` is stored (already implemented ✅)

### Frontend Changes

#### 1. Create WebSocket Hook/Utility
**File**: `satoshi-dice-main/src/utils/websocket.js` (NEW FILE)

**Purpose**: Centralized WebSocket connection management with auto-reconnection

**Features**:
- Connect to `/ws` or `/ws/bets` endpoint
- Auto-reconnection with exponential backoff
- Ping/pong heartbeat to keep connection alive
- Event handlers for different message types
- Cleanup on component unmount

**Structure**:
```javascript
export const useWebSocket = (url, onMessage, onError, onConnect) => {
  const [ws, setWs] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const pingIntervalRef = useRef(null);
  
  // Connection logic
  // Auto-reconnection logic
  // Ping/pong logic
  // Cleanup logic
};
```

#### 2. Update Main Page Component
**File**: `satoshi-dice-main/src/app/page.js`

**Changes Required**:

**A. Remove REST API Call for Recent Bets**
- Remove `getRecentBets()` call from `fetchData()`
- Remove `recentBets` state initialization from REST API

**B. Add WebSocket Connection**
- Import WebSocket utility/hook
- Connect to WebSocket on component mount
- Handle `new_bet` messages
- Update `recentBets` state when new bet arrives

**C. Maintain Last 3 Bets**
- Keep only the last 3 bets in state
- When a new bet arrives:
  1. Add it to the beginning of the array
  2. Keep only the first 3 items
  3. Update UI automatically

**D. State Management**
```javascript
const [recentBets, setRecentBets] = useState([]); // Max 3 items
const [wsConnected, setWsConnected] = useState(false);

// WebSocket message handler
const handleBetMessage = (message) => {
  if (message.type === 'new_bet' && message.bet) {
    setRecentBets(prev => {
      // Add new bet at the beginning
      const updated = [message.bet, ...prev];
      // Keep only last 3
      return updated.slice(0, 3);
    });
  }
};
```

**E. Connection Status Indicator (Optional)**
- Show connection status in UI
- Display "Reconnecting..." when disconnected
- Show green indicator when connected

#### 3. WebSocket Message Format Handling

**Expected Message Format**:
```json
{
  "type": "new_bet",
  "bet": {
    "bet_id": "507f1f77bcf86cd799439011",
    "bet_number": 123,
    "user_address": "tb1q...",
    "bet_amount": 100000,
    "multiplier": 2,
    "roll_result": 1234,
    "is_win": true,
    "payout_amount": 200000,
    "profit": 100000,
    "created_at": "2024-01-01T12:00:00Z",
    "payout_txid": "abc123...",
    "deposit_txid": "def456..."
  }
}
```

**Transformation**:
```javascript
const transformBetForDisplay = (bet) => {
  return {
    result: bet.is_win ? 'win' : 'lose',
    betAmount: formatBetAmount(bet.bet_amount),
    betAmountSat: bet.bet_amount,
    payoutAmount: bet.is_win ? formatBetAmount(bet.payout_amount) : '0.00000000',
    payoutAmountSat: bet.is_win ? bet.payout_amount : 0,
    bet: bet.bet_number || bet.bet_id?.slice(-8) || 'N/A',
    roll: bet.roll_result || 'N/A'
  };
};
```

#### 4. Initial Data Loading

**Option A**: Fetch initial 3 bets via REST API, then switch to WebSocket
- Pros: Users see data immediately
- Cons: Two data sources (REST + WebSocket)

**Option B**: Wait for WebSocket connection, then request initial data
- Pros: Single data source
- Cons: Users see empty state until first bet arrives

**Recommendation**: **Option A** - Fetch initial 3 bets via REST API on mount, then use WebSocket for real-time updates. This provides the best user experience.

#### 5. Error Handling

**Scenarios to Handle**:
1. **WebSocket Connection Failure**
   - Show error message
   - Attempt reconnection
   - Fallback to REST API polling (optional)

2. **WebSocket Disconnection**
   - Auto-reconnect with exponential backoff
   - Show "Reconnecting..." indicator
   - Keep existing bets visible

3. **Invalid Message Format**
   - Log error
   - Ignore invalid messages
   - Continue processing valid messages

4. **Component Unmount During Connection**
   - Clean up WebSocket connection
   - Clear reconnection timers
   - Clear ping intervals

## Implementation Steps

### Phase 1: Backend Verification
1. ✅ Verify bet broadcast includes all necessary fields
2. ✅ Verify broadcast happens after bet processing completes
3. ✅ Test WebSocket endpoint is accessible

### Phase 2: Frontend WebSocket Utility
1. Create `src/utils/websocket.js` with connection management
2. Implement auto-reconnection logic
3. Implement ping/pong heartbeat
4. Add error handling

### Phase 3: Frontend Integration
1. Remove REST API call for recent bets (or keep for initial load)
2. Add WebSocket connection on component mount
3. Handle `new_bet` messages
4. Update `recentBets` state (max 3 items)
5. Transform bet data for display
6. Add connection status indicator (optional)

### Phase 4: Testing
1. Test WebSocket connection
2. Test real-time updates when new bet is processed
3. Test auto-reconnection on disconnect
4. Test component cleanup on unmount
5. Test with multiple simultaneous bets
6. Test error handling

## Files to Create/Modify

### New Files:
1. `satoshi-dice-main/src/utils/websocket.js` - WebSocket connection utility

### Modified Files:
1. `satoshi-dice-main/src/app/page.js` - Add WebSocket integration
2. `satoshi-dice-main/src/utils/api.js` - (Optional) Keep `getRecentBets` for initial load

## Code Structure Preview

### WebSocket Utility (`src/utils/websocket.js`):
```javascript
import { useEffect, useRef, useState } from 'react';

export const useWebSocket = (url, onMessage, onError, onConnect) => {
  const [ws, setWs] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const pingIntervalRef = useRef(null);
  const shouldReconnect = useRef(true);
  
  const connect = () => {
    // WebSocket connection logic
    // Auto-reconnection logic
    // Ping/pong logic
  };
  
  useEffect(() => {
    connect();
    return () => {
      shouldReconnect.current = false;
      // Cleanup
    };
  }, [url]);
  
  return { ws, isConnected };
};
```

### Main Page Integration (`src/app/page.js`):
```javascript
import { useWebSocket } from '@/utils/websocket';

// In component:
const handleBetMessage = (message) => {
  if (message.type === 'new_bet' && message.bet) {
    setRecentBets(prev => {
      const transformed = transformBetForDisplay(message.bet);
      return [transformed, ...prev].slice(0, 3);
    });
  }
};

const { isConnected } = useWebSocket(
  `${process.env.NEXT_PUBLIC_API_URL?.replace('http', 'ws')}/ws/bets`,
  handleBetMessage,
  (error) => console.error('WebSocket error:', error),
  () => console.log('WebSocket connected')
);
```

## Key Considerations

### 1. **WebSocket URL**
- Convert HTTP URL to WebSocket URL: `http://localhost:8000` → `ws://localhost:8000`
- Handle both `ws://` and `wss://` (secure) protocols
- Use environment variable: `NEXT_PUBLIC_WS_URL` or derive from `NEXT_PUBLIC_API_URL`

### 2. **Message Ordering**
- New bets should appear at the top
- Maintain chronological order (newest first)
- Limit to 3 items maximum

### 3. **Performance**
- Only update state when new bet arrives
- Use React's state batching for multiple rapid updates
- Avoid unnecessary re-renders

### 4. **User Experience**
- Show loading state while connecting
- Show connection status indicator
- Keep existing bets visible during reconnection
- Smooth transitions when new bets arrive

### 5. **Backward Compatibility**
- Keep REST API endpoint for initial load (optional)
- Handle cases where WebSocket is not available
- Graceful degradation to REST API polling

## Expected Outcome

After implementation:
- Recent games section shows last 3 bets
- Updates in real-time via WebSocket
- No REST API polling needed (or only for initial load)
- Auto-reconnection on disconnect
- Smooth user experience with live updates
- Connection status visible to users

## Testing Checklist

- [ ] WebSocket connects successfully
- [ ] Recent games update in real-time when new bet is processed
- [ ] Only last 3 bets are displayed
- [ ] New bets appear at the top
- [ ] Auto-reconnection works on disconnect
- [ ] Component cleanup works on unmount
- [ ] Error handling works correctly
- [ ] Connection status indicator works
- [ ] Multiple rapid bets are handled correctly
- [ ] Initial data load works (if using REST API)

## Notes

1. **Initial Load**: Consider fetching initial 3 bets via REST API for immediate display, then switching to WebSocket for updates.

2. **Connection Management**: Use a custom hook or utility to manage WebSocket connections, ensuring proper cleanup and reconnection.

3. **Message Format**: Ensure backend broadcast format matches frontend expectations. Verify all required fields are included.

4. **Performance**: Limit state updates to only when necessary. Use React's optimization techniques to prevent unnecessary re-renders.

5. **Error Handling**: Implement robust error handling for connection failures, invalid messages, and edge cases.
