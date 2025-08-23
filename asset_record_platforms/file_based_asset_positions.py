import json
import logging
import os

from .position import *

_log = logging.getLogger(__name__)


class AssetPositions:
    """基於檔案儲存的、帳號下的資產倉位"""

    BASE_DIR = os.path.normpath(os.path.join(
            os.path.dirname(__file__), '..', "asset-positions"))

    def __init__(self, watching_symbols, cash_asset):
        os.makedirs(AssetPositions.BASE_DIR, mode=0o755, exist_ok=True)
        self.positions = dict()

        self.__read_file(cash_asset)
        for symbol in watching_symbols:
            self.__read_file(symbol.base_asset)

    def get_total_commision_as_usdt(self):
        """取得總手續費 (USDT)"""
        sum = Decimal('0.0')
        for pos in self.positions.values():
            sum += pos.total_commission_as_usdt

        return sum

    def get_transactions_count(self):
        """取得交易完成總數"""
        sum = int(0)
        for pos in self.positions.values():
            sum += pos.get_transactions_count()

        return sum

    def cal_total_open_position_count(self):
        total_open_count = int(0)

        for _symbol, position in self.positions.items():
            if position.open_quantity > 0:
                total_open_count += 1

        return total_open_count

    def cal_total_open_cost(self):
        total_open_cost = Decimal(0)

        for _symbol, position in self.positions.items():
            if position.open_cost > 0:
                total_open_cost += position.open_cost

        return total_open_cost
    
    def cal_portfolio_pnl(self, market_prices_dict, cash_currency="USDT"):
        """Calculate comprehensive portfolio P&L metrics
        
        Args:
            market_prices_dict: Dict of {symbol_info: current_price} from market
            cash_currency: Base currency for calculations (default: USDT)
            
        Returns:
            dict with portfolio metrics and per-asset details
        """
        from datetime import datetime, timezone
        
        portfolio_cost = Decimal('0')
        portfolio_market_value = Decimal('0') 
        portfolio_realized_pnl = Decimal('0')
        portfolio_unrealized_pnl = Decimal('0')
        
        asset_details = []
        
        for asset_symbol, position in self.positions.items():
            # Skip cash currency itself and assets with no positions
            if asset_symbol == cash_currency or position.open_quantity <= 0:
                continue
                
            # Find current market price for this asset
            for symbol_info, price in market_prices_dict.items():
                if symbol_info.base_asset == asset_symbol:
                    current_price = price
                    break
            else:
                _log.warning(f"No market price found for {asset_symbol}, skipping from P&L calculation")
                continue
                
            # Calculate metrics for this asset
            cost = position.open_cost
            avg_price = cost / position.open_quantity if position.open_quantity > 0 else Decimal('0')
            market_value = position.open_quantity * current_price
            unrealized_pnl = market_value - cost
            return_percentage = (unrealized_pnl / cost * 100) if cost > 0 else Decimal('0')
            
            # Add to portfolio totals
            portfolio_cost += cost
            portfolio_market_value += market_value
            portfolio_realized_pnl += position.realized_gain
            portfolio_unrealized_pnl += unrealized_pnl
            
            # Store asset details
            asset_details.append({
                'symbol': asset_symbol,
                'quantity': position.open_quantity,
                'avg_price': avg_price,
                'mark_price': current_price,
                'cost': cost,
                'market_value': market_value,
                'unrealized_pnl': unrealized_pnl,
                'return_percentage': return_percentage
            })
            
        # Calculate portfolio percentages
        portfolio_unrealized_pnl_percentage = (portfolio_unrealized_pnl / portfolio_cost * 100) if portfolio_cost > 0 else Decimal('0')
        portfolio_net_pnl = portfolio_realized_pnl + portfolio_unrealized_pnl
        portfolio_net_pnl_percentage = (portfolio_net_pnl / portfolio_cost * 100) if portfolio_cost > 0 else Decimal('0')
        
        return {
            'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M%z'),
            'base_ccy': cash_currency,
            'portfolio_cost': portfolio_cost,
            'portfolio_market_value': portfolio_market_value,
            'portfolio_unrealized_pnl': portfolio_unrealized_pnl,
            'portfolio_unrealized_pnl_percentage': portfolio_unrealized_pnl_percentage,
            'portfolio_realized_pnl': portfolio_realized_pnl,
            'portfolio_net_pnl': portfolio_net_pnl,
            'portfolio_net_pnl_percentage': portfolio_net_pnl_percentage,
            'assets': asset_details
        }
    
    def format_pnl_snapshot_message(self, pnl_data, account_id="Trading"):
        """Format P&L data into the requested message format
        
        Args:
            pnl_data: Dict returned from cal_portfolio_pnl()
            account_id: Account identifier for the message
            
        Returns:
            Formatted string message
        """
        def format_number(value, decimals=4):
            """Format number with proper sign and decimals"""
            if value >= 0:
                return f"+{value:.{decimals}f}"
            else:
                return f"{value:.{decimals}f}"
        
        def format_percentage(value, decimals=2):
            """Format percentage with proper sign"""
            if value >= 0:
                return f"+{value:.{decimals}f}%"
            else:
                return f"{value:.{decimals}f}%"
                
        lines = []
        
        # Header
        lines.append("-" * 50)
        lines.append(f"P/L SNAPSHOT {pnl_data['timestamp']} | Account: {account_id} | Base: {pnl_data['base_ccy']} | Pricing: Mark")
        lines.append("")
        
        # Portfolio summary
        lines.append(f"Total Cost: {pnl_data['portfolio_cost']:.2f} {pnl_data['base_ccy']} | Market Value: {pnl_data['portfolio_market_value']:.2f} {pnl_data['base_ccy']}")
        lines.append(f"Unrealized PnL: {format_number(pnl_data['portfolio_unrealized_pnl'], 2)} {pnl_data['base_ccy']} ({format_percentage(pnl_data['portfolio_unrealized_pnl_percentage'])})")
        lines.append(f"Realized PnL: {format_number(pnl_data['portfolio_realized_pnl'], 2)} {pnl_data['base_ccy']}")
        lines.append(f"Net PnL: {format_number(pnl_data['portfolio_net_pnl'], 2)} {pnl_data['base_ccy']} ({format_percentage(pnl_data['portfolio_net_pnl_percentage'])})")
        lines.append("")
        
        # Individual assets
        for asset in pnl_data['assets']:
            lines.append(f"{asset['symbol']} | Qty: {asset['quantity']:.8f}")
            lines.append(f"Avg Price: {asset['avg_price']:.2f} {pnl_data['base_ccy']}")
            lines.append(f"Mark Price: {asset['mark_price']:.2f} {pnl_data['base_ccy']}")
            lines.append(f"Cost: {asset['cost']:.4f} {pnl_data['base_ccy']}")
            lines.append(f"Market Value: {asset['market_value']:.4f} {pnl_data['base_ccy']}")
            lines.append(f"UPnL: {format_number(asset['unrealized_pnl'], 4)} {pnl_data['base_ccy']} ({format_percentage(asset['return_percentage'])})")
            lines.append("")
        
        lines.append("-" * 50)
        
        return "\n".join(lines)

    def __read_file(self, asset_symbol):
        record_path = AssetPositions.__get_record_path(asset_symbol)

        if not os.path.exists(record_path):
            self.positions[asset_symbol] = Position(
                asset_symbol, self.__on_position_update, None)
            _log.debug(
                f"{asset_symbol} position file does not exist, skip loading ({record_path})")
            return

        with open(record_path, "r+") as json_file:
            _log.debug(
                f"{asset_symbol} position file exists, loading ({record_path})")
            self.positions[asset_symbol] = Position(
                asset_symbol, self.__on_position_update, json.load(json_file))

    def __on_position_update(self, asset_symbol):
        record_path = AssetPositions.__get_record_path(asset_symbol)
        _log.debug(f"__on_position_update, writing to {record_path}")

        with open(record_path, 'w') as outfile:
            position = self.positions[asset_symbol]
            json.dump(position.to_dict(), outfile)

    def __get_record_path(asset_symbol):
        return os.sep.join([AssetPositions.BASE_DIR, f"{asset_symbol}.json"])
