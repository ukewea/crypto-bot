#!/bin/bash

# Crypto Trading Dashboard Startup Script
# This script starts both the API server and React frontend

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="$SCRIPT_DIR/dashboard/crypto-dashboard"

echo -e "${BLUE}🚀 Crypto Trading Dashboard Startup Script${NC}"
echo -e "${BLUE}===========================================${NC}"
echo ""

# Check if we're in the right directory (crypto-bot root)
if [[ ! -f "$SCRIPT_DIR/trade_loop.py" ]] || [[ ! -d "$SCRIPT_DIR/asset-positions" ]]; then
    echo -e "${RED}❌ Error: This script must be run from the crypto-bot repository root${NC}"
    echo -e "${YELLOW}   Expected files: trade_loop.py, asset-positions/ directory${NC}"
    echo -e "${YELLOW}   Current directory: $SCRIPT_DIR${NC}"
    exit 1
fi

# Check if dashboard directory exists
if [[ ! -d "$DASHBOARD_DIR" ]]; then
    echo -e "${RED}❌ Error: Dashboard directory not found${NC}"
    echo -e "${YELLOW}   Expected: $DASHBOARD_DIR${NC}"
    echo -e "${YELLOW}   Please make sure the dashboard is properly installed${NC}"
    exit 1
fi

# Check if package.json exists
if [[ ! -f "$DASHBOARD_DIR/package.json" ]]; then
    echo -e "${RED}❌ Error: package.json not found in dashboard directory${NC}"
    echo -e "${YELLOW}   Expected: $DASHBOARD_DIR/package.json${NC}"
    exit 1
fi

# Check if node_modules exists, if not, install dependencies
if [[ ! -d "$DASHBOARD_DIR/node_modules" ]]; then
    echo -e "${YELLOW}📦 Dependencies not found. Installing...${NC}"
    cd "$DASHBOARD_DIR"
    npm install
    
    # Also install server dependencies
    if [[ -d "server" ]] && [[ ! -d "server/node_modules" ]]; then
        echo -e "${YELLOW}📦 Installing server dependencies...${NC}"
        cd server
        npm install
        cd ..
    fi
    cd "$SCRIPT_DIR"
fi

# Check if asset-positions directory has data
ASSET_COUNT=$(find "$SCRIPT_DIR/asset-positions" -name "*.json" 2>/dev/null | wc -l)
if [[ $ASSET_COUNT -eq 0 ]]; then
    echo -e "${YELLOW}⚠️  Warning: No asset position files found in asset-positions/${NC}"
    echo -e "${YELLOW}   The dashboard will show empty data until you have trading positions${NC}"
else
    echo -e "${GREEN}✅ Found $ASSET_COUNT asset position files${NC}"
fi

# Check if custom port is requested
if [[ -n "$1" ]]; then
    if [[ "$1" =~ ^[0-9]+$ ]] && [[ "$1" -ge 1024 ]] && [[ "$1" -le 65535 ]]; then
        CUSTOM_PORT="$1"
        echo -e "${BLUE}🔧 Using custom port: $CUSTOM_PORT${NC}"
    else
        echo -e "${RED}❌ Error: Invalid port number '$1'${NC}"
        echo -e "${YELLOW}   Port must be a number between 1024-65535${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}🎯 Starting Dashboard Services...${NC}"
echo -e "${BLUE}📍 Script location: $SCRIPT_DIR${NC}"
echo -e "${BLUE}📍 Dashboard location: $DASHBOARD_DIR${NC}"
echo -e "${BLUE}📍 Asset positions: $SCRIPT_DIR/asset-positions${NC}"

# Display startup information
echo ""
echo -e "${GREEN}📊 Dashboard will be available at:${NC}"
if [[ -n "$CUSTOM_PORT" ]]; then
    echo -e "${GREEN}   🌐 Frontend: http://localhost:5173 (or next available port)${NC}"
    echo -e "${GREEN}   🔗 API Server: http://localhost:$CUSTOM_PORT${NC}"
    echo ""
    echo -e "${YELLOW}⏳ Starting servers with custom port $CUSTOM_PORT...${NC}"
else
    echo -e "${GREEN}   🌐 Frontend: http://localhost:5173 (or next available port)${NC}"
    echo -e "${GREEN}   🔗 API Server: http://localhost:39583${NC}"
    echo ""
    echo -e "${YELLOW}⏳ Starting servers with default ports...${NC}"
fi

echo -e "${BLUE}💡 Press Ctrl+C to stop both servers${NC}"
echo ""

# Change to dashboard directory and start the servers
cd "$DASHBOARD_DIR"

if [[ -n "$CUSTOM_PORT" ]]; then
    # Start with custom port
    export PORT="$CUSTOM_PORT"
    export VITE_API_PORT="$CUSTOM_PORT"
    npm run dev:port
else
    # Start with default ports
    npm run dev:full
fi