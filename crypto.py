from binance.client import Client
from binance.enums import *

class Crypto:
    # 建構式
    def __init__(self, config):
        self.client = Client(config.auth["API_KEY"], config.auth["API_SECRET"])

    def get_exchange_symbol(self, quoteAsset):
        exchange_info = self.client.get_exchange_info()
        # print(type(exchange_info))
        # with open('exchange_info.json', 'w') as outfile:
        #     json.dump(exchange_info, outfile, indent=4)

        # 找出以 USDT 報價，且目前可交易、可送市價單、非槓桿型的交易對
        # print([item for item in exchange_info['symbols'] if item['symbol'] == "BTCUSDT"])
        trade_with_usdt = [item for item in exchange_info['symbols']
                        if item['quoteAsset'].upper() == quoteAsset]

        return [symbol['symbol'] for symbol in trade_with_usdt if symbol['status'].upper() == "TRADING" and "MARKET" in symbol['orderTypes']and not "LEVERAGED" in symbol['permissions']]

    def get_klines(self, symbol, klines_limit = 100, interval=Client.KLINE_INTERVAL_15MINUTE):
        """
        Get klines data
        :param symbol: symbol e.q. BTCUSDT、DOGEUSDT
        :param klines_limit: K線的數量限制
        :param interval: 幾分的K線資料
        :return: klines data
        """
        klines = self.client.get_klines(
        symbol=symbol,
        interval=Client.KLINE_INTERVAL_15MINUTE,
        limit=klines_limit)
        if len(klines) < klines_limit:
            raise Exception(f"No enough data for {symbol} {len(klines)}")

        return [Kline(data) for data in klines]

    # def get_closed_prices(self, symbol, klines_limit = 100, interval=Client.KLINE_INTERVAL_15MINUTE):
    #     klines = self.get_klines(symbol, klines_limit, interval)
    #     return [kline.close for kline in klines]


class Kline:
    def __init__(self, dict):
        """
        [
        1499040000000,      # Open time
        "0.01634790",       # Open
        "0.80000000",       # High
        "0.01575800",       # Low
        "0.01577100",       # Close
        "148976.11427815",  # Volume
        1499644799999,      # Close time
        "2434.19055334",    # Quote asset volume
        308,                # Number of trades
        "1756.87402397",    # Taker buy base asset volume
        "28.46694368",      # Taker buy quote asset volume
        "17928899.62484339" # Can be ignored
        ]
        """
        self.open_time = dict[0]
        self.open = dict[1]
        self.high = dict[2]
        self.low = dict[3]
        self.close = dict[4]
        self.volume = dict[5]
        self.close_time = dict[6]
        self.quote_asset_volume = dict[7]
        self.number_of_trades = dict[8]
        self.taker_buy_base_asset_volume = dict[9]
        self.taker_buy_quote_asset_volume = dict[10]
