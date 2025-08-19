#!/usr/bin/env python3
"""
Portfolio Summary Script

Calculates current profit/loss for all recorded crypto positions and sends
a summary to the configured notification platform (Discord/Telegram).

Usage: python portfolio_summary.py
"""

import logging
import os
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from asset_record_platforms.file_based_asset_positions import AssetPositions
from asset_record_platforms.position import Position
from bot_env_config.config import Config
from exchange_api_wrappers.crypto import Crypto
from exchange_api_wrappers.wrapped_data import WatchingSymbol

_log = logging.getLogger(__name__)


class PortfolioCalculator:
    """Calculates portfolio profit/loss and sends notifications"""
    
    def __init__(self, config: Config):
        self.config = config
        self.cash_currency = config.position_manage['cash_currency']
        
        # Initialize crypto API for price fetching
        trading_mode = config.position_manage.get('trading_mode', 'mock_trading')
        if trading_mode == 'mock_trading':
            self.crypto_api = Crypto.get_mock_trade_and_binance_klines(config)
        else:
            self.crypto_api = Crypto.get_binance_trade_and_klines(config)
        
        # Initialize notification platform
        self.notification_bot = config.spawn_nofification_platform()
        
    def load_positions(self) -> AssetPositions:
        """Load all asset positions from files"""
        _log.info("Loading asset positions from files...")
        
        # Get all position files
        positions_dir = os.path.join(os.path.dirname(__file__), "asset-positions")
        if not os.path.exists(positions_dir):
            _log.warning(f"Positions directory not found: {positions_dir}")
            return None
        
        position_files = [f for f in os.listdir(positions_dir) if f.endswith('.json')]
        if not position_files:
            _log.warning("No position files found")
            return None
        
        # Create watching symbols for all assets with positions
        watching_symbols = []
        for filename in position_files:
            asset_symbol = filename.replace('.json', '')
            if asset_symbol != self.cash_currency:  # Skip cash currency
                symbol = f"{asset_symbol}{self.cash_currency}"
                watching_symbols.append(WatchingSymbol(symbol, asset_symbol, None))
        
        if not watching_symbols:
            _log.warning("No crypto assets found in positions")
            return None
        
        # Load positions using existing system
        asset_positions = AssetPositions(watching_symbols, self.cash_currency)
        _log.info(f"Loaded positions for {len(asset_positions.positions)} assets")
        
        return asset_positions
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, Decimal]:
        """Fetch current market prices for all symbols"""
        _log.info(f"Fetching current prices for {len(symbols)} symbols...")
        prices = {}
        
        for symbol in symbols:
            try:
                price_data = self.crypto_api.get_latest_price(symbol)
                prices[symbol] = Decimal(price_data['price'])
                _log.debug(f"{symbol}: {prices[symbol]}")
            except Exception as e:
                _log.error(f"Failed to get price for {symbol}: {e}")
                prices[symbol] = Decimal('0')
        
        return prices
    
    def calculate_portfolio_summary(self) -> Dict:
        """Calculate complete portfolio profit/loss summary"""
        _log.info("Calculating portfolio summary...")
        
        # Load positions
        asset_positions = self.load_positions()
        if not asset_positions:
            return {"error": "No positions found"}
        
        # Get symbols that have open positions
        symbols_to_price = []
        assets_with_positions = []
        
        for asset_symbol, position in asset_positions.positions.items():
            if asset_symbol != self.cash_currency and position.open_quantity > 0:
                symbol = f"{asset_symbol}{self.cash_currency}"
                symbols_to_price.append(symbol)
                assets_with_positions.append((asset_symbol, position))
        
        if not symbols_to_price:
            return {"error": "No open positions found"}
        
        # Get current market prices
        current_prices = self.get_current_prices(symbols_to_price)
        
        # Calculate summary for each asset
        asset_summaries = []
        total_cost = Decimal('0')
        total_current_value = Decimal('0')
        total_realized_gain = Decimal('0')
        total_commission = Decimal('0')
        total_transactions = 0
        
        for asset_symbol, position in assets_with_positions:
            symbol = f"{asset_symbol}{self.cash_currency}"
            current_price = current_prices.get(symbol, Decimal('0'))
            
            # Calculate metrics
            avg_buy_price = position.open_cost / position.open_quantity if position.open_quantity > 0 else Decimal('0')
            current_value = position.open_quantity * current_price
            unrealized_pnl = current_value - position.open_cost
            unrealized_pnl_pct = (unrealized_pnl / position.open_cost * 100) if position.open_cost > 0 else Decimal('0')
            
            asset_summary = {
                'asset': asset_symbol,
                'quantity': position.open_quantity,
                'avg_buy_price': avg_buy_price,
                'current_price': current_price,
                'total_cost': position.open_cost,
                'current_value': current_value,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_pct': unrealized_pnl_pct,
                'realized_gain': position.realized_gain,
                'commission': position.total_commission_as_usdt,
                'transactions_count': position.get_transactions_count()
            }
            
            asset_summaries.append(asset_summary)
            
            # Add to totals
            total_cost += position.open_cost
            total_current_value += current_value
            total_realized_gain += position.realized_gain
            total_commission += position.total_commission_as_usdt
            total_transactions += position.get_transactions_count()
        
        # Calculate portfolio totals
        total_unrealized_pnl = total_current_value - total_cost
        total_unrealized_pnl_pct = (total_unrealized_pnl / total_cost * 100) if total_cost > 0 else Decimal('0')
        total_pnl = total_unrealized_pnl + total_realized_gain
        
        return {
            'timestamp': datetime.now(timezone.utc),
            'assets': asset_summaries,
            'totals': {
                'total_cost': total_cost,
                'current_value': total_current_value,
                'unrealized_pnl': total_unrealized_pnl,
                'unrealized_pnl_pct': total_unrealized_pnl_pct,
                'realized_gain': total_realized_gain,
                'total_pnl': total_pnl,
                'commission': total_commission,
                'transactions_count': total_transactions
            }
        }
    
    def format_summary_message(self, summary: Dict) -> str:
        """Format portfolio summary into a readable message"""
        if 'error' in summary:
            return f"❌ Portfolio Summary Error: {summary['error']}"
        
        msg = []
        msg.append("📊 **PORTFOLIO SUMMARY**")
        msg.append(f"🕒 {summary['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} UTC")
        msg.append("")
        
        # Individual asset details
        msg.append("🏦 **POSITIONS:**")
        for asset in summary['assets']:
            pnl_emoji = "📈" if asset['unrealized_pnl'] >= 0 else "📉"
            msg.append(f"{pnl_emoji} **{asset['asset']}**")
            msg.append(f"   • Quantity: {asset['quantity']:.8f}")
            msg.append(f"   • Avg Buy: ${asset['avg_buy_price']:.4f}")
            msg.append(f"   • Current: ${asset['current_price']:.4f}")
            msg.append(f"   • Cost: ${asset['total_cost']:.2f}")
            msg.append(f"   • Value: ${asset['current_value']:.2f}")
            msg.append(f"   • PnL: ${asset['unrealized_pnl']:.2f} ({asset['unrealized_pnl_pct']:.2f}%)")
            if asset['realized_gain'] != 0:
                msg.append(f"   • Realized: ${asset['realized_gain']:.2f}")
            msg.append(f"   • Trades: {asset['transactions_count']}")
            msg.append("")
        
        # Portfolio totals
        totals = summary['totals']
        total_emoji = "💰" if totals['total_pnl'] >= 0 else "💸"
        msg.append("📋 **PORTFOLIO TOTALS:**")
        msg.append(f"💵 Total Invested: ${totals['total_cost']:.2f}")
        msg.append(f"💎 Current Value: ${totals['current_value']:.2f}")
        msg.append(f"📊 Unrealized P&L: ${totals['unrealized_pnl']:.2f} ({totals['unrealized_pnl_pct']:.2f}%)")
        
        if totals['realized_gain'] != 0:
            msg.append(f"✅ Realized Gains: ${totals['realized_gain']:.2f}")
        
        msg.append(f"{total_emoji} **Total P&L: ${totals['total_pnl']:.2f}**")
        msg.append(f"💰 Commission Paid: ${totals['commission']:.2f}")
        msg.append(f"🔄 Total Transactions: {totals['transactions_count']}")
        
        return "\n".join(msg)
    
    def send_notification(self, message: str):
        """Send portfolio summary via configured notification platform"""
        if not self.notification_bot:
            _log.warning("No notification platform configured")
            print("\n" + "="*60)
            print("PORTFOLIO SUMMARY (Console Output)")
            print("="*60)
            print(message)
            print("="*60)
            return
        
        try:
            _log.info("Sending portfolio summary via notification platform...")
            self.notification_bot.send_message(message)
            _log.info("Portfolio summary sent successfully!")
        except Exception as e:
            _log.error(f"Failed to send notification: {e}")
            print(f"\nFailed to send notification: {e}")
            print("\n" + "="*60)
            print("PORTFOLIO SUMMARY (Console Fallback)")
            print("="*60)
            print(message)
            print("="*60)
    
    def run(self):
        """Main execution method"""
        _log.info("Starting portfolio summary calculation...")
        
        try:
            # Calculate portfolio summary
            summary = self.calculate_portfolio_summary()
            
            # Format message
            message = self.format_summary_message(summary)
            
            # Send notification
            self.send_notification(message)
            
            _log.info("Portfolio summary completed successfully!")
            
        except Exception as e:
            error_msg = f"❌ Portfolio calculation failed: {str(e)}"
            _log.error(error_msg)
            
            try:
                if self.notification_bot:
                    self.notification_bot.send_message(error_msg)
                else:
                    print(f"\nError: {error_msg}")
            except:
                print(f"\nError: {error_msg}")


def main():
    """Main entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s][%(levelname)s][%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    try:
        # Load configuration
        config = Config()
        
        # Create and run portfolio calculator
        calculator = PortfolioCalculator(config)
        calculator.run()
        
    except Exception as e:
        _log.error(f"Failed to initialize portfolio calculator: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()