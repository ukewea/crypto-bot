import backtrader as bt
import datetime
from Analyzer import *
from crypto import *
from config import *

config = Config()
crypto = Crypto(config)

# 交易用的貨幣，等同於買股票用的現金
cash_asset = "USDT"

# 要排除的貨幣
exclude_assets = ["DOGE"]

watching_symbols = crypto.get_tradable_symbols(cash_asset, exclude_assets)
equities_balance = crypto.get_equities_balance(watching_symbols, cash_asset)
willr_analyzer = WILLR_Analyzer(config)
rsi_analyzer = RSI_Analyzer(config)

for symbol_info in watching_symbols:
    symbol = symbol_info.symbol
    base_asset = symbol_info.base_asset

    asset_balance = equities_balance[base_asset]
    if asset_balance is None:
        # 沒辦法看到該幣餘額，推斷帳號無法交易此幣，所以不計算策略
        print(f"Cannot get {base_asset} balance in your account")
        continue

    #fromdate = datetime.datetime.strptime('2020-07-01', '%Y-%m-%d')
    #todate = datetime.datetime.strptime('2020-07-12', '%Y-%m-%d')
    data = bt.feeds.GenericCSVData(dataname=f'data\{symbol}.csv', dtformat=2, compression=15, timeframe=bt.TimeFrame.Minutes)#, fromdate=fromdate, todate=todate)
    #willr_analyzer.Backtest(data)
    rsi_analyzer.Backtest(data)