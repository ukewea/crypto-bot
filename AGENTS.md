# AGENTS.md

This document provides guidance for AI agents (Claude Code, GitHub Copilot, etc.) when working with the crypto-bot repository. It outlines project conventions, development workflows, and architectural patterns to ensure consistent and effective assistance.

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

# Check code style
poetry run black --check .

# Run linting (if configured)
poetry run flake8 .
```

### Testing
```bash
# Run tests (when available)
poetry run pytest

# Test configuration loading
poetry run python -c "from bot_env_config.config import Config; Config()"
```

### Running the Bot
```bash
# Main entry point - starts the trading loop
python trade_loop.py

# Alternative entry points
python get_data.py  # Legacy entry point mentioned in README

# Container deployment
docker-compose up --build
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
- `execute_buy_order()` - Creates buy orders with fund limits (supports DCA and traditional strategies)
- `close_all_position()` - Liquidates all holdings of a currency
- Handles order validation, minimum notional requirements, and lot size filtering

### Strategy System

**analyzer/** - Pluggable strategy implementations
- `analyzer.py` - Base abstract class with `Trade` enum (PASS/BUY/SELL)
- `RSI_Analyzer.py`, `WILLR_Analyzer.py` - Technical indicator strategies
- `DCA_Buy_Analyzer.py`, `DCA_Sell_Analyzer.py` - Dollar-cost averaging strategies
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
- `position-manage.json` - Cash currency, position limits, trading behavior, include/exclude lists
- `bot.json` - Notification platform settings
- `credentials.json` - Google Sheets service account
- `logging.ini` - Logging configuration

### Position Accumulation Strategies

The `position_accumulation_strategy` setting in `position-manage.json` controls how the bot handles existing positions when buy signals are generated:

**"hold_until_sell" (Traditional):**
- **Pattern**: Buy → Hold → Sell
- **Behavior**: Skip all buy signals while holding a position
- **Use case**: Technical analysis strategies (RSI, WILLR) that expect holding periods
- **Example**: Buy when RSI oversold, hold until RSI overbought, then sell

**"accumulate" (DCA-friendly):**
- **Pattern**: Buy → Buy → Buy (continuous accumulation)
- **Behavior**: Allow multiple buys to build larger positions over time
- **Use case**: Dollar-cost averaging and systematic accumulation strategies
- **Example**: DCA analyzer buying $10 every hour regardless of existing positions

```json
{
  "position_accumulation_strategy": "accumulate"  // For DCA strategies
  "position_accumulation_strategy": "hold_until_sell"  // For technical analysis
}
```

### Key Design Patterns

- **Strategy Pattern**: Analyzers are pluggable via dynamic module loading
- **Position Management**: Enforces max fund per order, max open positions, total cost limits
- **Graceful Shutdown**: Signal handling ensures clean state persistence
- **Error Recovery**: Extensive exception handling with logging, continues operation on API failures
- **Rate Limiting**: Built-in delays between API calls and symbol processing

### Important Constraints
- Only processes symbols where account has balance visibility
- Respects Binance lot size, notional, and quantity filters
- Maintains transaction history in local JSON for auditability
- Supports both live trading and mock trading modes

### Order Execution Behavior

**Why Order Amounts Vary from `max_fund_per_order`:**

The bot's order execution system prioritizes **exchange compliance** over exact dollar amounts. When placing orders, the actual cost may differ from the configured `max_fund_per_order` due to Binance's trading rules:

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

## Development Conventions

### File Naming
- Analyzer classes: `{Type}_Analyzer.py` (e.g., `RSI_Analyzer.py`, `DCA_Buy_Analyzer.py`)
- Configuration files: `{purpose}.json` in `user-config/`
- API wrappers: `{exchange}_{function}.py` (e.g., `binance_trading.py`)

### Code Style
- Use Python snake_case for variables and functions
- Class names in PascalCase
- Constants in UPPER_SNAKE_CASE
- Comprehensive logging with structured messages

### Configuration Management
- Never commit actual API keys or credentials
- Use `user-config-sample/` for templates
- Support both live and mock trading modes
- Validate configuration on startup

## Trading Strategy Development

### Adding New Analyzers
1. Inherit from `analyzer.Analyzer` base class
2. Implement `analyze(klines, position)` method
3. Return `Trade.BUY`, `Trade.SELL`, or `Trade.PASS`
4. Add configuration section to `analyzer.json`
5. Update `config.py` if needed for dynamic loading

### Analyzer Types Available
- **RSI_Analyzer**: Relative Strength Index technical analysis
- **WILLR_Analyzer**: Williams %R technical analysis
- **DCA_Buy_Analyzer**: Dollar-cost averaging buy strategy
- **DCA_Sell_Analyzer**: Dollar-cost averaging sell strategy

### Configuration Examples
```json
// Technical Analysis Strategy
{
    "type": "RSI",
    "RSI": {"period": 14, "underbuy": 30, "oversell": 70}
}

// DCA Buy Strategy
{
    "type": "DCA_Buy",
    "DCA": {"min_interval_between_buy": 3600}
}

// DCA Sell Strategy
{
    "type": "DCA_Sell", 
    "DCA": {"min_interval_between_sell": 7200}
}
```

## Error Handling & Safety

### Error Recovery
- Extensive exception handling with logging
- Continues operation on API failures
- Rate limiting with built-in delays
- Transaction rollback on critical failures

### Safety Mechanisms
- Mock trading mode for safe testing
- Position limits to prevent overexposure
- Graceful shutdown to preserve state
- Transaction logging for audit trails

## Security Considerations

- API keys stored in `user-config/auth.json` (not committed)
- Support for testnet and live trading modes
- Transaction logging for audit trails
- No exposure of sensitive data in logs

## Common Pitfalls

1. **Order Rejection**: Always respect exchange filters (minimum quantity, notional value)
2. **Position Tracking**: Don't bypass the position management system
3. **Configuration**: Validate JSON syntax and required fields
4. **Rate Limits**: Respect Binance API rate limits with delays
5. **Graceful Shutdown**: Use proper shutdown mechanisms to avoid state corruption

## Testing Strategies

### Mock Trading Mode
- Set `"trading_mode": "mock_trading"` in `position-manage.json`
- Uses real market data but simulates trades
- Safe for strategy development and testing

### Configuration Testing
```python
from bot_env_config.config import Config
config = Config()
analyzer = config.spawn_analyzer()
```

### Component Testing
- Test analyzers with historical kline data
- Validate position calculations
- Check configuration loading and validation

## Deployment

### Docker
```bash
# Build container
docker build -t crypto-bot:latest .

# Run with docker-compose
docker-compose up -d
```

### Production Checklist
- [ ] API keys configured and tested
- [ ] Trading mode set correctly (`binance_trading` for live)
- [ ] Position limits configured appropriately
- [ ] Notification platforms configured
- [ ] Google Sheets integration (optional) configured
- [ ] Graceful shutdown mechanism tested
- [ ] Log monitoring in place

## Documentation Updates

When modifying the codebase:
1. Update `CLAUDE.md` for major architectural changes
2. Update configuration examples in `user-config-sample/`
3. Document new analyzer types and their parameters
4. Update Docker configuration if dependencies change
5. Maintain this `AGENTS.md` file for AI agent guidance

---

*This document should be updated whenever significant architectural changes, new patterns, or development conventions are introduced to the project.*