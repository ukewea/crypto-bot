import logging.config

from bot_env_config.config import Config
from binance.client import Client
from binance.enums import *
from . import binance_klines, binance_trading, mock_trading, wrapped_data
from typing import List, Dict

_log = logging.getLogger(__name__)


class Crypto:
    def __init__(self, klines, trade):
        """
        建構式
        klines: 幣價 K 線圖的資料來源 API wrapper
        trade: 交易所交易的交易 API wrapper
        """

        self.__klines = klines
        self.__trade = trade

#region trading related APIs

    def get_binance_trade_and_klines(config: Config):
        client = Client(
            api_key=config.auth["API_KEY"],
            api_secret=config.auth["API_SECRET"],
            testnet=False
        )

        klines = binance_klines.BinanceKlineWrapper(client)
        trade = binance_trading.BinanceTradingWrapper(client)

        return Crypto(klines, trade)

    def get_mock_trade_and_binance_klines(config: Config):
        client = Client(
            api_key=config.auth["API_KEY"],
            api_secret=config.auth["API_SECRET"],
            testnet=False
        )

        klines = binance_klines.BinanceKlineWrapper(client)
        trade = mock_trading.MockTradingWrapper(client)

        return Crypto(klines, trade)

    def get_equities_balance(
        self,
        watching_symbols: List[wrapped_data.WatchingSymbol],
        cash_asset: str
    ) -> Dict[str, wrapped_data.AssetBalance]:
        """取得所有資產的餘額，交易用的現金 (aka. cash_asset) 餘額也會包含在內"""
        return self.__trade.get_equities_balance(
            watching_symbols,
            cash_asset
        )

    def order_qty(self, side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
        """送出指定交易數量的訂單 (e.g., 買/賣 10 顆 BTC)"""
        return self.__trade.order_qty(side, quantity, symbol, order_type)

    def order_quote_qty(self, side, quoteOrderQty, symbol, order_type=ORDER_TYPE_MARKET):
        """送出指定成交額的訂單 (e.g., 購買交易對 BTCUSDT，成交額要求 10000UDST)"""
        return self.__trade.order_quote_qty(self, side, quoteOrderQty, symbol, order_type)

#endregion

#region Klines related APIs

    def get_tradable_symbols(self, quote_asset, include_assets, exclude_assets):
        """找出以 quote_asset 報價，且目前可交易、可送市價單、非槓桿型的交易對"""
        return self.__klines.get_tradable_symbols(quote_asset, include_assets, exclude_assets)

    def get_latest_price(self, trade_symbol):
        """取得指定交易對的最新報價"""
        return self.__klines.get_latest_price(trade_symbol)

    def get_historical_klines(self, symbol, KLINE_INTERVAL, fromdate, todate):
        return self.__klines.get_historical_klines(symbol, KLINE_INTERVAL, fromdate, todate)

    def get_klines(self, symbol, klines_limit=100, interval=Client.KLINE_INTERVAL_15MINUTE):
        """
        Get klines data
        :param symbol: symbol e.g., BTCUSDT、DOGEUSDT
        :param klines_limit: K線的數量限制
        :param interval: 幾分的K線資料
        :return: klines data
        """
        return self.__klines.get_klines(symbol, klines_limit, interval)
#endregion
