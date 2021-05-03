if __name__ == '__main__':
    import time
    import file_based_asset_positions
    import position
    from decimal import Decimal
    from Analyzer import *
    from crypto import *
    from binance.enums import *
    from config import *

    tic = time.perf_counter()
    config = Config()
    crypto = Crypto(config)

    exchange_info = crypto.get_exchange_info()

    # 交易用的貨幣，等同於買股票用的現金
    cash_asset = "USDT"

    # 要排除的貨幣
    with open("exclude-coins.json", "r+") as json_file:
        exclude_assets = json.load(json_file)

    watching_symbols = crypto.get_tradable_symbols(cash_asset, exclude_assets)
    equities_balance = crypto.get_equities_balance(watching_symbols, cash_asset)
    record = file_based_asset_positions.AssetPositions(watching_symbols, cash_asset)

    # 印出倉位
    # for k, v in record.positions.items():
    #     print(v)

    rsi_analyzer = RSI_Analyzer(config)
    willr_analyzer = WILLR_Analyzer(config)

    total_free_balance_as_cash_asset = 0.0
    total_locked_balance_as_cash_asset = 0.0

    # crypto.order_quote_qty("BUY", 14, "DOGEUSDT")

    # {'symbol': 'DOGEUSDT', 'orderId': 786775885, 'orderListId': -1, 'clientOrderId': 'gQp1YKqpjVBMwlkUIcCgWV', 'transactTime': , 'price': '0.00000000', 'origQty': '36.60000000', 'executedQty': '36.60000000', 'cummulativeQuoteQty': '13.96546200', 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'MARKET', 'side': 'BUY', 'fills': [{'price': '0.38157000', 'qty': '36.60000000', 'commission': '0.00001676', 'commissionAsset': 'BNB', 'tradeId': 142837993}]}

    transaction = position.Transaction(1620011227094, SIDE_BUY, "DOGE", "DOGEUSDT", Decimal('36.60000000'), Decimal('0.38157000'), Decimal('0.00001676'), 'BNB')
    record.positions["DOGE"].add_transaction(transaction)

    transaction = position.Transaction(1620011227094, SIDE_BUY, "DOGE", "DOGEUSDT", Decimal('36.60000000'), Decimal('0.38157000'), Decimal('0.00001676'), 'BNB')
    record.positions["DOGE"].add_transaction(transaction)

    transaction = position.Transaction(1620011227094, SIDE_BUY, "DOGE", "DOGEUSDT", Decimal('36.60000000'), Decimal('0.38157000'), Decimal('0.00001676'), 'BNB')
    record.positions["DOGE"].add_transaction(transaction)

    transaction = position.Transaction(1620011227094, SIDE_SELL, "DOGE", "DOGEUSDT", Decimal('36.60000000'), Decimal('0.38157000'), Decimal('0.00001676'), 'BNB')
    record.positions["DOGE"].add_transaction(transaction)

    transaction = position.Transaction(1620011227094, SIDE_SELL, "DOGE", "DOGEUSDT", Decimal('36.60000000'), Decimal('0.38157000'), Decimal('0.00001676'), 'BNB')
    record.positions["DOGE"].add_transaction(transaction)

    transaction = position.Transaction(1620011227094, SIDE_SELL, "DOGE", "DOGEUSDT", Decimal('36.60000000'), Decimal('0.38157000'), Decimal('0.00001676'), 'BNB')
    record.positions["DOGE"].add_transaction(transaction)

    raise Exception()

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
    # fund_per_asset = free_cash_asset / len(watching_symbols)
    print(f"可用 {cash_asset} = {free_cash_asset}, 下單凍結 {cash_asset} = {locked_cash_asset}")
    # print(f"平均到 {len(watching_symbols)} 項資產，每項資產資金 ({cash_asset}) = {fund_per_asset}")
    print(f"可用現貨估值 ({cash_asset}) = {total_free_balance_as_cash_asset}"
        f", +{cash_asset} = {total_free_balance_as_cash_asset + free_cash_asset}")
    print(f"下單凍結現貨估值 ({cash_asset}) = {total_locked_balance_as_cash_asset}"
        f", +{cash_asset} = {total_locked_balance_as_cash_asset + locked_cash_asset}")
