import time
import file_based_record
import csv
from binance.client import Client
from Analyzer import *
from crypto import *
from config import *
tic = time.perf_counter()
config = Config()
crypto = Crypto(config)

# 交易用的貨幣，等同於買股票用的現金
cash_asset = "USDT"

# 要排除的貨幣
exclude_assets = []

watching_symbols = crypto.get_tradable_symbols(cash_asset, exclude_assets)
equities_balance = crypto.get_equities_balance(watching_symbols, cash_asset)

fromdate = "1 Jan, 2021"
enddate = "1 May, 2021"
KLINE_INTERVAL = Client.KLINE_INTERVAL_1HOUR

for symbol_info in watching_symbols:
    symbol = symbol_info.symbol
    base_asset = symbol_info.base_asset

    asset_balance = equities_balance[base_asset]
    if asset_balance is None:
        # 沒辦法看到該幣餘額，推斷帳號無法交易此幣，所以不計算策略
        print(f"Cannot get {base_asset} balance in your account")
        continue

    csvfile = open(f'data\{symbol}.csv', 'w', newline='') 
    candlestick_writer = csv.writer(csvfile, delimiter=',')
    candlesticks = crypto.get_historical_klines(symbol, KLINE_INTERVAL, fromdate, enddate)
    for candlestick in candlesticks:
        candlestick[0] = candlestick[0] / 1000 # 為了轉成float型態
        candlestick_writer.writerow(candlestick)

    csvfile.close()