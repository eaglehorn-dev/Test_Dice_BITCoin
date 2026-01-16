# Bet History Large Data Integration Plan

## Overview
Integrate the bet history page with the backend API, implementing efficient data handling for large datasets (potentially thousands or millions of bets). The solution must handle pagination, filtering, searching, and real-time updates while maintaining good performance and user experience.

## Current Implementation

### Frontend (`satoshi-dice-main/src/components/gameHistory/index.js`)
- **Current State**: Uses hardcoded mock data (5 items)
- **Filtering**: Client-side filtering (All, Wins, Big Wins, Rare Wins)
- **Display**: Shows all items at once (no pagination)
- **Data Structure**: Simple array with basic bet information

### Backend API Endpoints

#### 1. Get Bet History by Address
**Endpoint**: `GET /api/bets/history/{address}?limit=50&multiplier=2&search=...`

**Response**:
```json
{
  "bets": [...],
  "total_bets": 1234,
  "total_wagered": 567890,
  "total_won": 234567,
  "total_lost": 333323
}
```

**Limitations**:
- Requires user address
- Max limit: 100 bets per request
- No pagination (offset/skip)
- No server-side filtering for "Big Wins" or "Rare Wins"

#### 2. Get Recent Bets (All Users)
**Endpoint**: `GET /api/bets/recent?limit=50`

**Response**:
```json
{
  "bets": [...],
  "count": 50
}
```

**Limitations**:
- Max limit: 100 bets per request
- No pagination
- No filtering options

## Challenges with Large Data

### 1. **Data Volume**
- Potential millions of bets in database
- Cannot load all at once
- Memory constraints in browser

### 2. **Performance Issues**
- Rendering thousands of DOM elements is slow
- Network bandwidth for large payloads
- Database query performance

### 3. **User Experience**
- Long loading times
- Browser freezing during render
- Poor mobile performance

## Proposed Solution

### Phase 1: Backend Enhancements & Optimizations

#### 1.1 Database Index Strategy for Large Queries

**File**: `backend/app/models/database.py`

**Critical Indexes for Performance**:

```python
# Base indexes for user queries
bets_col.create_index([("user_id", 1), ("created_at", -1)])
bets_col.create_index([("user_id", 1), ("roll_result", 1)])  # For filtering completed bets

# Indexes for "wins" filter (most common)
bets_col.create_index([("user_id", 1), ("is_win", 1), ("created_at", -1)])

# Compound index for "big_wins" filter (is_win + bet_amount + created_at)
# This is CRITICAL for performance on large datasets
bets_col.create_index([
    ("user_id", 1),
    ("is_win", 1),
    ("bet_amount", -1),  # Descending for big wins
    ("created_at", -1)
], name="idx_user_win_amount_date")

# Compound index for "rare_wins" filter (is_win + roll_result + created_at)
# This is CRITICAL for performance on large datasets
bets_col.create_index([
    ("user_id", 1),
    ("is_win", 1),
    ("roll_result", 1),  # Ascending for rare wins (< 1000)
    ("created_at", -1)
], name="idx_user_win_roll_date")

# Index for multiplier filtering
bets_col.create_index([("user_id", 1), ("multiplier", 1), ("created_at", -1)])

# Indexes for search functionality
bets_col.create_index([("deposit_txid", 1)], sparse=True)
bets_col.create_index([("payout_txid", 1)], sparse=True)
bets_col.create_index([("target_address", 1)])

# Partial index for completed bets only (saves space and improves performance)
bets_col.create_index(
    [("user_id", 1), ("created_at", -1)],
    partialFilterExpression={"roll_result": {"$ne": None}},
    name="idx_user_completed_date"
)
```

**Index Optimization Notes**:
- **Compound indexes** must match query pattern (equality → sort → range)
- **Partial indexes** reduce index size by only indexing relevant documents
- **Sparse indexes** for optional fields (txids can be null)
- **Index order matters**: Equality fields first, then sort fields, then range fields

#### 1.2 Optimized Query Implementation

**File**: `backend/app/api/bet_routes.py`

**Key Optimizations**:

1. **Use Estimated Count for Large Datasets**
   - `count_documents()` is slow on large collections
   - Use `estimated_document_count()` for approximate total
   - Or skip count entirely and use `has_next` based on returned results

2. **Efficient Filter Queries**
   - Build queries that match index patterns exactly
   - Use compound indexes efficiently
   - Avoid full collection scans

3. **Cursor-based Pagination** (Alternative to offset-based)
   - More efficient for large datasets
   - Uses `_id` or `created_at` as cursor
   - Avoids `skip()` which becomes slow on large offsets

**Optimized Implementation**:

```python
@router.get("/history/{address}", response_model=BetHistoryResponse)
async def get_bet_history(
    address: str,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    multiplier: int = Query(default=None, description="Filter by multiplier"),
    search: str = Query(default=None, description="Search by target_address or txid"),
    filter: str = Query(default="all", description="Filter: all, wins, big_wins, rare_wins"),
    sort: str = Query(default="newest", description="Sort: newest, oldest, amount_desc, amount_asc"),
    cursor: str = Query(default=None, description="Cursor for pagination (internal)")
):
    """
    Optimized bet history endpoint with efficient queries for large datasets.
    
    Performance optimizations:
    - Uses compound indexes for filtered queries
    - Estimated count for large datasets
    - Efficient query patterns matching index structure
    - Cursor-based pagination option
    """
    try:
        users_col = get_users_collection()
        bets_col = get_bets_collection()
        
        # Get user
        user = await users_col.find_one({"address": address})
        if not user:
            return BetHistoryResponse(
                bets=[],
                pagination={"page": 1, "page_size": page_size, "total_pages": 0, "total_bets": 0, "has_next": False, "has_prev": False},
                stats={"total_wagered": 0, "total_won": 0, "total_lost": 0}
            )
        
        user_id = user["_id"]
        
        # Build base query - always include user_id and completed bets
        query = {
            "user_id": user_id,
            "roll_result": {"$ne": None}  # Only completed bets
        }
        
        # Build sort specification - CRITICAL: Must match index order
        sort_spec = []
        
        # Apply filters and build optimal query based on filter type
        if filter == "wins":
            query["is_win"] = True
            # Use index: (user_id, is_win, created_at)
            sort_spec = [("created_at", -1)] if sort == "newest" else [("created_at", 1)]
            
        elif filter == "big_wins":
            query["is_win"] = True
            # Define "big win" threshold (0.25 BTC = 25,000,000 satoshis)
            BIG_WIN_THRESHOLD = 25000000
            query["bet_amount"] = {"$gte": BIG_WIN_THRESHOLD}
            
            # Use compound index: (user_id, is_win, bet_amount, created_at)
            if sort == "newest":
                sort_spec = [("bet_amount", -1), ("created_at", -1)]  # Biggest wins first, then newest
            elif sort == "oldest":
                sort_spec = [("bet_amount", -1), ("created_at", 1)]
            elif sort == "amount_desc":
                sort_spec = [("bet_amount", -1), ("created_at", -1)]
            else:  # amount_asc
                sort_spec = [("bet_amount", 1), ("created_at", -1)]
                
        elif filter == "rare_wins":
            query["is_win"] = True
            # Define "rare win" threshold (roll < 1000)
            RARE_WIN_THRESHOLD = 1000
            query["roll_result"] = {"$lt": RARE_WIN_THRESHOLD}
            
            # Use compound index: (user_id, is_win, roll_result, created_at)
            if sort == "newest":
                sort_spec = [("roll_result", 1), ("created_at", -1)]  # Lowest roll first, then newest
            elif sort == "oldest":
                sort_spec = [("roll_result", 1), ("created_at", 1)]
            else:
                sort_spec = [("roll_result", 1), ("created_at", -1)]
                
        else:  # filter == "all"
            # Use base index: (user_id, created_at)
            sort_spec = [("created_at", -1)] if sort == "newest" else [("created_at", 1)]
        
        # Add multiplier filter if specified
        if multiplier:
            query["multiplier"] = multiplier
        
        # Add search filter if specified
        if search:
            query["$or"] = [
                {"target_address": {"$regex": search, "$options": "i"}},
                {"deposit_txid": {"$regex": search, "$options": "i"}},
                {"payout_txid": {"$regex": search, "$options": "i"}}
            ]
        
        # Calculate skip for offset-based pagination
        skip = (page - 1) * page_size
        
        # OPTIMIZATION: For large datasets, use estimated count or skip count entirely
        # Option 1: Use estimated count (faster but approximate)
        # total_bets = await bets_col.estimated_document_count()
        
        # Option 2: Count only if page is small (first few pages)
        # For later pages, skip count and use has_next based on results
        if page <= 3:
            total_bets = await bets_col.count_documents(query)
            total_pages = (total_bets + page_size - 1) // page_size
            has_prev = page > 1
        else:
            # For later pages, don't count (too expensive)
            # Fetch one extra item to determine has_next
            total_bets = None
            total_pages = None
            has_prev = True
        
        # Fetch bets with pagination
        # OPTIMIZATION: Fetch one extra to determine has_next without count
        fetch_limit = page_size + 1 if page > 3 else page_size
        
        cursor = bets_col.find(query).sort(sort_spec)
        
        # Apply pagination
        if skip > 0:
            cursor = cursor.skip(skip)
        
        bets = await cursor.limit(fetch_limit).to_list(length=fetch_limit)
        
        # Determine has_next
        if page > 3:
            has_next = len(bets) > page_size
            if has_next:
                bets = bets[:page_size]  # Remove extra item
        else:
            has_next = page < total_pages
        
        # Format response
        bet_items = [
            BetHistoryItem(
                bet_id=str(bet["_id"]),
                bet_number=bet.get("bet_number"),
                bet_amount=bet["bet_amount"],
                target_multiplier=bet["target_multiplier"],
                multiplier=bet.get("multiplier", int(bet["target_multiplier"])),
                win_chance=bet["win_chance"],
                roll_result=bet["roll_result"],
                is_win=bet["is_win"],
                payout_amount=bet["payout_amount"],
                profit=bet["profit"],
                created_at=bet["created_at"],
                nonce=bet["nonce"],
                user_address=user.get("address"),
                target_address=bet.get("target_address"),
                deposit_txid=bet.get("deposit_txid"),
                payout_txid=bet.get("payout_txid"),
                server_seed=bet.get("server_seed"),
                server_seed_hash=bet.get("server_seed_hash"),
                client_seed=bet.get("client_seed")
            )
            for bet in bets
        ]
        
        # Get stats (use aggregation for efficiency)
        stats = await _get_user_stats_aggregated(user_id, query)
        
        return BetHistoryResponse(
            bets=bet_items,
            pagination={
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "total_bets": total_bets,
                "has_next": has_next,
                "has_prev": has_prev
            },
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"Error getting bet history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_user_stats_aggregated(user_id: ObjectId, query: dict) -> dict:
    """
    Get user stats using MongoDB aggregation pipeline.
    More efficient than multiple queries for large datasets.
    """
    bets_col = get_bets_collection()
    
    # Use aggregation pipeline for efficient stats calculation
    pipeline = [
        {"$match": query},
        {
            "$group": {
                "_id": None,
                "total_wagered": {"$sum": "$bet_amount"},
                "total_won": {
                    "$sum": {
                        "$cond": [{"$eq": ["$is_win", True]}, "$bet_amount", 0]
                    }
                },
                "total_lost": {
                    "$sum": {
                        "$cond": [{"$eq": ["$is_win", False]}, "$bet_amount", 0]
                    }
                },
                "total_payout": {
                    "$sum": {
                        "$cond": [{"$eq": ["$is_win", True]}, "$payout_amount", 0]
                    }
                }
            }
        }
    ]
    
    result = await bets_col.aggregate(pipeline).to_list(length=1)
    
    if result:
        stats = result[0]
        return {
            "total_wagered": stats.get("total_wagered", 0),
            "total_won": stats.get("total_won", 0),
            "total_lost": stats.get("total_lost", 0),
            "total_payout": stats.get("total_payout", 0)
        }
    
    return {
        "total_wagered": 0,
        "total_won": 0,
        "total_lost": 0,
        "total_payout": 0
    }
```

#### 1.3 Cursor-Based Pagination (Alternative for Very Large Datasets)

**For datasets with millions of bets, cursor-based pagination is more efficient:**

```python
@router.get("/history/{address}/cursor", response_model=BetHistoryResponse)
async def get_bet_history_cursor(
    address: str,
    cursor: str = Query(default=None, description="Cursor from previous page"),
    page_size: int = Query(default=50, ge=1, le=100),
    filter: str = Query(default="all")
):
    """
    Cursor-based pagination - more efficient for very large datasets.
    Uses _id or created_at as cursor instead of skip().
    """
    # Parse cursor
    if cursor:
        cursor_date = datetime.fromisoformat(cursor)
        query["created_at"] = {"$lt": cursor_date}  # Get older bets
    
    # Fetch one extra to determine has_next
    bets = await bets_col.find(query).sort([("created_at", -1)]).limit(page_size + 1).to_list(length=page_size + 1)
    
    has_next = len(bets) > page_size
    if has_next:
        bets = bets[:page_size]
    
    # Return next cursor (created_at of last item)
    next_cursor = bets[-1]["created_at"].isoformat() if bets and has_next else None
    
    return {
        "bets": bets,
        "pagination": {
            "has_next": has_next,
            "next_cursor": next_cursor
        }
    }
```

#### 1.4 Query Performance Monitoring

**Add query performance logging:**

```python
import time

async def get_bet_history(...):
    start_time = time.time()
    
    # ... query execution ...
    
    query_time = time.time() - start_time
    
    # Log slow queries (> 1 second)
    if query_time > 1.0:
        logger.warning(f"Slow query detected: {query_time:.2f}s for user {address}, filter: {filter}")
    
    # Log query execution plan (for debugging)
    if logger.level == "DEBUG":
        explain = await bets_col.find(query).sort(sort_spec).explain()
        logger.debug(f"Query plan: {explain.get('executionStats', {})}")
```

#### 1.5 Caching Strategy for Stats

**Cache user stats to avoid recalculating on every request:**

```python
from functools import lru_cache
import redis  # or use in-memory cache

# Cache stats for 5 minutes
@lru_cache(maxsize=1000)
async def get_cached_user_stats(user_id: str, filter: str):
    cache_key = f"user_stats:{user_id}:{filter}"
    
    # Check cache
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Calculate stats
    stats = await _get_user_stats_aggregated(user_id, query)
    
    # Cache for 5 minutes
    await redis_client.setex(cache_key, 300, json.dumps(stats))
    
    return stats
```

#### 1.6 Materialized Views / Pre-aggregated Data (For Extremely Large Datasets)

**For production with millions of bets, consider pre-aggregating:**

```python
# Background job to pre-aggregate stats
async def update_user_stats_aggregate(user_id: ObjectId):
    """
    Pre-calculate and store user stats in a separate collection.
    Update periodically (every 5 minutes or on bet completion).
    """
    stats_col = get_user_stats_collection()
    
    # Calculate stats using aggregation
    stats = await _calculate_user_stats(user_id)
    
    # Store in stats collection
    await stats_col.update_one(
        {"user_id": user_id},
        {"$set": stats, "$setOnInsert": {"updated_at": datetime.utcnow()}},
        upsert=True
    )

# Then in API endpoint, just fetch from stats collection
async def get_bet_history(...):
    # Fast lookup from pre-aggregated stats
    stats = await stats_col.find_one({"user_id": user_id})
    return stats
```

### Phase 2: Frontend Implementation

#### 2.1 Implement Infinite Scroll / Virtual Scrolling

**Option A: Infinite Scroll (Recommended)**
- Load more data as user scrolls to bottom
- Simpler implementation
- Better for mobile
- Progressive loading

**Option B: Virtual Scrolling**
- Render only visible items
- Better for very large lists (10,000+ items)
- More complex implementation
- Requires library (react-window, react-virtualized)

**Recommendation**: Start with **Infinite Scroll**, upgrade to Virtual Scrolling if needed.

#### 2.2 State Management

**State Structure**:
```javascript
const [bets, setBets] = useState([]);
const [loading, setLoading] = useState(false);
const [hasMore, setHasMore] = useState(true);
const [page, setPage] = useState(1);
const [filter, setFilter] = useState('all');
const [search, setSearch] = useState('');
const [sort, setSort] = useState('newest');
const [stats, setStats] = useState(null);
const [error, setError] = useState(null);
```

#### 2.3 Data Fetching Strategy

**Initial Load**:
1. Fetch first page (50 items)
2. Show loading state
3. Display bets
4. Enable infinite scroll

**Load More**:
1. User scrolls to bottom
2. Increment page number
3. Fetch next page
4. Append to existing bets
5. Update `hasMore` flag

**Filter/Search Change**:
1. Reset page to 1
2. Clear existing bets
3. Fetch new data
4. Update stats

#### 2.4 Component Structure

```javascript
export default function BettingHistory() {
  const [bets, setBets] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  
  // Fetch bets function
  const fetchBets = async (pageNum = 1, reset = false) => {
    setLoading(true);
    try {
      const response = await getBetHistory({
        page: pageNum,
        page_size: 50,
        filter: filter,
        sort: 'newest'
      });
      
      if (reset) {
        setBets(response.bets);
      } else {
        setBets(prev => [...prev, ...response.bets]);
      }
      
      setHasMore(response.pagination.has_next);
      setStats(response.stats);
    } catch (error) {
      console.error('Error fetching bets:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Load more on scroll
  const handleScroll = useCallback(() => {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 1000) {
      if (!loading && hasMore) {
        setPage(prev => prev + 1);
      }
    }
  }, [loading, hasMore]);
  
  // Effect for initial load and filter changes
  useEffect(() => {
    setPage(1);
    setBets([]);
    fetchBets(1, true);
  }, [filter]);
  
  // Effect for pagination
  useEffect(() => {
    if (page > 1) {
      fetchBets(page, false);
    }
  }, [page]);
  
  // Scroll listener
  useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);
  
  return (
    <div>
      {/* Filter tabs */}
      {/* Bet list with infinite scroll */}
      {/* Loading indicator */}
      {/* End of list message */}
    </div>
  );
}
```

#### 2.5 Optimizations

**1. Debounce Search Input**
```javascript
const debouncedSearch = useMemo(
  () => debounce((value) => {
    setSearch(value);
    setPage(1);
    setBets([]);
    fetchBets(1, true);
  }, 500),
  []
);
```

**2. Memoize Bet Items**
```javascript
const BetItem = React.memo(({ bet }) => {
  // Render bet item
});
```

**3. Lazy Load Images/Icons**
- Use `loading="lazy"` for images
- Load icons on demand

**4. Virtualize Long Lists** (if needed)
```javascript
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={bets.length}
  itemSize={200}
  width="100%"
>
  {({ index, style }) => (
    <div style={style}>
      <BetItem bet={bets[index]} />
    </div>
  )}
</FixedSizeList>
```

### Phase 3: Real-time Updates (Optional)

#### 3.1 WebSocket Integration
- Connect to existing WebSocket endpoint
- Listen for `new_bet` messages
- Prepend new bets to list (if matches current filter)
- Update stats in real-time

**Implementation**:
```javascript
const handleBetMessage = useCallback((message) => {
  if (message.type === 'new_bet' && message.bet) {
    // Check if bet matches current filter
    if (matchesFilter(message.bet, filter)) {
      setBets(prev => [transformBet(message.bet), ...prev]);
      // Update stats if needed
    }
  }
}, [filter]);
```

### Phase 4: User Address Handling

#### 4.1 Address Input/Selection
**Option A**: User enters their address
**Option B**: Store address in localStorage/cookies
**Option C**: Get from wallet connection (future)

**Recommendation**: Start with **Option A** (address input), add localStorage persistence.

#### 4.2 Address Validation
- Validate Bitcoin address format
- Show error for invalid addresses
- Support both testnet and mainnet

## Implementation Steps

### Step 1: Backend Pagination
1. Update `get_bet_history` endpoint with pagination
2. Add filter support (wins, big_wins, rare_wins)
3. Add sort options
4. Add database indexes
5. Test with large datasets

### Step 2: API Utility Functions
1. Create `getBetHistory()` function in `src/utils/api.js`
2. Add parameters: page, page_size, filter, sort, search
3. Handle errors and loading states

### Step 3: Frontend Component Updates
1. Replace mock data with API calls
2. Implement infinite scroll
3. Add filter tabs (All, Wins, Big Wins, Rare Wins)
4. Add search functionality
5. Add loading states
6. Add error handling

### Step 4: Optimizations
1. Add debouncing for search
2. Memoize components
3. Optimize re-renders
4. Add virtual scrolling if needed

### Step 5: Real-time Updates (Optional)
1. Integrate WebSocket
2. Handle new bet messages
3. Update list in real-time
4. Update stats

## Files to Create/Modify

### Backend:
1. `backend/app/api/bet_routes.py` - Add pagination and filtering
2. `backend/app/dtos/bet_dto.py` - Update response models
3. `backend/app/models/database.py` - Add indexes

### Frontend:
1. `satoshi-dice-main/src/utils/api.js` - Add bet history API functions
2. `satoshi-dice-main/src/components/gameHistory/index.js` - Complete rewrite
3. `satoshi-dice-main/src/components/gameHistory/BetItem.js` - (NEW) Memoized bet item component
4. `satoshi-dice-main/src/hooks/useInfiniteScroll.js` - (NEW) Custom hook for infinite scroll

## Key Considerations

### 1. **Backend Performance Optimizations**

#### Database Query Optimization:
- **Compound Indexes**: Must match query pattern exactly (equality → sort → range)
- **Index Order**: Critical for query performance
  - For "big_wins": `(user_id, is_win, bet_amount, created_at)`
  - For "rare_wins": `(user_id, is_win, roll_result, created_at)`
- **Partial Indexes**: Only index completed bets to reduce index size
- **Sparse Indexes**: For optional fields (txids)

#### Query Execution Optimization:
- **Avoid count_documents()** on large datasets (use estimated count or skip)
- **Fetch extra item** to determine has_next without counting
- **Use aggregation pipelines** for stats calculation (single query vs multiple)
- **Cursor-based pagination** for very large datasets (millions of bets)

#### Caching Strategy:
- **Cache user stats** for 5 minutes (stats don't change frequently)
- **Cache filter results** for first page (most common)
- **Invalidate cache** on new bet completion

#### Query Patterns:
- **Big Wins Query**: `{user_id, is_win: true, bet_amount: {$gte: threshold}}`
  - Must use index: `(user_id, is_win, bet_amount, created_at)`
  - Sort by `bet_amount` descending for biggest wins first
  
- **Rare Wins Query**: `{user_id, is_win: true, roll_result: {$lt: 1000}}`
  - Must use index: `(user_id, is_win, roll_result, created_at)`
  - Sort by `roll_result` ascending for rarest wins first

#### Performance Monitoring:
- **Log slow queries** (> 1 second)
- **Monitor index usage** (use `explain()` to verify index usage)
- **Track query execution time**
- **Alert on full collection scans**

### 2. **Frontend Performance**
- Limit page size to 50-100 items
- Use database indexes for fast queries
- Implement caching if needed
- Use virtual scrolling for 10,000+ items

### 2. **User Experience**
- Show loading indicators
- Smooth scrolling
- Preserve scroll position on filter change (optional)
- Show "No more bets" message
- Handle empty states

### 3. **Data Consistency**
- Handle race conditions
- Prevent duplicate bets
- Handle concurrent updates
- Validate data before display

### 4. **Error Handling**
- Network errors
- Invalid addresses
- Empty results
- Server errors
- Timeout handling

### 5. **Mobile Optimization**
- Touch-friendly infinite scroll
- Optimized rendering
- Reduced data per page on mobile
- Lazy loading images

## Testing Checklist

- [ ] Load first page of bets
- [ ] Infinite scroll loads more bets
- [ ] Filter tabs work correctly
- [ ] Search functionality works
- [ ] Sort options work
- [ ] Pagination metadata is correct
- [ ] Loading states display properly
- [ ] Error handling works
- [ ] Empty states display
- [ ] Performance with 1000+ bets
- [ ] Performance with 10,000+ bets
- [ ] Mobile responsiveness
- [ ] Real-time updates (if implemented)
- [ ] Address validation
- [ ] Database query performance

## Expected Outcome

After implementation:
- Bet history loads efficiently with pagination
- Infinite scroll for seamless browsing
- Server-side filtering (All, Wins, Big Wins, Rare Wins)
- Search functionality
- Sort options
- Handles large datasets (millions of bets)
- Good performance on mobile and desktop
- Real-time updates (optional)
- Smooth user experience

## Performance Targets

### Backend Performance:
- **Query Execution**: < 200ms for filtered queries (with proper indexes)
- **Big Wins Query**: < 500ms even with millions of bets (using compound index)
- **Rare Wins Query**: < 500ms even with millions of bets (using compound index)
- **Stats Aggregation**: < 300ms using aggregation pipeline
- **Index Usage**: 100% index coverage (no full collection scans)
- **Cache Hit Rate**: > 80% for stats queries

### Frontend Performance:
- **Initial Load**: < 1 second for first 50 bets
- **Load More**: < 500ms for next page
- **Filter Change**: < 1 second (including backend query)
- **Search**: < 500ms (debounced)
- **Render**: 60 FPS scrolling
- **Memory**: < 100MB for 1000 loaded bets

### Database Performance:
- **Index Build Time**: < 5 minutes for large collections
- **Index Size**: < 20% of collection size
- **Query Plan**: All queries use indexes (no COLLSCAN)
- **Query Selectivity**: Indexes reduce scanned documents by > 99%

## Notes

### Backend Optimization Notes:

1. **Index Strategy is Critical**: 
   - Compound indexes must match query patterns exactly
   - Test index usage with `explain()` before deploying
   - Monitor index usage and rebuild if needed

2. **Query Pattern Matching**:
   - Big Wins: Query must use `(user_id, is_win, bet_amount, created_at)` index
   - Rare Wins: Query must use `(user_id, is_win, roll_result, created_at)` index
   - Order matters: equality fields → sort fields → range fields

3. **Avoid Full Collection Scans**:
   - Always include `user_id` in query (most selective field)
   - Use `explain()` to verify index usage
   - Monitor for COLLSCAN in query plans

4. **Count Optimization**:
   - `count_documents()` is expensive on large collections
   - Use estimated count or skip count for later pages
   - Fetch extra item to determine has_next

5. **Aggregation for Stats**:
   - Single aggregation pipeline vs multiple queries
   - More efficient for calculating totals
   - Can be cached for better performance

6. **Cursor-Based Pagination**:
   - More efficient than offset-based for very large datasets
   - Avoids `skip()` which becomes slow on large offsets
   - Use `_id` or `created_at` as cursor

7. **Caching Strategy**:
   - Cache user stats (change infrequently)
   - Cache first page results (most common)
   - Invalidate on new bet completion
   - Use Redis or in-memory cache

8. **Materialized Views** (For Extremely Large Datasets):
   - Pre-aggregate stats in background job
   - Update periodically (every 5 minutes)
   - Fast lookup from pre-calculated data

### Frontend Notes:

1. **Start Simple**: Begin with basic pagination and infinite scroll, add optimizations as needed.

2. **Monitor Performance**: Use React DevTools Profiler to identify bottlenecks.

3. **Database Optimization**: Ensure proper indexes are in place before handling large datasets.

4. **Caching Strategy**: Consider caching recent pages in localStorage for faster navigation.

5. **Progressive Enhancement**: Start with server-side pagination, add virtual scrolling if needed for very large lists.

6. **User Address**: For now, require user to input their address. Future: integrate with wallet connection.

### Testing Large Datasets:

1. **Test with Realistic Data**:
   - Create test dataset with 1M+ bets
   - Test each filter type (all, wins, big_wins, rare_wins)
   - Verify index usage with `explain()`

2. **Performance Testing**:
   - Measure query execution time
   - Monitor database CPU and memory
   - Check for slow queries in logs

3. **Index Validation**:
   - Verify all queries use indexes
   - Check index selectivity
   - Monitor index size and build time
