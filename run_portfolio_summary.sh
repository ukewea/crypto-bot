#!/bin/bash
# Portfolio Summary Runner
# Quick script to run the portfolio summary calculation

set -e

echo "🚀 Running Portfolio Summary..."
echo "=================================="

# Check if poetry is available
if command -v poetry >/dev/null 2>&1; then
    echo "📦 Using Poetry to run script..."
    poetry run python portfolio_summary.py
else
    echo "🐍 Using Python directly..."
    python portfolio_summary.py
fi

echo "=================================="
echo "✅ Portfolio Summary Complete!"