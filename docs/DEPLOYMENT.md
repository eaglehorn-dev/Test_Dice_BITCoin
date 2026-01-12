# Deployment Guide

Complete production deployment guide for Bitcoin Dice Game.

## 🎯 Overview

This guide covers deploying the complete application stack:
- Backend (FastAPI + Python)
- Frontend (React)
- Database (SQLite/PostgreSQL)
- Nginx reverse proxy
- SSL/TLS configuration

## 📋 Prerequisites

- Ubuntu 20.04+ or similar Linux server
- Python 3.9+
- Node.js 16+
- Nginx
- Domain name (optional but recommended)
- Bitcoin testnet wallet with funds

## 🔧 Backend Deployment

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.9 python3-pip python3-venv nginx -y

# Install PostgreSQL (optional, for production)
sudo apt install postgresql postgresql-contrib -y
```

### 2. Create Application User

```bash
sudo adduser --system --group --home /opt/dice dice
sudo su - dice
```

### 3. Clone and Setup Application

```bash
cd /opt/dice
git clone <your-repo-url> app
cd app/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Create .env file
cat > .env << EOF
# BlockCypher
BLOCKCYPHER_API_TOKEN=your_actual_token_here
BLOCKCYPHER_NETWORK=test3

# House Wallet - CRITICAL: Keep secure!
HOUSE_PRIVATE_KEY=your_testnet_private_key
HOUSE_ADDRESS=your_testnet_address

# Database
DATABASE_URL=sqlite:///./dice_game.db
# For PostgreSQL: postgresql://dice:password@localhost/dice_game

# Game Configuration
HOUSE_EDGE=0.02
MIN_BET_SATOSHIS=10000
MAX_BET_SATOSHIS=1000000
MIN_MULTIPLIER=1.1
MAX_MULTIPLIER=98.0

# Bitcoin Network
CONFIRMATIONS_REQUIRED=1
MIN_CONFIRMATIONS_PAYOUT=0
NETWORK=testnet

# Transaction Detection
WEBHOOK_CALLBACK_URL=https://yourdomain.com/api/webhook/tx
POLLING_INTERVAL_SECONDS=30

# Fallback APIs
BLOCKSTREAM_API=https://blockstream.info/testnet/api
MEMPOOL_SPACE_API=https://mempool.space/testnet/api

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256

# Server
HOST=127.0.0.1
PORT=8000
RELOAD=false

# Frontend URL
FRONTEND_URL=https://yourdomain.com
EOF

# Secure the env file
chmod 600 .env
```

### 5. Initialize Database

```bash
source venv/bin/activate
python3 -c "from app.database import init_db; init_db()"
```

### 6. Create Systemd Service

```bash
sudo cat > /etc/systemd/system/dice-api.service << EOF
[Unit]
Description=Bitcoin Dice API
After=network.target

[Service]
Type=simple
User=dice
Group=dice
WorkingDirectory=/opt/dice/app/backend
Environment="PATH=/opt/dice/app/backend/venv/bin"
ExecStart=/opt/dice/app/backend/venv/bin/python -m app.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable dice-api
sudo systemctl start dice-api
sudo systemctl status dice-api
```

### 7. Verify Backend

```bash
# Check if API is running
curl http://127.0.0.1:8000/

# View logs
sudo journalctl -u dice-api -f
```

## 🎨 Frontend Deployment

### 1. Build Frontend

```bash
cd /opt/dice/app/frontend

# Install dependencies
npm install

# Create production .env
cat > .env << EOF
REACT_APP_API_URL=https://yourdomain.com
EOF

# Build
npm run build
```

### 2. Setup Static Files

```bash
sudo mkdir -p /var/www/dice
sudo cp -r build/* /var/www/dice/
sudo chown -R www-data:www-data /var/www/dice
```

## 🌐 Nginx Configuration

### 1. Create Nginx Config

```bash
sudo cat > /etc/nginx/sites-available/dice << 'EOF'
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=30r/s;

# Upstream backend
upstream dice_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name yourdomain.com;

    # Redirect to HTTPS (after SSL setup)
    # return 301 https://$server_name$request_uri;

    # Frontend
    root /var/www/dice;
    index index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
        limit_req zone=general_limit burst=20 nodelay;
    }

    # API proxy
    location /api {
        proxy_pass http://dice_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req zone=api_limit burst=5 nodelay;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files cache
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/dice /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### 2. SSL/TLS with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

### 3. Update Nginx for HTTPS

After SSL setup, uncomment the HTTPS redirect in nginx config and add:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # ... rest of configuration ...
}
```

## 🗄️ PostgreSQL Setup (Optional)

For production, use PostgreSQL instead of SQLite:

```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE dice_game;
CREATE USER dice WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE dice_game TO dice;
\q
EOF

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://dice:your_secure_password@localhost/dice_game

# Restart service
sudo systemctl restart dice-api
```

## 🔒 Security Hardening

### 1. Firewall Setup

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Fail2Ban

```bash
sudo apt install fail2ban -y

# Create jail for API
sudo cat > /etc/fail2ban/jail.d/dice.conf << EOF
[dice-api]
enabled = true
port = 80,443
filter = dice-api
logpath = /var/log/nginx/access.log
maxretry = 5
bantime = 3600
EOF

sudo systemctl restart fail2ban
```

### 3. Secure Private Keys

```bash
# Ensure .env is not readable by others
chmod 600 /opt/dice/app/backend/.env
chown dice:dice /opt/dice/app/backend/.env

# Never commit .env to git
echo ".env" >> /opt/dice/app/.gitignore
```

## 📊 Monitoring

### 1. Log Rotation

```bash
sudo cat > /etc/logrotate.d/dice << EOF
/opt/dice/app/backend/dice_game.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 dice dice
    sharedscripts
    postrotate
        systemctl reload dice-api > /dev/null
    endscript
}
EOF
```

### 2. Health Checks

```bash
# Add to crontab
crontab -e

# Add this line
*/5 * * * * curl -f http://localhost:8000/ || systemctl restart dice-api
```

### 3. Backup Script

```bash
#!/bin/bash
# /opt/dice/backup.sh

BACKUP_DIR="/opt/dice/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp /opt/dice/app/backend/dice_game.db $BACKUP_DIR/dice_game_$DATE.db

# Backup .env
cp /opt/dice/app/backend/.env $BACKUP_DIR/env_$DATE.bak

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

# Make executable
chmod +x /opt/dice/backup.sh

# Add to crontab for daily backups
# 0 2 * * * /opt/dice/backup.sh
```

## 🔄 Updates and Maintenance

### Updating the Application

```bash
# Pull latest code
cd /opt/dice/app
git pull

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart dice-api

# Update frontend
cd ../frontend
npm install
npm run build
sudo cp -r build/* /var/www/dice/
```

### Database Migrations

```bash
# If using Alembic for migrations
cd /opt/dice/app/backend
source venv/bin/activate
alembic upgrade head
sudo systemctl restart dice-api
```

## 📱 Monitoring Commands

```bash
# Check API status
sudo systemctl status dice-api

# View API logs
sudo journalctl -u dice-api -f

# Check nginx status
sudo systemctl status nginx

# View nginx error logs
sudo tail -f /var/log/nginx/error.log

# View nginx access logs
sudo tail -f /var/log/nginx/access.log

# Check disk usage
df -h

# Check memory usage
free -h

# Check active connections
ss -tuln
```

## 🚨 Troubleshooting

### API Not Starting

```bash
# Check logs
sudo journalctl -u dice-api -n 100

# Check permissions
ls -la /opt/dice/app/backend/.env

# Test manually
cd /opt/dice/app/backend
source venv/bin/activate
python -m app.main
```

### Database Issues

```bash
# Check database file
ls -la /opt/dice/app/backend/dice_game.db

# Recreate database
python -c "from app.database import drop_all, init_db; drop_all(); init_db()"
```

### Nginx Issues

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Restart nginx
sudo systemctl restart nginx
```

## 🎉 Verification

After deployment, verify:

1. ✅ Frontend loads at https://yourdomain.com
2. ✅ API responds at https://yourdomain.com/api/stats
3. ✅ Wallet connection works
4. ✅ Can create deposit address
5. ✅ Transaction detection works
6. ✅ Bet processing works
7. ✅ Payouts are sent
8. ✅ Verification page works

## 📞 Support

For issues:
- Check logs first
- Review configuration
- Test each component individually
- Verify network connectivity
- Check BlockCypher API limits

---

**⚠️ Important Reminders:**
- This is TESTNET ONLY
- Never use mainnet private keys
- Keep .env file secure
- Monitor server resources
- Regular backups are essential
- Test thoroughly before going live
