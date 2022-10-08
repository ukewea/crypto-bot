import logging.config
from decimal import Decimal
from typing import Dict, List
from binance.enums import *
from .binance_klines import BinanceKlineWrapper
from .wrapped_data import *
import json
import os
import time
import uuid
import random
import string
import bot_env_config.config
_log = logging.getLogger(__name__)

class MockTradingWrapper:
    """
    包裝一個假的、模擬用的資產 & 訂單相關 API。
    The purpose of the wrapper is for users to test their strategies, and can post their trading history to social media (w/ appropriate notification platform setting).
    """

    BASE_DIR = os.path.normpath(os.path.join(
            os.path.dirname(__file__), '..', "mock-exchange-data-storage"))

    def __init__(self, config: bot_env_config.config.Config, binance_quote_wrapper: BinanceKlineWrapper) -> None:
        # 還是需要幣安的報價 API。
        # 當收到市價單時，會使用幣安的即時報價來當作成交價。
        self.__binance_quote = binance_quote_wrapper
        self.__cash_currency = config.position_manage['cash_currency']

        os.makedirs(MockTradingWrapper.BASE_DIR, mode=0o755, exist_ok=True)
        self.__read_file()

        if self.__cash_currency not in self.__positions:
            # if cash record does not exist, fund it
            init_fund_amount = '10000000000'
            self.__positions[self.__cash_currency] = Decimal(init_fund_amount)
            _log.info(f'Funded {init_fund_amount} for mock trading cash')

    def get_equities_balance(
        self,
        watching_symbols: List[WatchingSymbol],
        cash_asset: str
    ) -> Dict[str, AssetBalance]:
        """取得所有資產的餘額，交易用的現金 (aka. cash_asset) 餘額也會包含在內"""
        if cash_asset not in self.__positions:
            raise Exception(f"Cannot get {cash_asset} balance in your account")

        ret = dict()
        ret[cash_asset] = AssetBalance({
            'asset': cash_asset,
            'free': self.__positions[cash_asset],
            'locked': '0.00000000'
        })

        for watching_symbol in watching_symbols:
            base_asset = watching_symbol.base_asset
            free = '0.00000000'
            if base_asset not in self.__positions:
                # expected behavior, new tokens may not have traded, hence no record to load
                pass
                #print(f"Cannot get {base_asset} balance in your account")
            else:
                free = self.__positions[base_asset]

            balance = AssetBalance({
                'asset': base_asset,
                'free': free,
                'locked': '0.00000000'
            })
            ret[base_asset] = balance

        return ret

    def order_qty(self, side: str, quantity: str, symbol: str, order_type=ORDER_TYPE_MARKET):
        """送出指定交易數量的訂單"""
        if not symbol.endswith(self.__cash_currency):
            raise Exception(f"symbol not end with {self.__cash_currency}")

        if order_type != ORDER_TYPE_MARKET:
            # raise error
            raise Exception("Only ORDER_TYPE_MARKET is supported.")

        if side != SIDE_BUY and side != SIDE_SELL:
            raise Exception(f"bad trade side {side}")

        try:
            # 市價單需使用幣安的即時報價來當作成交價。
            # 因為計算交易數量前，API caller 可能已經使用過幣安的 API 查過一次價格
            # 為了避免 API 呼叫次數過多，也為了加快處理速度，因此會優先使用快取的報價 (但距離查詢時間要在 3 秒內)
            # TODO impl __binance_quote.get_latest_price_cache_first
            # self.__binance_quote.get_latest_price_cache_first(symbol)
            latest_price_api_call = self.__binance_quote.get_latest_price(symbol)
            market_price = latest_price_api_call['price']

            _log.debug(f"[order_qty] mock exchanged received order, return as fulfilled")

            def current_milli_time():
                return round(time.time() * 1000)

            def random_str(length):
                letters = string.ascii_lowercase
                return ''.join(random.choice(letters) for _ in range(length))

            order = {
                "symbol": symbol,
                "orderId": uuid.uuid4().int & (1<<64)-1,
                "orderListId": -1,
                "clientOrderId": random_str(22),
                "transactTime": current_milli_time(),
                "price": "0.00000000",
                "origQty": quantity,
                "executedQty": quantity,
                "cummulativeQuoteQty": quantity,
                "status": "FILLED",
                "timeInForce": "GTC",
                "type": order_type,
                "side": side,
                "fills": [
                    {
                        "price": market_price,
                        "qty": quantity,
                        "commission": "0.0",
                        "commissionAsset": self.__cash_currency,
                        "tradeId": uuid.uuid4().int & (1<<64)-1
                    }
                ]
            }

            _log.debug(f"[order_qty] raw response: {order}")

            trading_asset = symbol[:-len(self.__cash_currency)]

            self.__on_order_fulfilled(side, trading_asset, market_price, quantity)
            return (True, order)
        except Exception as e:
            _log.error(f"[order_qty] an exception occurred - {e}")
            return (False, None)


    def __read_file(self):
        record_path = MockTradingWrapper.__get_record_path()

        if not os.path.exists(record_path):
            self.__positions = {}

            _log.debug(
                f"Mock exchange position file does not exist, skip loading ({record_path})")
            return

        with open(record_path, "r+") as json_file:
            _log.debug(
                f"Mock exchange position file exists, loading ({record_path})")
            all = json.load(json_file)
            self.__positions = all['positions']

    def __on_order_fulfilled(self, side: str, asset_symbol: str, price: str, quantity: str):
        record_path = MockTradingWrapper.__get_record_path()
        _log.debug(f"__on_order_fulfilled, writing to {record_path}")

        # side already checked, only SIDE_BUY and SIDE_SELL are allowed
        quantity = Decimal(quantity)
        if side == SIDE_SELL:
            quantity *= Decimal('-1')

        cash_delta = Decimal(price) * quantity * Decimal('-1')
        self.__positions[self.__cash_currency] += cash_delta

        if asset_symbol not in self.__positions:
            self.__positions[asset_symbol] = quantity
        else:
            self.__positions[asset_symbol] += quantity

        with open(record_path, 'w') as outfile:
            json.dump(self.to_dict(), outfile)
        _log.debug(f"__on_order_fulfilled, writing to {record_path} successfully.")

    def __get_record_path():
        return os.path.join(MockTradingWrapper.BASE_DIR, "mock-record.json")


    def to_dict(self):
        # 輸出全部轉 string，保留數字精度
        positions = {}
        for k, v in self.__positions.items():
            positions[k] = str(v)

        return {
            'positions': positions
        }
