# 🚀 Crypto Trading Dashboard - Quick Start Guide

## One-Command Startup

I've created startup scripts to launch your dashboard with a single command from the crypto-bot root directory.

### For Linux/Mac:
```bash
./start-dashboard.sh
```

### For Windows:
```cmd
start-dashboard.bat
```

## What the Scripts Do

1. **🔍 Auto-Detection**: Finds the script location and navigates to the dashboard
2. **✅ Validation**: Checks for required files and directories
3. **📦 Auto-Install**: Installs dependencies if they're missing
4. **🚀 Launch**: Starts both API server (port 39583) and React frontend (port 5173)
5. **📊 Status**: Shows available asset files and provides access URLs

## Custom Port Usage

If you want to use a different port:

### Linux/Mac:
```bash
./start-dashboard.sh 8080    # Use port 8080 instead of 39583
```

### Windows:
```cmd
start-dashboard.bat 8080
```

## Expected Output

```
🚀 Crypto Trading Dashboard Startup Script
===========================================

✅ Found 7 asset position files
🎯 Starting Dashboard Services...
📍 Script location: /home/q/crypto-bot
📍 Dashboard location: /home/q/crypto-bot/dashboard/crypto-dashboard
📍 Asset positions: /home/q/crypto-bot/asset-positions

📊 Dashboard will be available at:
   🌐 Frontend: http://localhost:5173 (or next available port)
   🔗 API Server: http://localhost:39583

⏳ Starting servers with default ports...
💡 Press Ctrl+C to stop both servers
```

## Features of the Scripts

### Smart Error Handling
- ❌ Validates you're in the crypto-bot root directory
- ❌ Checks for required files (trade_loop.py, asset-positions/)
- ❌ Verifies dashboard installation
- ❌ Validates custom port numbers (1024-65535 range)

### Auto-Setup
- 📦 Installs npm dependencies if missing
- 📦 Installs server dependencies automatically
- 🔧 Sets up environment variables for custom ports

### User-Friendly
- 🎨 Color-coded output (Linux/Mac)
- 📊 Shows count of asset position files found
- ⚠️ Warnings for missing data
- 💡 Clear instructions and URLs

## Troubleshooting

### If the script fails:
1. **Make sure you're in the crypto-bot root directory**
   ```bash
   cd /path/to/your/crypto-bot
   ls -la  # Should see trade_loop.py, asset-positions/, etc.
   ```

2. **Check Node.js is installed**
   ```bash
   node --version  # Should show v16+ 
   npm --version   # Should show v8+
   ```

3. **Permissions (Linux/Mac)**
   ```bash
   chmod +x start-dashboard.sh
   ```

4. **Manual dashboard start (if script fails)**
   ```bash
   cd dashboard/crypto-dashboard
   npm install
   cd server && npm install && cd ..
   npm run dev:full
   ```

### Common Issues:
- **Port already in use**: Try a custom port with `./start-dashboard.sh 8080`
- **No asset files found**: Dashboard will work but show empty data until you have positions
- **npm errors**: Delete `node_modules` folders and run script again

## What You'll See

Once started, your dashboard will display:
- 📊 **Real-time portfolio overview** with current values
- 💹 **Live Binance prices** for all your assets  
- 🎯 **Unrealized P&L** calculations
- 📈 **Interactive charts** and visualizations
- 💼 **Detailed asset cards** with current prices
- 📋 **Complete transaction history**

**The dashboard automatically reads your actual trading data and fetches live market prices!** 🚀