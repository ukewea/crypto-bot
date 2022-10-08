import logging.config
from decimal import Decimal
from typing import Dict, List
from .wrapped_data import *
from binance.client import Client
from binance.enums import *

_log = logging.getLogger(__name__)


class BinanceTradingWrapper:
    """包裝幣安的資產 & 訂單相關 API"""

    def __init__(self, client: Client) -> None:
        self.__client = client

    def get_account(self):
        account = self.__client.get_account()
        return account

    def get_equities_balance(
        self,
        watching_symbols: List[WatchingSymbol],
        cash_asset: str
    ) -> Dict[str, AssetBalance]:
        """取得所有資產的餘額，交易用的現金 (aka. cash_asset) 餘額也會包含在內"""

        account = self.get_account()
        balances = account['balances']
        ret = dict()

        asset_balance = [x for x in balances if x['asset'] == cash_asset]
        if len(asset_balance) < 1:
            raise Exception(f"Cannot get {cash_asset} balance in your account")

        balance = AssetBalance(asset_balance[0])
        ret[cash_asset] = balance

        for watching_symbol in watching_symbols:
            base_asset = watching_symbol.base_asset
            asset_balance = [x for x in balances if x['asset'] == base_asset]
            if len(asset_balance) < 1:
                print(f"Cannot get {base_asset} balance in your account")
                continue

            balance = AssetBalance(asset_balance[0])
            ret[base_asset] = balance

        return ret

    def order_qty(self, side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
        """送出指定交易數量的訂單"""

        if order_type != ORDER_TYPE_MARKET:
            # raise error
            pass
        try:
            self._binance_quote.get_latest_price_cache_first(symbol)
            _log.debug(f"[order_qty] sending order")
            order = self.__client.create_order(
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity)

            _log.debug(f"[order_qty] raw response: {order}")
            return (True, order)
        except Exception as e:
            _log.error(f"[order_qty] an exception occurred - {e}")
            return (False, None)

    def order_quote_qty(self, side, quoteOrderQty, symbol, order_type=ORDER_TYPE_MARKET):
        """送出指定成交額的訂單"""
        try:
            _log.debug(f"[order_quote_qty] sending order")
            order = self.__client.create_order(
                symbol=symbol,
                side=side,
                type=order_type,
                quoteOrderQty=quoteOrderQty)

            _log.debug(f"[order_quote_qty] raw response: {order}")
            return (True, order)
        except Exception as e:
            _log.error(f"[order_quote_qty] an exception occurred - {e}")
            return (False, None)
