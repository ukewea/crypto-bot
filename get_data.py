if __name__ == '__main__':
    import logging.config
    import os

    # initialize logger before importing any other modules
    os.makedirs('logs', mode=0o755, exist_ok=True)
    os.makedirs('logs-debug', mode=0o755, exist_ok=True)

    logging.config.fileConfig(os.path.join('user-config', 'logging.ini'))

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

    log = logging.getLogger(__name__)
    log.info("Starting...")

    # Some objects load from local file
    config = Config()

    # 交易用的貨幣，等同於買股票用的現金
    cash_currency = config.position_manage['cash_currency']
    log.info(f"Cash currency: {cash_currency}")

    # 每個幣種最多投入的資金
    max_fund_per_currency = Decimal(config.position_manage['max_fund_per_currency'])
    log.info(f"Max fund per currency: {max_fund_per_currency}")

    # 最多開倉的貨幣數量
    max_open_positions = int(config.position_manage['max_open_positions'])
    log.info(f"Max open positions: {max_open_positions}")

    # 要排除、不交易的貨幣
    exclude_currencies = config.position_manage['exclude_currencies']
    log.info(f"Excluded currencies: {exclude_currencies}")

    crypto = Crypto(config)
    notif = config.spawn_nofification_platform()

    # Analyzers
    rsi_analyzer = RSI_Analyzer(config)
    willr_analyzer = WILLR_Analyzer(config)

    # Data fetched via API
    exchange_info = crypto.get_exchange_info()
    # print(exchange_info)
    watching_symbols = crypto.get_tradable_symbols(cash_currency, exclude_currencies)
    log.debug(f"Watching trading symbols: {watching_symbols}")

    equities_balance = crypto.get_equities_balance(watching_symbols, cash_currency)
    record = file_based_asset_positions.AssetPositions(watching_symbols, cash_currency)
    report = CryptoReport(config=config)

    # 印出持倉
    for k, v in record.positions.items():
        if v.open_quantity > 0:
            log.info(f"Position from save file: {str(v)}")

    keep_loop_running = True

    while keep_loop_running:
        tic = time.perf_counter()

        # 給這一輪的 transaction 一個 group ID
        round_id = str(time.time_ns())
        log.debug(f"Starting new round, round_id = {round_id}")

        total_free_balance_as_cash_asset = Decimal('0')
        total_locked_balance_as_cash_asset = Decimal('0')

        free_cash = equities_balance[cash_currency].free
        log.debug(f'Available {cash_currency}: {free_cash}')
        market_price_dict = {}
        transactions_made = []

        for symbol_info in watching_symbols:
            trade_symbol = symbol_info.symbol
            base_asset = symbol_info.base_asset

            asset_balance = equities_balance[base_asset]
            if asset_balance is None:
                # 沒辦法看到該幣餘額，推斷帳號無法交易此幣，所以不計算策略
                log.warning(f"Cannot get {base_asset} balance in your account, skip analyzing this currency")
                continue

            try:
                log.debug(f'[{trade_symbol}] Downloading K lines')
                klines = crypto.get_klines(trade_symbol, 20)
                latest_quote = klines[-1].close
                total_free_balance_as_cash_asset += asset_balance.free * latest_quote
                total_locked_balance_as_cash_asset += asset_balance.locked * latest_quote

                trade_rsi = rsi_analyzer.Analyze(klines)
                trade_willr = willr_analyzer.Analyze(klines)
                # if trade_rsi == Trade.PASS and trade_willr == Trade.PASS:
                #     continue

                log.debug(f"[{trade_symbol}]: RSI = {trade_rsi}, WILLR = {trade_willr}")
                try:
                    if trade_willr == Trade.BUY:
                        # 確認剩餘的現金是否大於最大投入限額
                        # 若剩餘的現金小於限額，將剩餘現金投入
                        free_cash = equities_balance[cash_currency].free
                        max_fund = free_cash.min(max_fund_per_currency)

                        trade_result = send_order.open_position_with_max_fund(
                            api_client=crypto,
                            base_asset=base_asset,
                            trade_symbol=trade_symbol,
                            cash_asset=cash_currency,
                            max_fund=max_fund,
                            asset_position=record.positions[base_asset],
                            symbol_info=symbol_info,
                            round_id=round_id,
                        )

                        if trade_result.ok:
                            report.add_transaction(trade_result.transactions)
                            for transaction in trade_result.transactions:
                                log.info(transaction)
                                if notif is not None:
                                    transactions_made.append(transaction)
                    elif trade_willr == Trade.SELL:
                        trade_result = send_order.close_all_position(
                            api_client=crypto,
                            base_asset=base_asset,
                            trade_symbol=trade_symbol,
                            cash_asset=cash_currency,
                            asset_position=record.positions[base_asset],
                            symbol_info=symbol_info,
                            round_id=round_id,
                        )

                        if trade_result.ok:
                            report.add_transaction(trade_result.transactions)
                            for transaction in trade_result.transactions:
                                log.info(transaction)
                                if notif is not None:
                                    transactions_made.append(transaction)
                    else:
                        continue
                finally:
                    time.sleep(0.5)
                    market_price_dict[symbol_info] = latest_quote

            except:
                logging.exception("Catched an exception in trading symbol loop")
                time.sleep(3)
            finally:
                if os.path.exists("stoppp"):
                    log.warning("stop file detected, break trading symbol loop")
                    os.rename("stoppp", "_stoppp")
                    keep_loop_running = False
                    break

        # free_cash = equities_balance[cash_currency].free
        # print(f"可用現貨估值 ({cash_currency}) = {total_free_balance_as_cash_asset}"
        #     f", +{cash_currency} = {total_free_balance_as_cash_asset + free_cash_asset}")
        # print(f"下單凍結現貨估值 ({cash_currency}) = {total_locked_balance_as_cash_asset}"
        #     f", +{cash_currency} = {total_locked_balance_as_cash_asset + locked_cash_asset}")

        try:
            # 有買入或賣出時，從 API 更新餘額，取得最新的剩餘現金
            log.debug(f"Fetching latest {cash_currency} balance from exchange")
            equities_balance = crypto.get_equities_balance(watching_symbols, cash_currency)
        except:
            logging.exception(f"Catched an exception while fetching latest {cash_currency} balance from exchange")

        try:
            # 跑完一輪後再一次送出全部的交易通知
            if notif is not None and len(transactions_made) > 0:
                log.debug("Sending transactions notification")
                notif.notify_transactions(transactions_made)
        except:
            logging.exception(f"Catched an exception while sending transactions notification")

        report.update_market_price(market_price_dict, record.positions)
        toc = time.perf_counter()
        time_elapsed = toc - tic
        log.debug(f"Round ended, took {time_elapsed:0.4f} seconds")

        if not keep_loop_running:
            log.warning("stop file detected, break the outer loop")
            break

        cool_down_time = 60 - time_elapsed
        if cool_down_time > 0:
            log.debug(f"Sleep {cool_down_time} seconds before next round")
            time.sleep(cool_down_time)
