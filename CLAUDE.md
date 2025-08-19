# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python cryptocurrency trading bot that automatically trades on Binance using customized strategies based on technical analysis indicators (RSI, Williams %R). The bot operates 24/7 and includes features for position management, transaction reporting to Google Sheets, and push notifications.

## Common Commands

### Dependency Management
```bash
# Install dependencies
poetry install

# Run with poetry
poetry run python trade_loop.py

# Alternative with pip
pip install -r requirements.txt
python trade_loop.py
```

### Code Quality
```bash
# Format code (Black is configured)
poetry run black .
```

### Running the Bot
```bash
# Main entry point - starts the trading loop
python trade_loop.py

# Alternative entry points
python get_data.py  # Legacy entry point mentioned in README
```

### Graceful Shutdown
- Create a file named `stoppp` in root directory, or
- Use Ctrl+C (SIGINT) or kill command (SIGTERM)
- Never use `kill -9` as it corrupts position management

## Architecture

### Core Components

**trade_loop.py** - Main entry point containing the trading loop (`TradeLoopRunner` class)
- Runs continuous 60-second cycles analyzing all configured cryptocurrencies
- Handles graceful shutdown via signal handlers
- Manages position limits and cash flow

**send_order.py** - Binance API integration for order execution
- `open_position_with_max_fund()` - Creates buy orders with fund limits
- `close_all_position()` - Liquidates all holdings of a currency
- Handles order validation, minimum notional requirements, and lot size filtering

### Strategy System

**analyzer/** - Pluggable strategy implementations
- `analyzer.py` - Base abstract class with `Trade` enum (PASS/BUY/SELL)
- `RSI_Analyzer.py`, `WILLR_Analyzer.py` - Technical indicator strategies
- New strategies must inherit from `Analyzer` and implement `analyze(klines, position)`

### Infrastructure

**exchange_api_wrappers/** - Binance API abstraction layer
- `crypto.py` - Main API wrapper interface
- `binance_trading.py`, `binance_klines.py` - Live trading implementations
- `mock_trading.py` - Paper trading for testing

**asset_record_platforms/** - Position tracking system
- `file_based_asset_positions.py` - Local JSON-based position storage
- `position.py` - Transaction and position data structures
- Maintains trading history for version control

**notification_platforms/** - Push notification system
- `discord_bot.py`, `telegram_bot.py` - Platform-specific implementations
- `queue_task.py` - Async notification queue management

**bot_env_config/** - Configuration management
- `config.py` - Loads JSON configs from `user-config/` directory
- Handles API keys, strategy parameters, position limits, notification settings

### Configuration Files Structure
Located in `user-config/` (copy from `user-config-sample/`):
- `auth.json` - Binance API credentials, Google Sheets API
- `analyzer.json` - Strategy type and parameters
- `position-manage.json` - Cash currency, position limits, include/exclude lists
- `bot.json` - Notification platform settings
- `credentials.json` - Google Sheets service account
- `logging.ini` - Logging configuration

### Key Design Patterns

- **Strategy Pattern**: Analyzers are pluggable via dynamic module loading
- **Position Management**: Enforces max fund per currency, max open positions, total cost limits
- **Graceful Shutdown**: Signal handling ensures clean state persistence
- **Error Recovery**: Extensive exception handling with logging, continues operation on API failures
- **Rate Limiting**: Built-in delays between API calls and symbol processing

### Important Constraints
- Only processes symbols where account has balance visibility
- Respects Binance lot size, notional, and quantity filters
- Maintains transaction history in local JSON for auditability
- Supports both live trading and mock trading modes

### Order Execution Behavior

**Why Order Amounts Vary from `max_fund_per_currency`:**

The bot's order execution system prioritizes **exchange compliance** over exact dollar amounts. When placing orders, the actual cost may differ from the configured `max_fund_per_currency` due to Binance's trading rules:

1. **LOT_SIZE Filter Compliance**: Each trading pair has specific quantity restrictions
   - `minQty`: Minimum quantity per order
   - `maxQty`: Maximum quantity per order  
   - `stepSize`: Quantity must be a multiple of this value

2. **Order Calculation Process** (`send_order.py:82-95`):
   ```
   max_buyable_quantity = max_fund ÷ current_price
   rounded_quantity = max_buyable_quantity - (max_buyable_quantity % step_size)
   actual_cost = rounded_quantity × execution_price
   ```

3. **Typical Variance Examples**:
   - Target: $10.00 → Actual: $9.25 (BTC) - 7.5% under due to strict step size
   - Target: $10.00 → Actual: $9.90 (ETH) - 1% under due to favorable step size
   - Target: $10.00 → Actual: $9.92 (DOGE) - 0.8% under due to rounding

4. **Additional Factors**:
   - **NOTIONAL Filter**: Minimum order value requirements
   - **Price Fluctuations**: Price may change between calculation and execution
   - **Quantity Rounding**: Always rounds down to ensure exchange acceptance

**Design Rationale**: This approach ensures orders are never rejected by the exchange due to filter violations, which is more reliable than attempting exact dollar amounts that might fail. The variance is typically small (within 10% of target) and represents successful market execution rather than system error.