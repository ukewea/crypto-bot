if __name__ == '__main__':
    import time
    import csv
    import os
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

    fromdate = "01-01-2021"
    todate = "05-01-2021" # API有問題，目前不管怎樣都會抓到今天為止
    KLINE_INTERVAL = Client.KLINE_INTERVAL_15MINUTE
    BASE_DIR = 'history_klines'

    os.makedirs(BASE_DIR, mode=0o755, exist_ok=True)

    for symbol_info in watching_symbols:
        symbol = symbol_info.symbol
        base_asset = symbol_info.base_asset

        csv_path = os.path.join(BASE_DIR, f'{symbol}.csv')

        # if os.path.exists(csv_path):
        #     print(f'[{symbol}] skip...')
        #     continue

        csvfile = open(csv_path, 'w', newline='')
        candlestick_writer = csv.writer(csvfile, delimiter=',')
        print(f'[{symbol}] start downloading...')
        candlesticks = crypto.get_historical_klines(symbol, KLINE_INTERVAL, fromdate, todate)
        for candlestick in candlesticks:
            candlestick[0] = candlestick[0] / 1000 # 為了轉成float型態
            candlestick_writer.writerow(candlestick)

        print(f'[{symbol}] downloaded to {csv_path}')
        csvfile.close()
