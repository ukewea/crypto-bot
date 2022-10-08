import logging.config
from decimal import Decimal
from typing import Dict, List
from binance.enums import *
from .binance_klines import BinanceKlineWrapper
from .wrapped_data import *

_log = logging.getLogger(__name__)

class MockTradingWrapper:
    """
    包裝一個假的、模擬用的資產 & 訂單相關 API。
    The purpose of the wrapper is for users to test their strategies, and can post their trading history to social media (w/ appropriate notification platform setting).

    Due to this purpose, the order will always be
    """

    def __init__(self, binance_quote_wrapper: BinanceKlineWrapper) -> None:
        """
        還是需要幣安的報價 API。
        當收到市價單時，會使用幣安的即時報價來當作成交價。
        """
        self._binance_quote = binance_quote_wrapper
        pass

    def order_qty(self, side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
        #???????????????????????
        """送出指定交易數量的訂單"""

        if order_type != ORDER_TYPE_MARKET:
            # raise error
            pass
        try:
            # 市價單需使用幣安的即時報價來當作成交價。
            # 因為賽計算交易數量前，API caller 可能已經使用過幣安的 API 查過一次價格
            # 為了避免 API 呼叫次數過多，也為了加快處理速度，因此會優先使用快取的報價 (但距離查詢時間要在 3 秒內)
            # impl _binance_quote.get_latest_price_cache_first
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
