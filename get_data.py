import time
import websocket
import json
import pprint
import talib
import numpy
import config
from binance.client import Client
from binance.enums import *

client = Client(config.API_KEY, config.API_SECRET)
watching_symbols = []

usdt_quote_count = 0
trading_count = 0
allow_market_order = 0
not_leveraged = 0

RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
KLINES_LIMIT = 100

exchange_info = client.get_exchange_info()
# print(type(exchange_info))
with open('exchange_info.json', 'w') as outfile:
    json.dump(exchange_info, outfile, indent=4)

# 找出以 USDT 報價，且目前可交易、可送市價單、非槓桿型的交易對
# print([item for item in exchange_info['symbols'] if item['symbol'] == "BTCUSDT"])
trade_with_usdt = [item for item in exchange_info['symbols']
                   if item['quoteAsset'].upper() == "USDT"]

watching_symbols = [symbol['symbol'] for symbol in trade_with_usdt if symbol['status'].upper() == "TRADING" and "MARKET" in symbol['orderTypes']and not "LEVERAGED" in symbol['permissions']]
tic = time.perf_counter()

for symbol in watching_symbols:
    try:
        temp_data = client.get_klines(
            symbol=symbol,
            interval=Client.KLINE_INTERVAL_15MINUTE,
            limit=KLINES_LIMIT,
        )

        if len(temp_data) < KLINES_LIMIT:
            print(f"No enough data for {symbol} {len(temp_data)}")
            continue
        # print(f"Downloaded {symbol}")
        # print(temp_data)
        closes = [float(data[4]) for data in temp_data]

        continue

        np_closes = numpy.array(closes)
        rsi = talib.RSI(np_closes, RSI_PERIOD)
        # print(f"all RSI for {symbol} calculated so far")
        # print(rsi)
        last_rsi = rsi[-2]

        # quit(1)

    except Exception as e:
        print(e.message)

    # TODO catch return status
    #print(temp_data)

toc = time.perf_counter()
print(f"Downloaded quotes took {toc - tic:0.4f} seconds")

print(client.response.headers)

# print("Watching symbols: {}".format(watching_symbols))

prices = client.get_all_tickers()

with open('get_all_tickers.json', 'w') as outfile:
    json.dump(prices, outfile, indent=4)
