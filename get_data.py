import time
from crypto import *
from config import *
from RSI_Analyzer import *

tic = time.perf_counter()
config = Config()
crypto = Crypto(config)
watching_symbols = crypto.get_exchange_symbol("USDT")
analyzer = RSI_Analyzer(config)

for symbol in watching_symbols:
    try:
        closes = crypto.get_closed_prices(symbol)
        trade = analyzer.Analyze(closes)
        print(f"{symbol} suggest: {trade}")
    except:
        print(e.message) # 語法待確認

toc = time.perf_counter()
print(f"Downloaded quotes took {toc - tic:0.4f} seconds")