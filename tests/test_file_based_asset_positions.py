#!/usr/bin/env python3
"""
Unit tests for file_based_asset_positions.py

This module contains comprehensive tests covering:
- AssetPositions initialization and file operations
- Portfolio P&L calculations with various market conditions
- P&L message formatting and edge cases
- Error handling and boundary conditions
"""

import unittest
import tempfile
import shutil
import json
import os
from decimal import Decimal
from unittest.mock import patch

# Add the project root to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from asset_record_platforms.file_based_asset_positions import AssetPositions
from exchange_api_wrappers.wrapped_data import WatchingSymbol


class TestAssetPositions(unittest.TestCase):
    """Test cases for AssetPositions class"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.original_base_dir = AssetPositions.BASE_DIR
        AssetPositions.BASE_DIR = self.test_dir
        
        # Sample watching symbols
        self.watching_symbols = [
            WatchingSymbol(symbol="BTCUSDT", base_asset="BTC", info={}),
            WatchingSymbol(symbol="ETHUSDT", base_asset="ETH", info={}),
            WatchingSymbol(symbol="DOGEUSDT", base_asset="DOGE", info={})
        ]
        
        # Sample market prices
        self.market_prices = {
            self.watching_symbols[0]: Decimal('50000.00'),  # BTC
            self.watching_symbols[1]: Decimal('3000.00'),   # ETH
            self.watching_symbols[2]: Decimal('0.50')       # DOGE
        }
        
        # Sample position data
        self.btc_position_data = {
            "open_quantity": "0.001",
            "open_cost": "45.00",
            "realized_gain": "5.00",
            "total_commission_as_usdt": "0.10",
            "transactions": [
                {
                    "time": "1640995200000",
                    "activity": "BUY",
                    "symbol": "BTC",
                    "trade_symbol": "BTCUSDT",
                    "quantity": "0.001",
                    "price": "45000.00",
                    "commission": "0.001",
                    "commission_asset": "BTC",
                    "commission_as_usdt": "0.10",
                    "round_id": "test_round_1",
                    "order_id": "order_1",
                    "trade_id": "trade_1",
                    "closed_trade_ids": []
                }
            ]
        }

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original BASE_DIR
        AssetPositions.BASE_DIR = self.original_base_dir
        # Remove temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_position_file(self, asset_symbol, position_data):
        """Helper method to create a position file for testing."""
        file_path = os.path.join(self.test_dir, f"{asset_symbol}.json")
        with open(file_path, 'w') as f:
            json.dump(position_data, f)
        return file_path

    def test_initialization_empty_directory(self):
        """Test AssetPositions initialization with empty directory."""
        asset_positions = AssetPositions(self.watching_symbols, "USDT")
        
        # Should have positions for all symbols plus cash currency
        expected_positions = len(self.watching_symbols) + 1  # +1 for USDT
        self.assertEqual(len(asset_positions.positions), expected_positions)
        
        # All positions should be empty initially
        for _symbol, position in asset_positions.positions.items():
            self.assertEqual(position.open_quantity, Decimal('0'))
            self.assertEqual(position.open_cost, Decimal('0'))
            self.assertEqual(position.realized_gain, Decimal('0'))

    def test_initialization_with_existing_files(self):
        """Test AssetPositions initialization with existing position files."""
        # Create a BTC position file
        self.create_position_file("BTC", self.btc_position_data)
        
        asset_positions = AssetPositions(self.watching_symbols, "USDT")
        
        # BTC position should be loaded from file
        btc_position = asset_positions.positions["BTC"]
        self.assertEqual(btc_position.open_quantity, Decimal('0.001'))
        self.assertEqual(btc_position.open_cost, Decimal('45.00'))
        self.assertEqual(btc_position.realized_gain, Decimal('5.00'))
        self.assertEqual(len(btc_position.transactions), 1)

    def test_directory_creation(self):
        """Test that BASE_DIR is created if it doesn't exist."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
        
        # Should create directory during initialization
        _asset_positions = AssetPositions(self.watching_symbols, "USDT")
        
        self.assertTrue(os.path.exists(self.test_dir))
        self.assertTrue(os.path.isdir(self.test_dir))

    def test_cal_total_open_position_count_empty(self):
        """Test total open position count with no positions."""
        asset_positions = AssetPositions(self.watching_symbols, "USDT")
        
        count = asset_positions.cal_total_open_position_count()
        self.assertEqual(count, 0)

    def test_cal_total_open_position_count_with_positions(self):
        """Test total open position count with multiple positions."""
        self.create_position_file("BTC", self.btc_position_data)
        
        # Create ETH position
        eth_position_data = {
            "open_quantity": "0.5",
            "open_cost": "1500.00",
            "realized_gain": "0.00",
            "total_commission_as_usdt": "0.05",
            "transactions": []
        }
        self.create_position_file("ETH", eth_position_data)
        
        asset_positions = AssetPositions(self.watching_symbols, "USDT")
        
        count = asset_positions.cal_total_open_position_count()
        self.assertEqual(count, 2)  # BTC and ETH

    def test_cal_total_open_cost_empty(self):
        """Test total open cost calculation with no positions."""
        asset_positions = AssetPositions(self.watching_symbols, "USDT")
        
        total_cost = asset_positions.cal_total_open_cost()
        self.assertEqual(total_cost, Decimal('0'))

    def test_cal_total_open_cost_with_positions(self):
        """Test total open cost calculation with multiple positions."""
        self.create_position_file("BTC", self.btc_position_data)
        
        eth_position_data = {
            "open_quantity": "0.5",
            "open_cost": "1500.00",
            "realized_gain": "0.00",
            "total_commission_as_usdt": "0.05",
            "transactions": []
        }
        self.create_position_file("ETH", eth_position_data)
        
        asset_positions = AssetPositions(self.watching_symbols, "USDT")
        
        total_cost = asset_positions.cal_total_open_cost()
        expected_cost = Decimal('45.00') + Decimal('1500.00')  # BTC + ETH
        self.assertEqual(total_cost, expected_cost)

    def test_get_total_commission_as_usdt(self):
        """Test total commission calculation."""
        self.create_position_file("BTC", self.btc_position_data)
        
        asset_positions = AssetPositions(self.watching_symbols, "USDT")
        
        total_commission = asset_positions.get_total_commision_as_usdt()
        self.assertEqual(total_commission, Decimal('0.10'))

    def test_get_transactions_count(self):
        """Test total transactions count."""
        self.create_position_file("BTC", self.btc_position_data)
        
        asset_positions = AssetPositions(self.watching_symbols, "USDT")
        
        tx_count = asset_positions.get_transactions_count()
        self.assertEqual(tx_count, 1)

    def test_cal_portfolio_pnl_empty_positions(self):
        """Test P&L calculation with no positions."""
        asset_positions = AssetPositions(self.watching_symbols, "USDT")
        
        pnl_data = asset_positions.cal_portfolio_pnl(self.market_prices, "USDT")
        
        self.assertEqual(pnl_data['portfolio_cost'], Decimal('0'))
        self.assertEqual(pnl_data['portfolio_market_value'], Decimal('0'))
        self.assertEqual(pnl_data['portfolio_unrealized_pnl'], Decimal('0'))
        self.assertEqual(pnl_data['portfolio_realized_pnl'], Decimal('0'))
        self.assertEqual(pnl_data['portfolio_net_pnl'], Decimal('0'))
        self.assertEqual(len(pnl_data['assets']), 0)

    def test_cal_portfolio_pnl_with_gains(self):
        """Test P&L calculation with profitable positions."""
        self.create_position_file("BTC", self.btc_position_data)
        
        asset_positions = AssetPositions(self.watching_symbols, "USDT")
        
        pnl_data = asset_positions.cal_portfolio_pnl(self.market_prices, "USDT")
        
        # BTC: 0.001 * 50000 = 50.00 market value, 45.00 cost = 5.00 unrealized gain
        expected_unrealized_pnl = Decimal('5.00')
        expected_realized_pnl = Decimal('5.00')
        expected_net_pnl = expected_unrealized_pnl + expected_realized_pnl
        
        self.assertEqual(pnl_data['portfolio_cost'], Decimal('45.00'))
        self.assertEqual(pnl_data['portfolio_market_value'], Decimal('50.00'))
        self.assertEqual(pnl_data['portfolio_unrealized_pnl'], expected_unrealized_pnl)
        self.assertEqual(pnl_data['portfolio_realized_pnl'], expected_realized_pnl)
        self.assertEqual(pnl_data['portfolio_net_pnl'], expected_net_pnl)
        self.assertEqual(len(pnl_data['assets']), 1)

    def test_cal_portfolio_pnl_with_losses(self):
        """Test P&L calculation with losing positions."""
        # Create position bought at higher price
        losing_position_data = {
            "open_quantity": "0.001",
            "open_cost": "55.00",  # Bought at 55000
            "realized_gain": "-2.00",
            "total_commission_as_usdt": "0.10",
            "transactions": []
        }
        self.create_position_file("BTC", losing_position_data)
        
        asset_positions = AssetPositions(self.watching_symbols, "USDT")
        
        pnl_data = asset_positions.cal_portfolio_pnl(self.market_prices, "USDT")
        
        # BTC: 0.001 * 50000 = 50.00 market value, 55.00 cost = -5.00 unrealized loss
        expected_unrealized_pnl = Decimal('-5.00')
        expected_realized_pnl = Decimal('-2.00')
        expected_net_pnl = expected_unrealized_pnl + expected_realized_pnl
        
        self.assertEqual(pnl_data['portfolio_unrealized_pnl'], expected_unrealized_pnl)
        self.assertEqual(pnl_data['portfolio_realized_pnl'], expected_realized_pnl)
        self.assertEqual(pnl_data['portfolio_net_pnl'], expected_net_pnl)

    def test_cal_portfolio_pnl_multiple_assets(self):
        """Test P&L calculation with multiple assets."""
        self.create_position_file("BTC", self.btc_position_data)
        
        eth_position_data = {
            "open_quantity": "0.5",
            "open_cost": "1400.00",  # Bought at 2800 each
            "realized_gain": "10.00",
            "total_commission_as_usdt": "0.05",
            "transactions": []
        }
        self.create_position_file("ETH", eth_position_data)
        
        asset_positions = AssetPositions(self.watching_symbols, "USDT")
        
        pnl_data = asset_positions.cal_portfolio_pnl(self.market_prices, "USDT")
        
        # BTC: 0.001 * 50000 = 50.00 market, 45.00 cost = +5.00 unrealized
        # ETH: 0.5 * 3000 = 1500.00 market, 1400.00 cost = +100.00 unrealized
        expected_cost = Decimal('45.00') + Decimal('1400.00')
        expected_market_value = Decimal('50.00') + Decimal('1500.00')
        expected_unrealized_pnl = Decimal('5.00') + Decimal('100.00')
        expected_realized_pnl = Decimal('5.00') + Decimal('10.00')
        
        self.assertEqual(pnl_data['portfolio_cost'], expected_cost)
        self.assertEqual(pnl_data['portfolio_market_value'], expected_market_value)
        self.assertEqual(pnl_data['portfolio_unrealized_pnl'], expected_unrealized_pnl)
        self.assertEqual(pnl_data['portfolio_realized_pnl'], expected_realized_pnl)
        self.assertEqual(len(pnl_data['assets']), 2)

    def test_cal_portfolio_pnl_missing_market_price(self):
        """Test P&L calculation when market price is missing for some assets."""
        self.create_position_file("BTC", self.btc_position_data)
        
        # Create position for asset not in market_prices
        sol_symbol = WatchingSymbol(symbol="SOLUSDT", base_asset="SOL", info={})
        sol_position_data = {
            "open_quantity": "10",
            "open_cost": "1000.00",
            "realized_gain": "0.00",
            "total_commission_as_usdt": "0.20",
            "transactions": []
        }
        self.create_position_file("SOL", sol_position_data)
        
        # Initialize with SOL symbol but no market price
        watching_symbols_with_sol = self.watching_symbols + [sol_symbol]
        asset_positions = AssetPositions(watching_symbols_with_sol, "USDT")
        
        with patch('asset_record_platforms.file_based_asset_positions._log') as mock_log:
            pnl_data = asset_positions.cal_portfolio_pnl(self.market_prices, "USDT")
            
            # Should log warning for missing SOL price
            mock_log.warning.assert_called_with("No market price found for SOL, skipping from P&L calculation")
            
            # Should only include BTC in calculations
            self.assertEqual(len(pnl_data['assets']), 1)
            self.assertEqual(pnl_data['assets'][0]['symbol'], 'BTC')

    def test_cal_portfolio_pnl_zero_cost_position(self):
        """Test P&L calculation with zero cost position (edge case)."""
        zero_cost_position_data = {
            "open_quantity": "0.001",
            "open_cost": "0.00",  # Free coins somehow
            "realized_gain": "0.00",
            "total_commission_as_usdt": "0.00",
            "transactions": []
        }
        self.create_position_file("BTC", zero_cost_position_data)
        
        asset_positions = AssetPositions(self.watching_symbols, "USDT")
        
        pnl_data = asset_positions.cal_portfolio_pnl(self.market_prices, "USDT")
        
        # Should handle division by zero gracefully
        asset = pnl_data['assets'][0]
        self.assertEqual(asset['cost'], Decimal('0'))
        self.assertEqual(asset['market_value'], Decimal('50.00'))
        self.assertEqual(asset['unrealized_pnl'], Decimal('50.00'))
        self.assertEqual(asset['return_percentage'], Decimal('0'))  # Should default to 0 when cost is 0

    def test_cal_portfolio_pnl_zero_quantity_position(self):
        """Test P&L calculation with zero quantity position."""
        zero_qty_position_data = {
            "open_quantity": "0.000",
            "open_cost": "0.00",
            "realized_gain": "5.00",  # All sold, profit realized
            "total_commission_as_usdt": "0.10",
            "transactions": []
        }
        self.create_position_file("BTC", zero_qty_position_data)
        
        asset_positions = AssetPositions(self.watching_symbols, "USDT")
        
        pnl_data = asset_positions.cal_portfolio_pnl(self.market_prices, "USDT")
        
        # Should skip assets with zero quantity in asset list
        self.assertEqual(len(pnl_data['assets']), 0)
        # Realized P&L is only counted when we have open positions to iterate over
        # Since BTC has zero quantity, it gets skipped entirely including its realized gains
        self.assertEqual(pnl_data['portfolio_realized_pnl'], Decimal('0'))

    def test_format_pnl_snapshot_message_basic(self):
        """Test basic P&L message formatting."""
        pnl_data = {
            'timestamp': '2025-01-01 12:00+0000',
            'base_ccy': 'USDT',
            'portfolio_cost': Decimal('100.00'),
            'portfolio_market_value': Decimal('110.00'),
            'portfolio_unrealized_pnl': Decimal('10.00'),
            'portfolio_unrealized_pnl_percentage': Decimal('10.00'),
            'portfolio_realized_pnl': Decimal('5.00'),
            'portfolio_net_pnl': Decimal('15.00'),
            'portfolio_net_pnl_percentage': Decimal('15.00'),
            'assets': [
                {
                    'symbol': 'BTC',
                    'quantity': Decimal('0.001'),
                    'avg_price': Decimal('45000.00'),
                    'mark_price': Decimal('50000.00'),
                    'cost': Decimal('45.00'),
                    'market_value': Decimal('50.00'),
                    'unrealized_pnl': Decimal('5.00'),
                    'return_percentage': Decimal('11.11')
                }
            ]
        }
        
        asset_positions = AssetPositions([], "USDT")
        message = asset_positions.format_pnl_snapshot_message(pnl_data, "TestAccount")
        
        # Check key components are in the message
        self.assertIn("P/L SNAPSHOT 2025-01-01 12:00+0000", message)
        self.assertIn("Account: TestAccount", message)
        self.assertIn("Base: USDT", message)
        self.assertIn("Total Cost: 100.00 USDT", message)
        self.assertIn("Market Value: 110.00 USDT", message)
        self.assertIn("Unrealized PnL: +10.00 USDT (+10.00%)", message)
        self.assertIn("Realized PnL: +5.00 USDT", message)
        self.assertIn("Net PnL: +15.00 USDT (+15.00%)", message)
        self.assertIn("BTC | Qty: 0.00100000", message)
        self.assertIn("Avg Price: 45000.00 USDT", message)
        self.assertIn("Mark Price: 50000.00 USDT", message)
        self.assertIn("UPnL: +5.0000 USDT (+11.11%)", message)

    def test_format_pnl_snapshot_message_negative_pnl(self):
        """Test P&L message formatting with negative values."""
        pnl_data = {
            'timestamp': '2025-01-01 12:00+0000',
            'base_ccy': 'USDT',
            'portfolio_cost': Decimal('100.00'),
            'portfolio_market_value': Decimal('90.00'),
            'portfolio_unrealized_pnl': Decimal('-10.00'),
            'portfolio_unrealized_pnl_percentage': Decimal('-10.00'),
            'portfolio_realized_pnl': Decimal('-5.00'),
            'portfolio_net_pnl': Decimal('-15.00'),
            'portfolio_net_pnl_percentage': Decimal('-15.00'),
            'assets': [
                {
                    'symbol': 'BTC',
                    'quantity': Decimal('0.001'),
                    'avg_price': Decimal('55000.00'),
                    'mark_price': Decimal('45000.00'),
                    'cost': Decimal('55.00'),
                    'market_value': Decimal('45.00'),
                    'unrealized_pnl': Decimal('-10.00'),
                    'return_percentage': Decimal('-18.18')
                }
            ]
        }
        
        asset_positions = AssetPositions([], "USDT")
        message = asset_positions.format_pnl_snapshot_message(pnl_data)
        
        # Check negative values are formatted correctly
        self.assertIn("Unrealized PnL: -10.00 USDT (-10.00%)", message)
        self.assertIn("Realized PnL: -5.00 USDT", message)
        self.assertIn("Net PnL: -15.00 USDT (-15.00%)", message)
        self.assertIn("UPnL: -10.0000 USDT (-18.18%)", message)

    def test_format_pnl_snapshot_message_empty_assets(self):
        """Test P&L message formatting with no assets."""
        pnl_data = {
            'timestamp': '2025-01-01 12:00+0000',
            'base_ccy': 'USDT',
            'portfolio_cost': Decimal('0.00'),
            'portfolio_market_value': Decimal('0.00'),
            'portfolio_unrealized_pnl': Decimal('0.00'),
            'portfolio_unrealized_pnl_percentage': Decimal('0.00'),
            'portfolio_realized_pnl': Decimal('0.00'),
            'portfolio_net_pnl': Decimal('0.00'),
            'portfolio_net_pnl_percentage': Decimal('0.00'),
            'assets': []
        }
        
        asset_positions = AssetPositions([], "USDT")
        message = asset_positions.format_pnl_snapshot_message(pnl_data)
        
        # Should still have portfolio summary but no individual assets
        self.assertIn("Total Cost: 0.00 USDT", message)
        self.assertIn("Market Value: 0.00 USDT", message)
        # Should have proper formatting structure
        self.assertTrue(message.startswith("-" * 50))
        self.assertTrue(message.endswith("-" * 50))

    def test_invalid_json_file_handling(self):
        """Test handling of invalid JSON in position files."""
        # Create a file with invalid JSON
        invalid_file = os.path.join(self.test_dir, "BTC.json")
        with open(invalid_file, 'w') as f:
            f.write('invalid json content')
        
        with self.assertRaises(json.JSONDecodeError):
            AssetPositions(self.watching_symbols, "USDT")

    def test_file_permissions_handling(self):
        """Test handling of file permission errors."""
        # Create a file with restrictive permissions
        btc_file = self.create_position_file("BTC", self.btc_position_data)
        os.chmod(btc_file, 0o000)  # No permissions
        
        try:
            with self.assertRaises(PermissionError):
                AssetPositions(self.watching_symbols, "USDT")
        finally:
            # Restore permissions for cleanup
            os.chmod(btc_file, 0o644)

    def test_different_cash_currencies(self):
        """Test P&L calculations with different cash currencies."""
        self.create_position_file("BTC", self.btc_position_data)
        
        asset_positions = AssetPositions(self.watching_symbols, "EUR")
        
        pnl_data = asset_positions.cal_portfolio_pnl(self.market_prices, "EUR")
        
        self.assertEqual(pnl_data['base_ccy'], 'EUR')
        # Should still calculate P&L correctly regardless of cash currency
        self.assertEqual(len(pnl_data['assets']), 1)

    def test_large_decimal_precision(self):
        """Test handling of high precision decimal values."""
        high_precision_data = {
            "open_quantity": "0.000000001",
            "open_cost": "0.00000005",
            "realized_gain": "0.00000001",
            "total_commission_as_usdt": "0.000000001",
            "transactions": []
        }
        self.create_position_file("BTC", high_precision_data)
        
        asset_positions = AssetPositions(self.watching_symbols, "USDT")
        
        pnl_data = asset_positions.cal_portfolio_pnl(self.market_prices, "USDT")
        
        # Should handle tiny values without losing precision
        asset = pnl_data['assets'][0]
        self.assertEqual(asset['quantity'], Decimal('0.000000001'))
        self.assertEqual(asset['cost'], Decimal('0.00000005'))

    @patch('asset_record_platforms.file_based_asset_positions._log')
    def test_logging_integration(self, mock_log):
        """Test that logging works correctly."""
        # Test warning for missing market price
        self.create_position_file("BTC", self.btc_position_data)
        asset_positions = AssetPositions(self.watching_symbols, "USDT")
        
        # Call with empty market prices to trigger warning
        _pnl_data = asset_positions.cal_portfolio_pnl({}, "USDT")
        
        mock_log.warning.assert_called_with("No market price found for BTC, skipping from P&L calculation")


class TestAssetPositionsIntegration(unittest.TestCase):
    """Integration tests that test the complete workflow."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_base_dir = AssetPositions.BASE_DIR
        AssetPositions.BASE_DIR = self.test_dir
        
    def tearDown(self):
        """Clean up integration test fixtures."""
        AssetPositions.BASE_DIR = self.original_base_dir
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    def test_complete_pnl_workflow(self):
        """Test complete P&L calculation and formatting workflow."""
        # Setup realistic portfolio data
        watching_symbols = [
            WatchingSymbol(symbol="BTCUSDT", base_asset="BTC", info={}),
            WatchingSymbol(symbol="ETHUSDT", base_asset="ETH", info={}),
            WatchingSymbol(symbol="DOGEUSDT", base_asset="DOGE", info={})
        ]
        
        market_prices = {
            watching_symbols[0]: Decimal('60000.00'),
            watching_symbols[1]: Decimal('4000.00'),
            watching_symbols[2]: Decimal('0.75')
        }
        
        # Create position files
        positions_data = {
            "BTC": {
                "open_quantity": "0.01",
                "open_cost": "500.00",
                "realized_gain": "50.00",
                "total_commission_as_usdt": "2.50",
                "transactions": []
            },
            "ETH": {
                "open_quantity": "0.25",
                "open_cost": "800.00",
                "realized_gain": "25.00",
                "total_commission_as_usdt": "1.60",
                "transactions": []
            },
            "DOGE": {
                "open_quantity": "1000",
                "open_cost": "200.00",
                "realized_gain": "-10.00",
                "total_commission_as_usdt": "0.80",
                "transactions": []
            }
        }
        
        for symbol, data in positions_data.items():
            file_path = os.path.join(self.test_dir, f"{symbol}.json")
            with open(file_path, 'w') as f:
                json.dump(data, f)
        
        # Initialize AssetPositions
        asset_positions = AssetPositions(watching_symbols, "USDT")
        
        # Calculate P&L
        pnl_data = asset_positions.cal_portfolio_pnl(market_prices, "USDT")
        
        # Verify calculations
        # BTC: 0.01 * 60000 = 600, cost 500 = +100 unrealized
        # ETH: 0.25 * 4000 = 1000, cost 800 = +200 unrealized  
        # DOGE: 1000 * 0.75 = 750, cost 200 = +550 unrealized
        expected_cost = Decimal('1500.00')  # 500 + 800 + 200
        expected_market_value = Decimal('2350.00')  # 600 + 1000 + 750
        expected_unrealized_pnl = Decimal('850.00')  # 100 + 200 + 550
        expected_realized_pnl = Decimal('65.00')  # 50 + 25 + (-10)
        expected_net_pnl = Decimal('915.00')  # 850 + 65
        
        self.assertEqual(pnl_data['portfolio_cost'], expected_cost)
        self.assertEqual(pnl_data['portfolio_market_value'], expected_market_value)
        self.assertEqual(pnl_data['portfolio_unrealized_pnl'], expected_unrealized_pnl)
        self.assertEqual(pnl_data['portfolio_realized_pnl'], expected_realized_pnl)
        self.assertEqual(pnl_data['portfolio_net_pnl'], expected_net_pnl)
        self.assertEqual(len(pnl_data['assets']), 3)
        
        # Format message
        message = asset_positions.format_pnl_snapshot_message(pnl_data, "IntegrationTest")
        
        # Verify message contains expected data
        self.assertIn("IntegrationTest", message)
        self.assertIn("Total Cost: 1500.00 USDT", message)
        self.assertIn("Market Value: 2350.00 USDT", message)
        self.assertIn("Unrealized PnL: +850.00 USDT", message)
        self.assertIn("Net PnL: +915.00 USDT", message)
        
        # Verify all assets are included
        self.assertIn("BTC |", message)
        self.assertIn("ETH |", message) 
        self.assertIn("DOGE |", message)


if __name__ == '__main__':
    # Configure test runner
    unittest.main(verbosity=2)