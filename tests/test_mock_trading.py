#!/usr/bin/env python3
"""
Unit tests for exchange_api_wrappers/mock_trading.py

This module contains tests for:
- MockTradingWrapper initialization and configuration
- Mock trading operations (buy/sell orders)
- Balance management and position tracking
- Data persistence and file operations
- Integration with Binance price feeds
"""

import unittest
import tempfile
import shutil
import json
import os
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from exchange_api_wrappers.mock_trading import MockTradingWrapper
from exchange_api_wrappers.wrapped_data import WatchingSymbol, AssetBalance
from binance.enums import *
import bot_env_config.config


class TestMockTradingWrapper(unittest.TestCase):
    """Test cases for MockTradingWrapper class"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create temporary directory for mock data storage
        self.test_dir = tempfile.mkdtemp()
        self.original_base_dir = MockTradingWrapper.BASE_DIR
        MockTradingWrapper.BASE_DIR = self.test_dir
        
        # Mock configuration
        self.mock_config = Mock()
        self.mock_config.position_manage = {'cash_currency': 'USDT'}
        
        # Mock Binance quote wrapper
        self.mock_binance_quote = Mock()
        self.mock_binance_quote.get_latest_price.return_value = {'price': '50000.00'}
        
        # Sample watching symbols
        self.watching_symbols = [
            WatchingSymbol(symbol="BTCUSDT", base_asset="BTC", info={}),
            WatchingSymbol(symbol="ETHUSDT", base_asset="ETH", info={}),
            WatchingSymbol(symbol="DOGEUSDT", base_asset="DOGE", info={})
        ]

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original BASE_DIR
        MockTradingWrapper.BASE_DIR = self.original_base_dir
        # Remove temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_mock_record_file(self, positions=None):
        """Helper method to create a mock record file."""
        if positions is None:
            positions = {
                "USDT": "10000.00",
                "BTC": "0.001",
                "ETH": "0.1"
            }
        
        record_data = {"positions": positions}
        record_path = os.path.join(self.test_dir, "mock-record.json")
        
        with open(record_path, 'w') as f:
            json.dump(record_data, f)
        
        return record_path

    def test_initialization_empty_directory(self):
        """Test MockTradingWrapper initialization with empty directory."""
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        # Should create directory
        self.assertTrue(os.path.exists(self.test_dir))
        self.assertTrue(os.path.isdir(self.test_dir))
        
        # Should have initial cash funding
        balances = wrapper.get_equities_balance([], "USDT")
        self.assertIn("USDT", balances)
        self.assertEqual(balances["USDT"].free, Decimal('10000000000'))  # Initial funding

    def test_initialization_with_existing_data(self):
        """Test MockTradingWrapper initialization with existing mock record."""
        # Create existing mock record
        self.create_mock_record_file({
            "USDT": "5000.00",
            "BTC": "0.05",
            "ETH": "0.25"
        })
        
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        # Should load existing positions
        balances = wrapper.get_equities_balance(self.watching_symbols, "USDT")
        
        self.assertEqual(balances["USDT"].free, Decimal('5000.00'))
        self.assertEqual(balances["BTC"].free, Decimal('0.05'))
        self.assertEqual(balances["ETH"].free, Decimal('0.25'))

    def test_get_equities_balance_basic(self):
        """Test basic equity balance retrieval."""
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        balances = wrapper.get_equities_balance(self.watching_symbols, "USDT")
        
        # Should return balances for cash currency and all watching symbols
        expected_assets = ["USDT", "BTC", "ETH", "DOGE"]
        self.assertEqual(set(balances.keys()), set(expected_assets))
        
        # All balances should be AssetBalance objects
        for asset, balance in balances.items():
            self.assertIsInstance(balance, AssetBalance)
            self.assertEqual(balance.asset, asset)
            self.assertEqual(balance.locked, Decimal('0'))

    def test_get_equities_balance_missing_cash_currency(self):
        """Test equity balance retrieval when cash currency is missing - should auto-fund."""
        # Create wrapper with positions file that doesn't include USDT
        self.create_mock_record_file({"BTC": "0.001"})
        
        # Should not raise exception - constructor auto-funds missing cash currency
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        # Should have auto-funded USDT
        balances = wrapper.get_equities_balance(self.watching_symbols, "USDT")
        self.assertIn("USDT", balances)
        self.assertEqual(balances["USDT"].free, Decimal('10000000000'))  # Initial funding
        
        # Should also have the existing BTC position
        self.assertEqual(balances["BTC"].free, Decimal('0.001'))

    def test_get_equities_balance_new_symbols(self):
        """Test equity balance retrieval for new/untraded symbols."""
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        # Add new symbol not in positions
        new_symbols = self.watching_symbols + [
            WatchingSymbol(symbol="SOLUSDT", base_asset="SOL", info={})
        ]
        
        balances = wrapper.get_equities_balance(new_symbols, "USDT")
        
        # Should return zero balance for new symbol
        self.assertIn("SOL", balances)
        self.assertEqual(balances["SOL"].free, Decimal('0'))
        self.assertEqual(balances["SOL"].asset, "SOL")

    def test_order_qty_buy_order_basic(self):
        """Test basic buy order execution."""
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        # Execute buy order
        success, order = wrapper.order_qty(
            side=SIDE_BUY,
            quantity="0.001",
            symbol="BTCUSDT",
            order_type=ORDER_TYPE_MARKET
        )
        
        # Should succeed
        self.assertTrue(success)
        self.assertIsNotNone(order)
        
        # Verify order structure
        self.assertEqual(order["symbol"], "BTCUSDT")
        self.assertEqual(order["side"], SIDE_BUY)
        self.assertEqual(order["type"], ORDER_TYPE_MARKET)
        self.assertEqual(order["status"], "FILLED")
        self.assertEqual(order["executedQty"], "0.001")
        
        # Verify fills
        self.assertEqual(len(order["fills"]), 1)
        fill = order["fills"][0]
        self.assertEqual(fill["price"], "50000.00")  # From mock
        self.assertEqual(fill["qty"], "0.001")

    def test_order_qty_sell_order_basic(self):
        """Test basic sell order execution."""
        # Set up wrapper with existing BTC position
        self.create_mock_record_file({
            "USDT": "1000.00",
            "BTC": "0.01"
        })
        
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        # Execute sell order
        success, order = wrapper.order_qty(
            side=SIDE_SELL,
            quantity="0.005",
            symbol="BTCUSDT",
            order_type=ORDER_TYPE_MARKET
        )
        
        # Should succeed
        self.assertTrue(success)
        self.assertIsNotNone(order)
        
        # Verify order structure
        self.assertEqual(order["symbol"], "BTCUSDT")
        self.assertEqual(order["side"], SIDE_SELL)
        self.assertEqual(order["executedQty"], "0.005")

    def test_order_qty_invalid_symbol(self):
        """Test order execution with invalid symbol (not ending with cash currency)."""
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        with self.assertRaises(Exception) as context:
            wrapper.order_qty(
                side=SIDE_BUY,
                quantity="0.001",
                symbol="BTCETH",  # Invalid - doesn't end with USDT
                order_type=ORDER_TYPE_MARKET
            )
        
        self.assertIn("symbol not end with USDT", str(context.exception))

    def test_order_qty_unsupported_order_type(self):
        """Test order execution with unsupported order type."""
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        with self.assertRaises(Exception) as context:
            wrapper.order_qty(
                side=SIDE_BUY,
                quantity="0.001",
                symbol="BTCUSDT",
                order_type=ORDER_TYPE_LIMIT  # Not supported
            )
        
        self.assertIn("Only ORDER_TYPE_MARKET is supported", str(context.exception))

    def test_order_qty_invalid_side(self):
        """Test order execution with invalid side."""
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        with self.assertRaises(Exception) as context:
            wrapper.order_qty(
                side="INVALID_SIDE",
                quantity="0.001",
                symbol="BTCUSDT",
                order_type=ORDER_TYPE_MARKET
            )
        
        self.assertIn("bad trade side", str(context.exception))

    def test_order_qty_binance_api_error(self):
        """Test order execution when Binance API fails."""
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        # Mock Binance API to raise exception
        self.mock_binance_quote.get_latest_price.side_effect = Exception("API Error")
        
        success, order = wrapper.order_qty(
            side=SIDE_BUY,
            quantity="0.001",
            symbol="BTCUSDT",
            order_type=ORDER_TYPE_MARKET
        )
        
        # Should fail gracefully
        self.assertFalse(success)
        self.assertIsNone(order)

    def test_position_updates_after_buy_order(self):
        """Test that positions are correctly updated after buy order."""
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        # Get initial balances
        initial_balances = wrapper.get_equities_balance(self.watching_symbols, "USDT")
        initial_usdt = initial_balances["USDT"].free
        initial_btc = initial_balances["BTC"].free
        
        # Execute buy order
        success, order = wrapper.order_qty(
            side=SIDE_BUY,
            quantity="0.001",
            symbol="BTCUSDT",
            order_type=ORDER_TYPE_MARKET
        )
        
        self.assertTrue(success)
        
        # Get updated balances
        updated_balances = wrapper.get_equities_balance(self.watching_symbols, "USDT")
        
        # USDT should decrease by price * quantity
        expected_usdt_decrease = Decimal('50000.00') * Decimal('0.001')  # 50.00 USDT
        expected_usdt = initial_usdt - expected_usdt_decrease
        self.assertEqual(updated_balances["USDT"].free, expected_usdt)
        
        # BTC should increase by quantity
        expected_btc = initial_btc + Decimal('0.001')
        self.assertEqual(updated_balances["BTC"].free, expected_btc)

    def test_position_updates_after_sell_order(self):
        """Test that positions are correctly updated after sell order."""
        # Set up with existing positions
        self.create_mock_record_file({
            "USDT": "1000.00",
            "BTC": "0.01"
        })
        
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        # Get initial balances
        initial_balances = wrapper.get_equities_balance(self.watching_symbols, "USDT")
        initial_usdt = initial_balances["USDT"].free
        initial_btc = initial_balances["BTC"].free
        
        # Execute sell order
        success, order = wrapper.order_qty(
            side=SIDE_SELL,
            quantity="0.005",
            symbol="BTCUSDT",
            order_type=ORDER_TYPE_MARKET
        )
        
        self.assertTrue(success)
        
        # Get updated balances
        updated_balances = wrapper.get_equities_balance(self.watching_symbols, "USDT")
        
        # USDT should increase by price * quantity
        expected_usdt_increase = Decimal('50000.00') * Decimal('0.005')  # 250.00 USDT
        expected_usdt = initial_usdt + expected_usdt_increase
        self.assertEqual(updated_balances["USDT"].free, expected_usdt)
        
        # BTC should decrease by quantity
        expected_btc = initial_btc - Decimal('0.005')
        self.assertEqual(updated_balances["BTC"].free, expected_btc)

    def test_data_persistence_after_order(self):
        """Test that order data is persisted to file."""
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        # Execute order
        success, order = wrapper.order_qty(
            side=SIDE_BUY,
            quantity="0.001",
            symbol="BTCUSDT",
            order_type=ORDER_TYPE_MARKET
        )
        
        self.assertTrue(success)
        
        # Check that file was created and contains correct data
        record_path = os.path.join(self.test_dir, "mock-record.json")
        self.assertTrue(os.path.exists(record_path))
        
        with open(record_path, 'r') as f:
            data = json.load(f)
        
        # Verify file structure
        self.assertIn("positions", data)
        positions = data["positions"]
        
        # Verify positions
        self.assertIn("USDT", positions)
        self.assertIn("BTC", positions)
        
        # Verify values are strings (for precision)
        self.assertIsInstance(positions["USDT"], str)
        self.assertIsInstance(positions["BTC"], str)

    def test_multiple_orders_accumulation(self):
        """Test that multiple orders correctly accumulate positions."""
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        # Execute multiple buy orders
        orders = []
        for i in range(3):
            success, order = wrapper.order_qty(
                side=SIDE_BUY,
                quantity="0.001",
                symbol="BTCUSDT",
                order_type=ORDER_TYPE_MARKET
            )
            self.assertTrue(success)
            orders.append(order)
        
        # Check final balances
        balances = wrapper.get_equities_balance(self.watching_symbols, "USDT")
        
        # Should have accumulated 0.003 BTC
        self.assertEqual(balances["BTC"].free, Decimal('0.003'))
        
        # USDT should have decreased by 3 * (50000 * 0.001) = 150.00
        expected_usdt = Decimal('10000000000') - Decimal('150.00')
        self.assertEqual(balances["USDT"].free, expected_usdt)

    def test_buy_and_sell_round_trip(self):
        """Test buying and then selling the same asset."""
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        # Initial balance
        initial_balances = wrapper.get_equities_balance(self.watching_symbols, "USDT")
        initial_usdt = initial_balances["USDT"].free
        
        # Buy BTC
        success, buy_order = wrapper.order_qty(
            side=SIDE_BUY,
            quantity="0.001",
            symbol="BTCUSDT",
            order_type=ORDER_TYPE_MARKET
        )
        self.assertTrue(success)
        
        # Sell the same amount
        success, sell_order = wrapper.order_qty(
            side=SIDE_SELL,
            quantity="0.001",
            symbol="BTCUSDT",
            order_type=ORDER_TYPE_MARKET
        )
        self.assertTrue(success)
        
        # Check final balances
        final_balances = wrapper.get_equities_balance(self.watching_symbols, "USDT")
        
        # BTC should be back to zero
        self.assertEqual(final_balances["BTC"].free, Decimal('0'))
        
        # USDT should be back to initial (no commission in mock)
        self.assertEqual(final_balances["USDT"].free, initial_usdt)

    def test_different_assets_trading(self):
        """Test trading different assets (BTC, ETH, DOGE)."""
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        # Set different prices for different assets
        price_responses = {
            "BTCUSDT": {"price": "50000.00"},
            "ETHUSDT": {"price": "3000.00"},
            "DOGEUSDT": {"price": "0.50"}
        }
        
        def mock_get_price(symbol):
            return price_responses.get(symbol, {"price": "1.00"})
        
        self.mock_binance_quote.get_latest_price.side_effect = mock_get_price
        
        # Trade different assets
        trades = [
            (SIDE_BUY, "0.001", "BTCUSDT"),
            (SIDE_BUY, "0.1", "ETHUSDT"),
            (SIDE_BUY, "100", "DOGEUSDT")
        ]
        
        for side, quantity, symbol in trades:
            success, order = wrapper.order_qty(
                side=side,
                quantity=quantity,
                symbol=symbol,
                order_type=ORDER_TYPE_MARKET
            )
            self.assertTrue(success)
        
        # Check all positions
        balances = wrapper.get_equities_balance(self.watching_symbols, "USDT")
        
        self.assertEqual(balances["BTC"].free, Decimal('0.001'))
        self.assertEqual(balances["ETH"].free, Decimal('0.1'))
        self.assertEqual(balances["DOGE"].free, Decimal('100'))
        
        # Calculate expected USDT remaining
        total_spent = (Decimal('0.001') * Decimal('50000.00') +  # BTC
                      Decimal('0.1') * Decimal('3000.00') +      # ETH
                      Decimal('100') * Decimal('0.50'))          # DOGE
        expected_usdt = Decimal('10000000000') - total_spent
        self.assertEqual(balances["USDT"].free, expected_usdt)

    def test_to_dict_method(self):
        """Test the to_dict method for data serialization."""
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        # Execute some trades
        wrapper.order_qty(SIDE_BUY, "0.001", "BTCUSDT", ORDER_TYPE_MARKET)
        
        # Get dictionary representation
        data_dict = wrapper.to_dict()
        
        # Verify structure
        self.assertIn("positions", data_dict)
        positions = data_dict["positions"]
        
        # Verify all values are strings
        for asset, balance in positions.items():
            self.assertIsInstance(asset, str)
            self.assertIsInstance(balance, str)
        
        # Verify content
        self.assertIn("USDT", positions)
        self.assertIn("BTC", positions)

    def test_high_precision_decimal_handling(self):
        """Test handling of high precision decimal values."""
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        # Use high precision quantity
        success, order = wrapper.order_qty(
            side=SIDE_BUY,
            quantity="0.000000001",  # 1 satoshi
            symbol="BTCUSDT",
            order_type=ORDER_TYPE_MARKET
        )
        
        self.assertTrue(success)
        
        # Check precision is maintained
        balances = wrapper.get_equities_balance(self.watching_symbols, "USDT")
        self.assertEqual(balances["BTC"].free, Decimal('0.000000001'))

    def test_zero_quantity_order(self):
        """Test handling of zero quantity orders."""
        wrapper = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        # Execute zero quantity order
        success, order = wrapper.order_qty(
            side=SIDE_BUY,
            quantity="0",
            symbol="BTCUSDT",
            order_type=ORDER_TYPE_MARKET
        )
        
        self.assertTrue(success)
        
        # Positions should not change
        balances = wrapper.get_equities_balance(self.watching_symbols, "USDT")
        self.assertEqual(balances["BTC"].free, Decimal('0'))

    def test_concurrent_wrapper_instances(self):
        """Test behavior with multiple wrapper instances (file locking simulation)."""
        # Create first wrapper
        wrapper1 = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        # Execute trade with first wrapper
        success, order = wrapper1.order_qty(SIDE_BUY, "0.001", "BTCUSDT", ORDER_TYPE_MARKET)
        self.assertTrue(success)
        
        # Create second wrapper (should read updated file)
        wrapper2 = MockTradingWrapper(self.mock_config, self.mock_binance_quote)
        
        # Check that second wrapper has updated positions
        balances = wrapper2.get_equities_balance(self.watching_symbols, "USDT")
        self.assertEqual(balances["BTC"].free, Decimal('0.001'))


class TestMockTradingWrapperIntegration(unittest.TestCase):
    """Integration tests for MockTradingWrapper"""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_base_dir = MockTradingWrapper.BASE_DIR
        MockTradingWrapper.BASE_DIR = self.test_dir
        
    def tearDown(self):
        """Clean up integration test fixtures."""
        MockTradingWrapper.BASE_DIR = self.original_base_dir
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    def test_realistic_trading_scenario(self):
        """Test a realistic trading scenario with multiple operations."""
        # Setup
        mock_config = Mock()
        mock_config.position_manage = {'cash_currency': 'USDT'}
        
        mock_binance = Mock()
        
        # Simulate changing market prices
        price_sequence = [
            {"price": "45000.00"},  # Initial BTC price
            {"price": "46000.00"},  # Price increase
            {"price": "44000.00"},  # Price decrease
            {"price": "47000.00"},  # Recovery
        ]
        
        mock_binance.get_latest_price.side_effect = price_sequence
        
        wrapper = MockTradingWrapper(mock_config, mock_binance)
        
        # Scenario: DCA buying strategy
        buy_amounts = ["0.001", "0.001", "0.0005", "0.001"]
        total_btc_bought = Decimal('0')
        total_usdt_spent = Decimal('0')
        
        for i, quantity in enumerate(buy_amounts):
            success, order = wrapper.order_qty(
                side=SIDE_BUY,
                quantity=quantity,
                symbol="BTCUSDT",
                order_type=ORDER_TYPE_MARKET
            )
            
            self.assertTrue(success)
            
            # Track totals
            qty_decimal = Decimal(quantity)
            price_decimal = Decimal(price_sequence[i]["price"])
            total_btc_bought += qty_decimal
            total_usdt_spent += qty_decimal * price_decimal
        
        # Verify final positions
        balances = wrapper.get_equities_balance([
            WatchingSymbol(symbol="BTCUSDT", base_asset="BTC", info={})
        ], "USDT")
        
        self.assertEqual(balances["BTC"].free, total_btc_bought)
        expected_usdt = Decimal('10000000000') - total_usdt_spent
        self.assertEqual(balances["USDT"].free, expected_usdt)
        
        # Verify data persistence
        record_path = os.path.join(self.test_dir, "mock-record.json")
        self.assertTrue(os.path.exists(record_path))
        
        with open(record_path, 'r') as f:
            saved_data = json.load(f)
            
        self.assertEqual(Decimal(saved_data["positions"]["BTC"]), total_btc_bought)
        self.assertEqual(Decimal(saved_data["positions"]["USDT"]), expected_usdt)


if __name__ == '__main__':
    unittest.main(verbosity=2)