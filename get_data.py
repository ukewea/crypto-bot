import time
from Analyzer import *
from crypto import *
from config import *

tic = time.perf_counter()
config = Config()
crypto = Crypto(config)

account = crypto.get_account()
balances = account['balances']

watching_symbols = crypto.get_tradable_symbols("USDT")
rsi_analyzer = RSI_Analyzer(config)
willr_analyzer = WILLR_Analyzer(config)

total_free_balance_as_usdt = 0.0
total_locked_balance_as_usdt = 0.0

for symbol_info in watching_symbols:
    symbol = symbol_info[0]
    base_asset = symbol_info[1]

    asset_balance = [x for x in balances if x['asset'] == base_asset]
    if len(asset_balance) < 1:
        # 沒辦法看到該幣餘額，推斷帳號無法交易此幣，所以不計算策略
        print(f"Cannot get {base_asset} balance in your account")
        continue

    try:
        klines = crypto.get_klines(symbol)
        latest_quote = float(klines[-1].close)
        free_balance = float(asset_balance[0]['free'])
        locked_balance = float(asset_balance[0]['locked'])

        total_free_balance_as_usdt += free_balance * latest_quote
        total_locked_balance_as_usdt += locked_balance * latest_quote

        trade = rsi_analyzer.Analyze(klines)
        if trade == Trade.PASS:
            continue

        print(f"[{symbol}]:")
        print(f"    RSI: {trade}")
        trade = willr_analyzer.Analyze(klines)
        print(f"    WILLR: {trade}")
    except Exception as e:
        print(e)

toc = time.perf_counter()
print(f"Download quotes & technical analysis took {toc - tic:0.4f} seconds")

usdt_balance = [x for x in balances if x['asset'] == "USDT"]
free_usdt = float(usdt_balance[0]['free'])
locked_usdt = float(usdt_balance[0]['locked'])
print(f"Your permission: {account['permissions']}")
print(f"Your USDT balance info: {usdt_balance}")
print(f"All free spot asset balance as USDT = {total_free_balance_as_usdt}"
    f", +USDT = {total_free_balance_as_usdt + free_usdt}")
print(f"All locked spot asset balance as USDT = {total_locked_balance_as_usdt}"
    f", +USDT = {total_locked_balance_as_usdt + locked_usdt}")
