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

    def get_closed_prices(self, symbol, klines_limit = 100, interval=Client.KLINE_INTERVAL_15MINUTE):
        klines = self.client.get_klines(
        symbol=symbol,
        interval=Client.KLINE_INTERVAL_15MINUTE,
        limit=klines_limit)
        if len(klines) < klines_limit:
            raise Exception(f"No enough data for {symbol} {len(klines)}")

        return [float(data[4]) for data in klines] # data[4]:K的收盤價

        
