# Satoshi Dice Main Frontend - Analysis Report

## Overview
This is a **Next.js 16.1.2** frontend application for a Satoshi Dice game, built with React 19.2.3 and Tailwind CSS 4. The application appears to be designed for **Bitcoin Cash (BCH)** gaming, not Bitcoin (BTC).

## Technology Stack

### Core Technologies
- **Framework**: Next.js 16.1.2 (App Router)
- **React**: 19.2.3
- **Styling**: Tailwind CSS 4
- **Icons**: Lucide React
- **QR Codes**: react-qrcode-logo

### Project Structure
```
satoshi-dice-main/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── page.js             # Main game page
│   │   ├── layout.js           # Root layout
│   │   ├── globals.css         # Global styles
│   │   ├── fair/page.js        # Provably Fair page
│   │   └── rules/page.js       # Rules & FAQ page
│   └── components/
│       ├── navbar/index.js     # Navigation bar
│       ├── footer/index.js     # Footer component
│       └── gameHistory/index.js # Betting history component
├── public/                     # Static assets
└── package.json
```

## Key Features

### 1. Main Game Page (`src/app/page.js`)
**Functionality:**
- Multiplier selection with 11 options (1.05x to 1000x)
- Bet amount slider (0.001 to 7.5 BCH)
- Currency toggle (BCH/USD)
- QR code display for deposit address
- Recent games display
- Total bets counter

**Key Components:**
- **Multiplier Selection**: 
  - Desktop: Button grid + draggable slider
  - Mobile: Chance badges only
  - 11 multipliers with corresponding win chances
- **Bet Amount Slider**: 
  - Logarithmic scale (0.001 - 7.5 BCH)
  - Min/1/2/x2/Max quick buttons
  - USD conversion display
- **Deposit Address**: 
  - QR code with logo
  - Copy address button
  - "Open in wallet" option

**Current Implementation:**
- Uses **hardcoded** deposit address: `bitcoincash:qz9cq5yfkyjpgq6xatlr6veyhmcartkyrg7wev9jzc`
- Static multiplier data (not from API)
- Mock recent games data
- Static total bets counter

### 2. Navigation Bar (`src/components/navbar/index.js`)
**Features:**
- Logo with link to home
- "How To Play" modal
- Links to Rules and Provably Fair pages
- Language selector (English)
- Sound toggle (on/off)

### 3. Betting History (`src/components/gameHistory/index.js`)
**Features:**
- Tab filtering: All, Wins, Big Wins, Rare Wins
- Displays: Result, Bet Amount, Payout, Time, Game ID, Deposit TX, Payout TX, Bet, Roll
- Responsive grid layout
- **Currently uses mock data**

### 4. Provably Fair Page (`src/app/fair/page.js`)
**Features:**
- Explanation of provably fair system
- Table showing:
  - Use Date
  - Server Seed Hash
  - Server Seed Plaintext (shows "Not Published" for future dates)
- **Currently uses hardcoded data** (21 entries)

### 5. Rules Page (`src/app/rules/page.js`)
**Features:**
- Game rules and explanation
- FAQ section
- Available Games table with:
  - Legacy Address
  - CashAddr
  - Max Roll (65535)
  - Max/Min Bet
  - Multiplier
  - Bet Number
  - Odds
- **Currently uses hardcoded game data** (11 games)

## Design & Styling

### Color Scheme
- Background: Dark (#222222) with background images
- Primary: Purple/Green gradients (#8360C3 to #2EBF91)
- Text: White on dark backgrounds, black on light
- Accents: #8EAAAF (teal), #2EBF91 (green for wins)

### UI Elements
- Glassmorphism effects (backdrop blur)
- Rounded corners (5px, 8px, 20px)
- Shadow effects
- Responsive design (mobile-first)

## Current Limitations & Integration Points

### 1. **No Backend Integration**
- All data is hardcoded/mocked
- No API calls to fetch wallets, bets, or game data
- Deposit address is static

### 2. **Bitcoin Cash vs Bitcoin**
- This frontend is designed for **Bitcoin Cash (BCH)**
- Uses `bitcoincash:` address format
- Your backend appears to be for **Bitcoin (BTC)**
- **Major incompatibility**: Address formats and networks differ

### 3. **Missing Features**
- No WebSocket integration for real-time updates
- No actual transaction detection
- No bet result processing
- No server seed hash management
- No wallet address generation per multiplier

### 4. **Integration Requirements**
To integrate with your existing backend:

1. **Replace BCH with BTC**:
   - Change address format from `bitcoincash:` to `bitcoin:` or remove prefix
   - Update currency references
   - Modify QR code generation

2. **API Integration**:
   - Connect to `/api/wallets/all` for multiplier options
   - Connect to `/api/wallets/{multiplier}` for deposit addresses
   - Connect to WebSocket `/ws/bets` for real-time updates
   - Connect to `/api/bets/history` for betting history
   - Connect to `/api/fairness/seeds` for provably fair data

3. **State Management**:
   - Replace hardcoded multipliers with API data
   - Replace static address with dynamic wallet addresses
   - Implement WebSocket for real-time bet results
   - Connect betting history to actual API

4. **Component Updates**:
   - `page.js`: Fetch wallets from API, use dynamic addresses
   - `gameHistory/index.js`: Connect to bet history API
   - `fair/page.js`: Connect to fairness seeds API
   - Add WebSocket connection for live updates

## Recommendations

### Option 1: Adapt This Frontend to Your Backend
1. Replace BCH references with BTC
2. Integrate API endpoints
3. Add WebSocket support
4. Connect all components to backend data

### Option 2: Use Your Existing Frontend
Your current `frontend/` directory already has:
- React Router setup
- API integration
- WebSocket support
- BTC address handling
- All necessary components

**Recommendation**: Since your existing frontend is already integrated with your backend and uses BTC, it might be easier to enhance it with design elements from this Next.js frontend rather than migrating everything.

## Next Steps

1. **Decide on approach**: Adapt Next.js frontend or enhance existing React frontend
2. **If adapting Next.js**:
   - Create API service layer
   - Replace BCH with BTC
   - Integrate WebSocket
   - Connect all data sources
3. **If enhancing existing**:
   - Extract design patterns from Next.js frontend
   - Apply to existing components
   - Maintain current backend integration

## File Dependencies

### API Integration Points Needed:
- `src/utils/api.js` - Create API service (similar to existing frontend)
- WebSocket connection in `page.js` for real-time updates
- Replace all hardcoded data with API calls

### Environment Variables Needed:
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_WS_URL` - WebSocket URL
