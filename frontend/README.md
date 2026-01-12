# Bitcoin Dice - Frontend

React-based frontend for the Bitcoin Provably Fair Dice Game.

## Features

- 🎨 Modern casino-style UI
- 👛 Wallet connection (Unisat-style)
- 🎲 Interactive dice game interface
- 📊 Real-time statistics
- 📜 Bet history tracking
- ✅ Provably fair verification page
- 📱 Fully responsive design

## Tech Stack

- React 18
- CSS3 with animations
- Axios for API calls
- React Router for navigation

## Installation

```bash
npm install
```

## Configuration

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

## Development

```bash
npm start
```

Runs the app in development mode at [http://localhost:3000](http://localhost:3000)

## Production Build

```bash
npm run build
```

Builds the app for production to the `build` folder.

## Components

### WalletConnect
- Connects to Unisat wallet or manual address input
- Displays connected address
- Handles user authentication with backend

### DiceGame
- Main game interface
- Multiplier and win chance selector
- Deposit address generation
- Transaction submission
- Real-time bet result display

### BetHistory
- Displays user's complete bet history
- Sortable and filterable
- Shows bet status and results

### FairnessVerifier
- Allows verification of any bet
- Displays cryptographic proof
- Shows HMAC calculation steps

### Stats
- Platform-wide statistics
- Total users, bets, wagered amounts
- Win rate and house edge

### RecentBets
- Live feed of recent bets
- Updates in real-time
- Shows all players' bets

## Styling

All components use custom CSS with:
- Casino-themed color scheme
- Smooth animations
- Glass-morphism effects
- Responsive grid layouts

## API Integration

The frontend communicates with the backend via REST API:

- `POST /api/user/connect` - Connect user
- `POST /api/deposit/create` - Create deposit address
- `POST /api/tx/submit` - Submit transaction
- `GET /api/bets/user/{address}` - Get user bets
- `GET /api/bet/{id}` - Get bet details
- `POST /api/bet/verify` - Verify bet fairness
- `GET /api/stats` - Get platform stats
- `GET /api/bets/recent` - Get recent bets

## Deployment

For production deployment:

1. Build the app: `npm run build`
2. Serve the `build` folder with any static file server
3. Configure environment variables for production API URL

Example with nginx:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /path/to/build;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## License

MIT
