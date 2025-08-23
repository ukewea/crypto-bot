# Unit Tests for Crypto-Bot

This directory contains comprehensive unit tests for the crypto-bot project, ensuring code quality and preventing regressions.

## Test Structure

### `test_file_based_asset_positions.py`
Comprehensive tests for the `file_based_asset_positions.py` module covering:

### `test_mock_trading.py`  
Extensive tests for the `exchange_api_wrappers/mock_trading.py` module covering:

#### **MockTradingWrapper Initialization**
- ✅ Empty directory setup with auto-funding
- ✅ Loading existing position data
- ✅ Directory creation and file management
- ✅ Cash currency auto-funding mechanism

#### **Trading Operations**
- ✅ Buy and sell order execution
- ✅ Market order processing with Binance price feeds
- ✅ Order validation (symbol format, order types, sides)
- ✅ Error handling for invalid orders and API failures

#### **Position Management**
- ✅ Balance updates after buy/sell operations
- ✅ Multi-asset trading (BTC, ETH, DOGE)
- ✅ High precision decimal handling
- ✅ Position accumulation over multiple trades

#### **Data Persistence**
- ✅ JSON file persistence after each order
- ✅ Data integrity across wrapper instances
- ✅ Concurrent access simulation
- ✅ Serialization with decimal precision

#### **Integration Testing**
- ✅ Complete DCA trading scenarios
- ✅ Round-trip trading (buy then sell)
- ✅ Realistic multi-asset portfolio simulation

#### **Initialization & File Operations**
- ✅ Empty directory initialization
- ✅ Loading existing position files  
- ✅ Directory creation when missing
- ✅ File permission error handling
- ✅ Invalid JSON file handling

#### **Portfolio Calculations**
- ✅ Total open position count (empty & with positions)
- ✅ Total open cost calculation
- ✅ Total commission calculation
- ✅ Transaction count tracking

#### **P&L Calculation Engine**
- ✅ Empty portfolio P&L calculation
- ✅ Profitable positions with gains
- ✅ Losing positions with losses
- ✅ Multiple assets portfolio
- ✅ Missing market price handling
- ✅ Zero cost position edge case
- ✅ Zero quantity position handling
- ✅ High precision decimal values
- ✅ Different cash currencies

#### **Message Formatting**
- ✅ Basic P&L snapshot formatting
- ✅ Negative P&L formatting with proper signs
- ✅ Empty portfolio message formatting
- ✅ Multi-asset portfolio formatting

#### **Error Handling & Edge Cases**
- ✅ File permission errors
- ✅ JSON parsing errors
- ✅ Missing market data
- ✅ Zero/negative values
- ✅ High precision decimals
- ✅ Logging integration

#### **Integration Tests**
- ✅ Complete P&L workflow from file loading to message formatting
- ✅ Realistic multi-asset portfolio scenarios
- ✅ End-to-end calculation validation

## Running Tests

### Option 1: Using the test runner (Recommended)
```bash
python run_tests.py
```

### Option 2: Direct unittest execution
```bash
python -m unittest tests.test_file_based_asset_positions -v
```

### Option 3: Specific test modules
```bash
python -m unittest tests.test_file_based_asset_positions -v
python -m unittest tests.test_mock_trading -v
```

### Option 4: Specific test classes
```bash
python -m unittest tests.test_file_based_asset_positions.TestAssetPositions -v
python -m unittest tests.test_mock_trading.TestMockTradingWrapper -v
```

### Option 5: Individual test methods
```bash
python -m unittest tests.test_file_based_asset_positions.TestAssetPositions.test_cal_portfolio_pnl_with_gains -v
python -m unittest tests.test_mock_trading.TestMockTradingWrapper.test_order_qty_buy_order_basic -v
```

## Test Coverage

The test suite covers **47 comprehensive test scenarios** with:

| Category | Tests | Coverage |
|----------|-------|----------|
| **Asset Positions** | 25 | File operations, P&L calculations, message formatting |
| **Mock Trading** | 22 | Trading operations, position management, data persistence |
| **Total Coverage** | **47** | **Complete production-ready test suite** |

### **Detailed Breakdown:**

#### **Asset Positions Module (25 tests)**
- **Initialization** | 4 tests | File loading, directory creation, error handling
- **Basic Calculations** | 6 tests | Position counts, costs, commissions, transactions  
- **P&L Engine** | 8 tests | All market scenarios including edge cases
- **Message Formatting** | 4 tests | All formatting scenarios with +/- values
- **Error Handling** | 2 tests | File errors, permissions, invalid data
- **Integration** | 1 test | End-to-end workflow validation

#### **Mock Trading Module (22 tests)**
- **Initialization** | 3 tests | Setup, auto-funding, data loading
- **Trading Operations** | 7 tests | Buy/sell orders, validation, error handling
- **Position Management** | 6 tests | Balance updates, multi-asset, precision
- **Data Persistence** | 4 tests | File operations, concurrency, serialization
- **Integration** | 2 tests | Complete trading scenarios, round-trip operations

## Test Data & Scenarios

### **Market Scenarios Tested**
- 📈 **Bull Market**: Assets gaining 10-90%+ 
- 📉 **Bear Market**: Assets losing 5-20%
- ⚖️ **Mixed Market**: Some gains, some losses
- 🎯 **Edge Cases**: Zero cost, zero quantity, missing prices

### **Portfolio Configurations**
- **Empty Portfolio**: No positions
- **Single Asset**: BTC only
- **Multi-Asset**: BTC, ETH, DOGE, ADA, SOL, SUI, XRP
- **High Precision**: Tiny quantities with 8+ decimal places

### **Error Conditions**
- **File System**: Permission errors, missing directories
- **Data Format**: Invalid JSON, corrupted files
- **Market Data**: Missing prices, stale data
- **Edge Cases**: Division by zero, null values

## Benefits of These Tests

### **🛡️ Regression Prevention**
- Prevents breaking existing functionality during updates
- Validates calculations with known good values
- Catches edge cases before production

### **📊 Accurate Financial Calculations**
- Ensures P&L calculations match expected values
- Validates percentage calculations and formatting
- Tests decimal precision for cryptocurrency amounts

### **🔒 Error Resilience**
- Handles file system errors gracefully
- Manages missing or corrupted data
- Provides fallbacks for edge cases

### **🚀 Confidence in Deployment**
- All 25 tests must pass before deployment
- Covers critical financial calculation paths
- Validates real-world usage scenarios

## Adding New Tests

When extending the codebase:

1. **Add new test methods** for new functionality
2. **Update existing tests** when changing behavior
3. **Test edge cases** especially for financial calculations
4. **Mock external dependencies** (file system, network)
5. **Use descriptive test names** explaining what's being tested

### Example Test Template
```python
def test_new_feature_scenario(self):
    """Test description explaining the scenario."""
    # Arrange: Set up test data
    test_data = {...}
    
    # Act: Execute the code under test
    result = asset_positions.new_method(test_data)
    
    # Assert: Verify expected outcomes
    self.assertEqual(result.expected_field, expected_value)
    self.assertTrue(result.success)
```

## Continuous Integration

These tests should be run:
- ✅ Before every commit
- ✅ In CI/CD pipelines  
- ✅ Before production deployments
- ✅ After dependency updates

---

*Keep the tests updated and comprehensive to maintain code quality and prevent financial calculation errors!*