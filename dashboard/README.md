# Crypto Trading Dashboard

A beautiful React TypeScript dashboard for monitoring cryptocurrency trading bot positions and performance.

## Features

- **📊 Enhanced Portfolio Overview**: Real-time summary with current market values
  - Total current portfolio value (live market prices)
  - Realized vs Unrealized P&L breakdown
  - Total return percentage with live price updates
  
- **💹 Live Market Integration**: 
  - **Binance API Integration**: Fetches current USDT prices for all assets
  - **Unrealized P&L Calculation**: Real-time gains/losses on open positions
  - **Current Value Display**: Live portfolio worth vs cost basis
  
- **🎯 Enhanced Asset Cards**: Individual asset performance with:
  - Current market price with "LIVE" indicator
  - Unrealized P&L (market price vs average buy price)  
  - Total P&L (realized + unrealized combined)
  - Current value vs total cost comparison
  
- **📈 Advanced Charts**: 
  - Portfolio allocation by current market value
  - Multi-bar performance chart (Cost vs Current Value vs P&L)
  - Color-coded profit/loss visualization
  
- **🔄 Smart Data Management**:
  - **30-second price caching** to avoid API rate limits
  - **Automatic price refresh** every time you refresh the dashboard
  - **Fallback handling** if Binance API is unavailable
  
- **📱 Responsive Design**: Works on desktop, tablet, and mobile devices
- **🚀 Real-time Updates**: Dynamic loading from asset-positions folder

## Screenshots

### Dashboard Overview
- Portfolio summary cards with total value, cost, and P&L
- Beautiful gradient backgrounds and responsive grid layout
- Asset cards showing holdings, average buy price, and realized P&L

### Asset Details
- Modal popup with detailed asset information
- Transaction history table with sorting and filtering
- Trading activity metrics and performance charts

### Data Visualization
- Portfolio allocation pie chart
- Asset performance comparison bar chart
- Interactive tooltips with detailed information

## Technology Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling and responsive design
- **Recharts** for data visualization
- **Lucide React** for icons
- **Modern ES6+** features and hooks

## Installation & Setup

### Quick Start (Dynamic Data Loading)

1. Navigate to the dashboard directory:
   ```bash
   cd dashboard/crypto-dashboard
   ```

2. Install dependencies for both frontend and backend:
   ```bash
   npm install
   cd server && npm install && cd ..
   ```

3. Start both servers (API backend + React frontend):
   ```bash
   npm run dev:full
   ```

4. Open your browser and visit `http://localhost:5173`

The dashboard will now **automatically load your actual asset position data** from the `asset-positions/` folder!

### Manual Setup (Individual Servers)

If you prefer to run servers separately:

1. **Start the API server** (in one terminal):
   ```bash
   cd server
   npm run dev
   ```

2. **Start the React app** (in another terminal):
   ```bash
   npm run dev
   ```

### Production Deployment

```bash
npm run build              # Build React app
npm run start:full         # Run both servers in production mode
```

## Configuration

### Dynamic Data Loading

✅ **SOLVED!** The dashboard now automatically reads your actual asset position files!

**How it works:**
1. **Node.js API Server** (`server/index.js`) runs on port **39583** and reads JSON files from `../../../asset-positions/`
2. **File Watching** automatically detects changes to your position files
3. **Real-time Updates** when your trading bot updates positions
4. **Automatic Refresh** button to manually reload data

**Supported files:** BTC.json, ETH.json, ADA.json, DOGE.json, SOL.json, SUI.json, XRP.json (and any new assets you add)

### Asset Position File Format
The dashboard expects JSON files with this structure:
```json
{
  "open_quantity": "0.00056",
  "open_cost": "64.0764680000000", 
  "realized_gain": "0.0",
  "total_commission_as_usdt": "0.0",
  "transactions": [
    {
      "time": "1755611608285",
      "activity": "BUY",
      "symbol": "BTC",
      "trade_symbol": "BTCUSDT",
      "quantity": "0.00008",
      "price": "115239.81000000",
      "commission": "0.0",
      "commission_asset": "USDT",
      "commission_as_usdt": "0.0",
      "round_id": "1755611608134542533",
      "order_id": "11276951932476010528",
      "trade_id": "13329001597177739616",
      "closed_trade_ids": []
    }
  ]
}
```

## Available Scripts

### Frontend & Backend Combined
- `npm run dev:full` - Start both API server and React dev server
- `npm run start:full` - Start both servers in production mode

### Individual Components  
- `npm run dev` - Start React development server only
- `npm run build` - Build React app for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run server` - Start API server in development mode
- `npm run start:server` - Start API server in production mode

## Features Breakdown

### Portfolio Summary
- **Total Value**: Current portfolio worth (placeholder for real-time market data)
- **Total Cost**: Amount invested across all positions
- **Total P&L**: Realized gains/losses
- **P&L Percentage**: Return on investment percentage

### Asset Cards
- **Holdings**: Current quantity held
- **Total Cost**: Total amount invested in the asset
- **Average Buy Price**: Cost basis per unit
- **Realized P&L**: Profit/loss from completed trades
- **Transaction Count**: Number of buy/sell orders
- **Last Transaction**: Most recent trading activity

### Transaction History
- Chronological list of all buy/sell transactions
- Sortable by date, type, quantity, price, and total value
- Color-coded for easy identification (green for buys, red for sells)
- Detailed information including timestamps, order IDs, and trade IDs

### Charts and Visualizations
- **Portfolio Allocation Pie Chart**: Shows distribution of investment across assets
- **Performance Bar Chart**: Compares cost vs realized P&L for each asset
- Interactive tooltips with detailed information
- Responsive design that adapts to screen size

## Customization

### Styling
- Built with Tailwind CSS for easy customization
- Gradient backgrounds and modern design
- Consistent color scheme throughout the application
- Responsive breakpoints for all device sizes

### Data Processing
- Modular utilities for parsing and calculating metrics
- Extensible architecture for adding new data sources
- Error handling and loading states
- TypeScript interfaces for type safety

## Future Enhancements

- **Real-time Market Data**: Integration with cryptocurrency APIs for current prices
- **Advanced Charts**: Candlestick charts, moving averages, and technical indicators
- **Export Features**: PDF reports, CSV exports, and data backup
- **Notifications**: Alerts for significant P&L changes or trading activity
- **Multi-timeframe Analysis**: Daily, weekly, monthly performance views
- **Advanced Filtering**: Filter by date range, asset type, or transaction size

## Integration with Trading Bot

The dashboard is designed to work seamlessly with the crypto trading bot:

1. **Automatic Data Updates**: Reads from the same asset-positions folder used by the bot
2. **Real-time Sync**: Updates as new transactions are recorded
3. **Consistent Data Format**: Uses the same JSON structure as the bot
4. **No Interference**: Read-only access to position data

## Port Configuration

### Changing the API Port

You can easily change the backend port using environment variables:

**Method 1: Using .env file (Recommended)**
```bash
# Copy the example file
cp .env.example .env

# Edit .env file and set:
VITE_API_PORT=12345

# Then run normally
npm run dev:full
```

**Method 2: Using environment variables directly**
```bash
# Both frontend and backend will use port 12345
VITE_API_PORT=12345 PORT=12345 npm run dev:full

# Or use the convenient script
PORT=12345 npm run dev:port
```

**Method 3: Backend only (⚠️ Not recommended)**
```bash
# This only changes backend - frontend won't connect unless you also set VITE_API_PORT
PORT=12345 npm run dev:full  # ❌ Won't work - frontend still connects to 39583

# Correct way:
PORT=12345 VITE_API_PORT=12345 npm run dev:full  # ✅ Works
```

**Available Scripts for Custom Ports:**
- `npm run dev:port` - Runs both servers with $PORT environment variable
- `npm run start:port` - Production mode with custom port

## Troubleshooting

### Common Issues

1. **No data showing**: Check that asset position files exist in the expected format
2. **Charts not displaying**: Ensure Recharts is properly installed and imported
3. **Styling issues**: Verify Tailwind CSS is configured correctly
4. **TypeScript errors**: Check that all types are properly imported and defined

### Development Tips

- Use browser developer tools to debug data loading issues
- Check the console for any error messages
- Verify that the asset data structure matches expected TypeScript interfaces
- Test with different screen sizes using responsive design tools

## License

This dashboard is part of the crypto trading bot project and follows the same licensing terms.