# Provably Fair Page API Integration Plan

## Overview
Connect the Next.js provably fair page (`src/app/fair/page.js`) to the backend API endpoint `/api/fairness/seeds` to display real server seed data instead of hardcoded values.

## Backend API Endpoint

**Endpoint**: `GET /api/fairness/seeds`

**Response Structure**:
```json
{
  "seeds": [
    {
      "seed_id": "string",
      "seed_date": "2026-01-18",  // ISO date format
      "server_seed_hash": "string",
      "server_seed": "string" | null,  // null for today/future dates
      "bet_count": 0,
      "created_at": "ISO timestamp"
    }
  ],
  "today": "2026-01-18",
  "three_days_later": "2026-01-21"
}
```

**Key Logic**:
- `server_seed` is `null` for today and future dates (shows "Not Published")
- `server_seed` contains the actual key for past dates
- Seeds are sorted by date (newest first)
- Shows seeds from past dates up to 3 days in the future

## Implementation Steps

### Step 1: Create API Utility File
**File**: `satoshi-dice-main/src/utils/api.js`

**Purpose**: Centralized API client for Next.js (similar to existing React frontend)

**Content**:
- Create axios instance with base URL from environment variable
- Export `getFairnessSeeds()` function
- Handle errors appropriately

**Environment Variable Needed**:
- `NEXT_PUBLIC_API_URL` (e.g., `http://localhost:8000` or `http://95.216.67.104:8000`)

### Step 2: Update Provably Fair Page
**File**: `satoshi-dice-main/src/app/fair/page.js`

**Changes Required**:

1. **Add State Management**:
   - `seeds` state (replaces hardcoded `fairGames`)
   - `loading` state
   - `error` state

2. **Add useEffect Hook**:
   - Fetch data on component mount
   - Call `getFairnessSeeds()` from API utility
   - Handle loading and error states

3. **Transform API Response**:
   - Convert API response format to match current UI structure
   - Format dates from ISO (`2026-01-18`) to display format (`Jan 18, 2026`)
   - Map `server_seed_hash` → `serverSeed`
   - Map `server_seed` → `plaintext` (or "Not Published" if null)

4. **Date Formatting Function**:
   - Convert ISO date string to readable format
   - Example: `"2026-01-18"` → `"Jan 18, 2026"`

5. **Update FairTable Component**:
   - Accept `seeds` prop instead of `fairGames`
   - Handle loading state (show spinner/skeleton)
   - Handle error state (show error message)
   - Display empty state if no seeds

### Step 3: Data Transformation Logic

**Current Structure** (hardcoded):
```javascript
{
  date: "Jan 18, 2026",
  serverSeed: "c40e8d949dc5d302ed95d6d58cd946525c449f18c9bd2cebef01ed8052dd8f6b5a",
  plaintext: "Not Published" | "actual_key_string"
}
```

**API Response Structure**:
```javascript
{
  seed_date: "2026-01-18",
  server_seed_hash: "c40e8d949dc5d302ed95d6d58cd946525c449f18c9bd2cebef01ed8052dd8f6b5a",
  server_seed: null | "actual_key_string"
}
```

**Transformation**:
```javascript
const transformedSeeds = apiResponse.seeds.map(seed => ({
  date: formatDate(seed.seed_date),  // "2026-01-18" → "Jan 18, 2026"
  serverSeed: seed.server_seed_hash,
  plaintext: seed.server_seed || "Not Published"
}));
```

### Step 4: UI Enhancements

**Loading State**:
- Show skeleton loader or spinner while fetching
- Maintain table structure during loading

**Error State**:
- Display user-friendly error message
- Option to retry
- Fallback to empty state

**Empty State**:
- Show message if no seeds available
- Suggest checking back later

### Step 5: Environment Configuration

**File**: `.env.local` (create if doesn't exist)

**Content**:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Note**: For production, use your actual backend URL (e.g., `http://95.216.67.104:8000`)

## Files to Create/Modify

### New Files:
1. `satoshi-dice-main/src/utils/api.js` - API utility functions

### Modified Files:
1. `satoshi-dice-main/src/app/fair/page.js` - Connect to API, add state management

### Configuration:
1. `.env.local` - Add API URL (if not exists)

## Code Structure Preview

### API Utility (`src/utils/api.js`):
```javascript
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getFairnessSeeds = async () => {
  const response = await api.get('/api/fairness/seeds');
  return response.data;
};
```

### Updated Page Component Structure:
```javascript
"use client"
import { useState, useEffect } from 'react';
import { getFairnessSeeds } from '@/utils/api';
// ... existing imports

export default function ProvablyFairPage() {
  const [seeds, setSeeds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSeeds();
  }, []);

  const fetchSeeds = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getFairnessSeeds();
      // Transform data here
      setSeeds(transformedData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Date formatting function
  const formatDate = (isoDate) => { /* ... */ };

  // Render loading, error, or table
}
```

## Testing Checklist

- [ ] API endpoint is accessible from Next.js app
- [ ] Data loads correctly on page mount
- [ ] Dates are formatted correctly
- [ ] "Not Published" shows for today/future dates
- [ ] Real keys show for past dates
- [ ] Loading state displays properly
- [ ] Error handling works (test with wrong API URL)
- [ ] Empty state works (if no seeds)
- [ ] Table layout remains intact with real data

## Dependencies to Install

If `axios` is not already installed:
```bash
npm install axios
```

## Notes

1. **CORS**: Ensure backend CORS allows requests from Next.js frontend origin
2. **Error Handling**: Implement graceful error handling for network issues
3. **Date Formatting**: Use JavaScript `Date` object or a library like `date-fns` for consistent formatting
4. **Type Safety**: Consider adding TypeScript or PropTypes for better type safety
5. **Caching**: Consider adding client-side caching or SWR/React Query for better performance

## Expected Outcome

After implementation:
- Page fetches real server seed data from backend
- Displays seeds from past dates up to 3 days in the future
- Shows "Not Published" for today and future dates
- Shows actual server seed keys for past dates
- Handles loading and error states gracefully
- Maintains existing UI design and layout
