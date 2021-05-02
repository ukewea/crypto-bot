import time
import file_based_record

from Analyzer import *
from crypto import *
from config import *
tic = time.perf_counter()
config = Config()
crypto = Crypto(config)

# 交易用的貨幣，等同於買股票用的現金
cash_asset = "USDT"

# 要排除的貨幣
exclude_assets = ["DOGE"]

watching_symbols = crypto.get_tradable_symbols(cash_asset, exclude_assets)
equities_balance = crypto.get_equities_balance(watching_symbols, cash_asset)
record = file_based_record.FileBasedRecord(watching_symbols, cash_asset)

# 印出倉位
for k, v in record.positions.items():
    print(v)

rsi_analyzer = RSI_Analyzer(config)
willr_analyzer = WILLR_Analyzer(config)

total_free_balance_as_cash_asset = 0.0
total_locked_balance_as_cash_asset = 0.0

for symbol_info in watching_symbols:
    symbol = symbol_info.symbol
    base_asset = symbol_info.base_asset

    asset_balance = equities_balance[base_asset]
    if asset_balance is None:
        # 沒辦法看到該幣餘額，推斷帳號無法交易此幣，所以不計算策略
        print(f"Cannot get {base_asset} balance in your account")
        continue

    try:
        klines = crypto.get_klines(symbol)
        latest_quote = klines[-1].close
        total_free_balance_as_cash_asset += asset_balance.free * latest_quote
        total_locked_balance_as_cash_asset += asset_balance.locked * latest_quote

        trade_rsi = rsi_analyzer.Analyze(klines)
        trade_willr = willr_analyzer.Analyze(klines)
        if trade_rsi == Trade.PASS and trade_willr == Trade.PASS:
            continue

        print(f"[{symbol}]:")
        print(f"    RSI: {trade_rsi}")
        print(f"    WILLR: {trade_willr}")
    except Exception as e:
        print(e)

toc = time.perf_counter()
print(f"Download quotes & technical analysis took {toc - tic:0.4f} seconds")

free_cash_asset = equities_balance[cash_asset].free
locked_cash_asset = equities_balance[cash_asset].locked
fund_per_asset = free_cash_asset / len(watching_symbols)
print(f"可用 {cash_asset} = {free_cash_asset}, 下單凍結 {cash_asset} = {locked_cash_asset}")
print(f"平均到 {len(watching_symbols)} 項資產，每項資產資金 ({cash_asset}) = {fund_per_asset}")
print(f"可用現貨估值 ({cash_asset}) = {total_free_balance_as_cash_asset}"
    f", +{cash_asset} = {total_free_balance_as_cash_asset + free_cash_asset}")
print(f"下單凍結現貨估值 ({cash_asset}) = {total_locked_balance_as_cash_asset}"
    f", +{cash_asset} = {total_locked_balance_as_cash_asset + locked_cash_asset}")
