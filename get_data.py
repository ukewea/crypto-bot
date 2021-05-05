if __name__ == '__main__':
    import time
    from time import perf_counter
    import file_based_asset_positions
    import position
    from decimal import Decimal
    from Analyzer import *
    from crypto import *
    from binance.enums import *
    from crypto_report import CryptoReport
    from config import *
    import send_order

    # 交易用的貨幣，等同於買股票用的現金
    cash_asset = "USDT"

    # 每個幣種最多投入的資金
    max_fund_per_currency = Decimal("20")

    # Some objects load from local file
    config = Config()
    crypto = Crypto(config)
    notif = config.spawn_nofification_platform()

    # 印出倉位
    # for k, v in record.positions.items():
    #     print(v)

    # Analyzers
    rsi_analyzer = RSI_Analyzer(config)
    willr_analyzer = WILLR_Analyzer(config)

    # Data fetched via API
    exchange_info = crypto.get_exchange_info()
    # print(exchange_info)
    watching_symbols = crypto.get_tradable_symbols(cash_asset, config.exclude_coins)
    equities_balance = crypto.get_equities_balance(watching_symbols, cash_asset)
    record = file_based_asset_positions.AssetPositions(watching_symbols, cash_asset)
    report = CryptoReport(config=config)

    # print(watching_symbols)

    while True:
        tic = time.perf_counter()

        total_free_balance_as_cash_asset = Decimal('0')
        total_locked_balance_as_cash_asset = Decimal('0')

        free_cash = equities_balance[cash_asset].free
        print(f'Free cash: {free_cash}')

        market_price_dict = {}
        for symbol_info in watching_symbols:
            trade_symbol = symbol_info.symbol
            base_asset = symbol_info.base_asset

            asset_balance = equities_balance[base_asset]
            if asset_balance is None:
                # 沒辦法看到該幣餘額，推斷帳號無法交易此幣，所以不計算策略
                print(f"Cannot get {base_asset} balance in your account")
                continue

            try:
                # print(f'[{trade_symbol}] Downloading K lines')
                klines = crypto.get_klines(trade_symbol, 20)
                latest_quote = klines[-1].close
                total_free_balance_as_cash_asset += asset_balance.free * latest_quote
                total_locked_balance_as_cash_asset += asset_balance.locked * latest_quote

                trade_rsi = rsi_analyzer.Analyze(klines)
                trade_willr = willr_analyzer.Analyze(klines)
                # if trade_rsi == Trade.PASS and trade_willr == Trade.PASS:
                #     continue

                print(f"[{trade_symbol}]: RSI = {trade_rsi}, WILLR = {trade_willr}")
                try:
                    if trade_rsi == Trade.BUY or trade_willr == Trade.BUY:
                        # 確認剩餘的現金是否大於最大投入限額
                        # 若剩餘的現金小於限額，將剩餘現金投入
                        free_cash = equities_balance[cash_asset].free
                        max_fund = free_cash.min(max_fund_per_currency)

                        trade_result = send_order.open_position_with_max_fund(
                            api_client=crypto,
                            base_asset=base_asset,
                            trade_symbol=trade_symbol,
                            cash_asset=cash_asset,
                            max_fund=max_fund,
                            asset_position=record.positions[base_asset],
                            symbol_info=symbol_info,
                        )

                        if trade_result.ok:
                            report.add_transaction(trade_result.transactions)
                            for transaction in trade_result.transactions:
                                print(transaction)
                    elif trade_rsi == Trade.SELL or trade_willr == Trade.SELL:
                        trade_result = send_order.close_all_position(
                            api_client=crypto,
                            base_asset=base_asset,
                            trade_symbol=trade_symbol,
                            cash_asset=cash_asset,
                            asset_position=record.positions[base_asset],
                            symbol_info=symbol_info,
                        )

                        if trade_result.ok:
                            report.add_transaction(trade_result.transactions)
                            for transaction in trade_result.transactions:
                                print(transaction)
                    else:
                        continue
                finally:
                    time.sleep(0.5)
                    market_price_dict[symbol_info] = latest_quote
                    # report.update_market_price(symbol_info, latest_quote)

            except Exception as e:
                print(e)
                time.sleep(3)

        # free_cash = equities_balance[cash_asset].free
        # print(f"可用現貨估值 ({cash_asset}) = {total_free_balance_as_cash_asset}"
        #     f", +{cash_asset} = {total_free_balance_as_cash_asset + free_cash_asset}")
        # print(f"下單凍結現貨估值 ({cash_asset}) = {total_locked_balance_as_cash_asset}"
        #     f", +{cash_asset} = {total_locked_balance_as_cash_asset + locked_cash_asset}")

        try:
            # 有買入或賣出時，從 API 更新餘額，取得最新的剩餘現金
            equities_balance = crypto.get_equities_balance(watching_symbols, cash_asset)
        except  Exception as e:
            print(e)

        report.update_market_price(market_price_dict)
        toc = time.perf_counter()
        time_elapsed = toc - tic
        print(f"Download quotes & technical analysis took {time_elapsed:0.4f} seconds")
        cool_down_time = 60 - time_elapsed
        if cool_down_time > 0:
            print(f"Sleep {cool_down_time} before next loop")
            time.sleep(cool_down_time)
