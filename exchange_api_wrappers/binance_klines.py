import logging.config
from decimal import Decimal
from typing import Dict, List
from binance.client import Client
from binance.enums import *
from exchange_api_wrappers.wrapped_data import *

_log = logging.getLogger(__name__)


class BinanceKlineWrapper:
    """包裝幣安的 K 線歷史資料讀取 API，用來取得技術分析所需資料。"""

    def __init__(self, client: Client) -> None:
        self.__client = client

    def get_tradable_symbols(self, quote_asset, include_assets, exclude_assets):
        """找出以 quote_asset 報價，且目前可交易、可送市價單、非槓桿型的交易對"""

        exchange_info = self.__get_exchange_info()
        # print(type(exchange_info))
        # with open('exchange_info.json', 'w') as outfile:
        #     json.dump(exchange_info, outfile, indent=4)

        trade_with_quote_asset = [item for item in exchange_info['symbols']
                                  if item['quoteAsset'].upper() == quote_asset]

        if include_assets is not None and exclude_assets is not None:
            raise ValueError(
                'include_assets and exclude_assets cannot both be non empty')

        if include_assets is not None:
            return [WatchingSymbol(symbol['symbol'], symbol['baseAsset'], symbol)
                    for symbol in trade_with_quote_asset
                    if symbol['status'].upper() == "TRADING"
                    and symbol['baseAsset'] in include_assets
                    and "MARKET" in symbol['orderTypes']
                    and not "LEVERAGED" in symbol['permissions']]

        if exclude_assets is not None:
            return [WatchingSymbol(symbol['symbol'], symbol['baseAsset'], symbol)
                    for symbol in trade_with_quote_asset
                    if symbol['status'].upper() == "TRADING"
                    and not symbol['baseAsset'] in exclude_assets
                    and "MARKET" in symbol['orderTypes']
                    and not "LEVERAGED" in symbol['permissions']]

    def get_latest_price(self, trade_symbol):
        """取得指定交易對的最新報價"""
        symbol_ticker = self.__client.get_symbol_ticker(symbol=trade_symbol)
        return symbol_ticker

    def get_historical_klines(self, symbol, KLINE_INTERVAL, fromdate, todate):
        return self.__client.get_historical_klines(symbol, KLINE_INTERVAL, fromdate, todate)
        # print(self.__client.response)

    def get_klines(self, symbol, klines_limit=100, interval=Client.KLINE_INTERVAL_15MINUTE):
        """
        Get klines data
        :param symbol: symbol e.g., BTCUSDT、DOGEUSDT
        :param klines_limit: K線的數量限制
        :param interval: 幾分的K線資料
        :return: klines data
        """

        klines = self.__client.get_klines(
            symbol=symbol,
            interval=interval,
            limit=klines_limit)
        if len(klines) < klines_limit:
            _log.debug(
                f"[{symbol}] No enough data for {symbol} (only {len(klines)})")
            return None

        return [Kline(data) for data in klines]

    def get_closed_prices(self, symbol, klines_limit = 100, interval=Client.KLINE_INTERVAL_15MINUTE):
        klines = self.get_klines(symbol, klines_limit, interval)
        return [kline.close for kline in klines]

    def __get_exchange_info(self):
        exchange_info = self.__client.get_exchange_info()
        return exchange_info
