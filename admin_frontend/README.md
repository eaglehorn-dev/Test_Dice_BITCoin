# 🎨 Bitcoin Dice Game - Admin Frontend

**React Admin Dashboard**

A beautiful, secure admin dashboard for managing your Bitcoin dice game. Connects to the admin backend API (port 8001).

---

## 🚀 **Quick Start**

### **1. Configure Environment**

Create a `.env` file in this directory:

```env
PORT=3001
REACT_APP_ADMIN_API_URL=http://localhost:8001
REACT_APP_ADMIN_API_KEY=your-admin-api-key-from-backend
```

⚠️ **Important**: The `REACT_APP_ADMIN_API_KEY` must match the `ADMIN_API_KEY` in your `admin_backend/.env` file!

### **2. Install Dependencies**

```bash
npm install
```

### **3. Start Frontend**

**Windows:**
```cmd
start-admin-frontend.bat
```

**Linux/Mac:**
```bash
chmod +x start-admin-frontend.sh
./start-admin-frontend.sh
```

**Or manually:**
```bash
npm start
```

The admin dashboard will open at: `http://localhost:3001`

---

## 🎯 **Features**

### **📊 Dashboard Overview**
- **Treasury Balance**: Live BTC balance with USD conversion
- **Real-time BTC Price**: From CoinGecko API
- **Period Stats**: Today, Week, Month, All-Time
- **Income vs. Outcome**: Track profit/loss
- **Win Rate**: Player win percentage

### **🔑 Wallet Vault Management**
- **View All Wallets**: See all multiplier wallets
- **Live Balances**: Real-time blockchain balances
- **Generate Wallets**: Create new wallets for any multiplier
- **Withdraw Funds**: Send to cold storage with one click
- **Wallet Stats**: Track received/sent amounts and bet counts

### **📈 Analytics**
- **Volume by Multiplier**: Bar charts showing bet distribution
- **Profit Analysis**: See which multipliers are profitable
- **Bet Counts**: Track activity per wallet
- **Historical Trends**: Daily stats over time

### **🔒 Security**
- **API Key Authentication**: All requests include API key header
- **IP Whitelisting**: Backend enforces IP restrictions
- **No Private Keys**: Frontend never sees wallet private keys
- **Secure Withdrawals**: Confirmation dialogs before withdrawals

---

## 🗂️ **Project Structure**

```
admin_frontend/
├── public/
│   └── index.html                 # HTML template
├── src/
│   ├── components/
│   │   ├── StatsCards.js          # Period statistics cards
│   │   ├── WalletGrid.js          # Wallet management table
│   │   └── VolumeChart.js         # Volume analytics chart
│   ├── pages/
│   │   └── Dashboard.js           # Main dashboard page
│   ├── services/
│   │   └── api.js                 # Admin API client
│   ├── utils/
│   │   └── format.js              # Formatting utilities
│   ├── App.js                     # Main React component
│   ├── index.js                   # React entry point
│   └── index.css                  # Tailwind CSS styles
├── .env                            # Your configuration
├── package.json                    # Dependencies
├── tailwind.config.js              # Tailwind configuration
└── README.md                       # This file
```

---

## 🎨 **UI Components**

### **Treasury Balance Card**
Gradient card showing:
- Total BTC balance across all wallets
- USD value
- Current BTC price

### **Stats Cards**
Four period cards (Today, Week, Month, All-Time) showing:
- Total bets
- Wins/Losses
- Income (total bets received)
- Outcome (total payouts sent)
- Net profit (green if positive, red if negative)
- Win rate percentage

### **Wallet Grid**
Comprehensive table with:
- Multiplier badges (2x, 3x, etc.)
- Bitcoin addresses (truncated)
- Live balances (sats + USD)
- Usage statistics (bets, received, sent)
- Status badges (Active/Depleted/Inactive)
- Withdraw button

### **Volume Chart**
- Summary cards for each multiplier
- Bar chart showing wagered/paid out/profit
- Color-coded (blue = wagered, red = paid, green = profit)

---

## 📱 **Responsive Design**

- **Desktop**: Full layout with all components
- **Tablet**: Adjusted grid layouts
- **Mobile**: Stacked cards, scrollable tables

Built with **Tailwind CSS** for beautiful, consistent styling.

---

## 🔧 **Configuration**

### **Environment Variables**

| Variable | Description | Example |
|----------|-------------|---------|
| `PORT` | Frontend port | `3001` |
| `REACT_APP_ADMIN_API_URL` | Admin backend URL | `http://localhost:8001` |
| `REACT_APP_ADMIN_API_KEY` | Admin API key | `your-32-char-secret` |

### **Proxy Configuration**

`package.json` includes a proxy to the admin backend:

```json
"proxy": "http://localhost:8001"
```

This allows relative API calls like `/admin/dashboard`.

---

## 🛠️ **Development**

### **Available Scripts**

```bash
npm start          # Start development server
npm build          # Build for production
npm test           # Run tests
npm eject          # Eject from Create React App
```

### **Hot Reload**

The development server supports hot module replacement. Changes to code will automatically refresh the browser.

### **API Key Testing**

If you get 401 errors, check:
1. `.env` file exists in `admin_frontend/`
2. `REACT_APP_ADMIN_API_KEY` matches backend's `ADMIN_API_KEY`
3. Restart the frontend after changing `.env`

---

## 🚀 **Production Deployment**

### **Build**

```bash
npm run build
```

This creates a `build/` folder with optimized static files.

### **Serve**

```bash
npm install -g serve
serve -s build -l 3001
```

### **Nginx Configuration**

```nginx
server {
    listen 443 ssl;
    server_name admin.yourgame.com;

    # SSL configuration...

    location / {
        root /var/www/admin_frontend/build;
        try_files $uri /index.html;
    }

    location /admin/ {
        proxy_pass http://127.0.0.1:8001/admin/;
        proxy_set_header X-Admin-API-Key $http_x_admin_api_key;
    }
}
```

---

## 📊 **Dashboard Workflow**

1. **Load Dashboard**:
   - Fetches `/admin/dashboard`
   - Displays treasury balance, stats, wallets, volume

2. **Generate Wallet**:
   - Enter multiplier (e.g., 10)
   - Click "Generate Wallet"
   - New wallet created and encrypted
   - Instantly appears in wallet grid

3. **Monitor Balances**:
   - Balances update every 60 seconds
   - Manual refresh button available
   - Real-time data from blockchain

4. **Withdraw Funds**:
   - Click "Withdraw" on any wallet
   - Confirms balance > 1000 sats
   - Sends entire balance to cold storage
   - Shows transaction ID

---

## 🆘 **Troubleshooting**

### **401 Unauthorized**
- Check `.env` file has correct `REACT_APP_ADMIN_API_KEY`
- Restart frontend: `npm start`
- Verify backend is running on port 8001

### **403 Forbidden**
- Your IP is not whitelisted on backend
- Add your IP to backend's `ADMIN_IP_WHITELIST`

### **CORS Errors**
- Ensure backend has frontend URL in `CORS allow_origins`
- Check `admin_backend/app/main.py` CORS settings

### **Can't Connect to Backend**
- Verify backend is running: `curl http://localhost:8001/admin/health`
- Check firewall settings
- Try `http://localhost:8001` instead of `127.0.0.1`

---

## 📝 **Dependencies**

- **React**: UI framework
- **Tailwind CSS**: Utility-first CSS
- **Axios**: HTTP client
- **Recharts**: Charts and visualizations
- **React Router**: Navigation (optional, for future pages)

---

## ✅ **Checklist**

- [ ] Create `.env` file with API key
- [ ] Run `npm install`
- [ ] Start admin backend (port 8001)
- [ ] Start admin frontend (port 3001)
- [ ] Access `http://localhost:3001`
- [ ] Verify dashboard loads
- [ ] Test wallet generation
- [ ] Test withdrawal (with test wallet)

---

**Built with React + Tailwind CSS + Recharts**
