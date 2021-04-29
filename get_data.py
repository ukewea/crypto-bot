import time
from Analyzer import *
from crypto import *
from config import *

tic = time.perf_counter()
crypto = Crypto(Config())
watching_symbols = crypto.get_exchange_symbol("USDT")
rsi_analyzer = RSI_Analyzer()
willr_analyzer = WILLR_Analyzer()
for symbol in watching_symbols:
    try:
        klines = crypto.get_klines(symbol)
        trade = rsi_analyzer.Analyze(klines)
        print(f"[{symbol}]:")
        print(f"    RSI: {trade}")
        trade = willr_analyzer.Analyze(klines)
        print(f"    WILLR: {trade}")
    except Exception as e:
        print(e.message)

toc = time.perf_counter()
print(f"Downloaded quotes took {toc - tic:0.4f} seconds")