import logging.config
import os

# initialize logger before importing any other modules
os.makedirs('logs', mode=0o755, exist_ok=True)
os.makedirs('logs-debug', mode=0o755, exist_ok=True)

logging.config.fileConfig(os.path.join('user-config', 'logging.ini'))

import time
from time import perf_counter
import file_based_asset_positions
import queue
from decimal import Decimal
from binance.enums import *
from typing import List
import position
from Analyzer import *
from crypto import *
from crypto_report import CryptoReport
from config import *
import send_order
from notification_platforms.queue_task import *

_log = logging.getLogger(__name__)


def __process_order_result(
    trade_result: send_order.OrderResult,
    report: CryptoReport,
    notif,
    tx_made: List[position.Transaction],
):
    if not trade_result.ok:
        return

    report.add_transaction(trade_result.transactions)
    for tx in trade_result.transactions:
        _log.info(tx)
        if notif is not None:
            tx_made.append(tx)

def __cal_new_cash_balance(
    cash_now: Decimal,
    cash_currency: str,
    trade_result: send_order.OrderResult
) -> Decimal:
    """更新此輪剩餘現金"""

    if not trade_result.ok:
        return cash_now

    total_cost_cash = Decimal('0')
    total_commission_cash = Decimal('0')

    for transact in trade_result.transactions:
        # 在此輪結束前還是會向交易所取得最新的餘額，所以計算有些微誤差應可接受
        total_cost_cash = transact.quantity * transact.price

        # 若手續費使用現金幣支付也要計入
        if transact.commission_asset == cash_currency:
            total_commission_cash += transact.commission

    if trade_result.side == SIDE_BUY:
        cash_now -= total_cost_cash
    elif trade_result.side == SIDE_SELL:
        cash_now += total_cost_cash
    else:
        log.error(f"Cannot calculate new cash balance due to unknown trade_result.side {trade_result.side}")
        return cash_now

    cash_now -= total_commission_cash

    return cash_now

if __name__ == '__main__':
    _log = logging.getLogger(__name__)
    _log.info("App starts")

    # Some objects load from local file
    config = Config()

    # 交易用的貨幣，等同於買股票用的現金
    cash_currency = config.position_manage['cash_currency']
    _log.info(f"Cash currency: {cash_currency}")

    # 每個幣種最多投入的資金
    max_fund_per_currency = Decimal(config.position_manage['max_fund_per_currency'])
    _log.info(f"Max fund per currency: {max_fund_per_currency}")

    # 最多開倉的貨幣數量
    max_open_positions = int(config.position_manage['max_open_positions'])
    _log.info(f"Max open positions: {max_open_positions}")

    # 要排除、不交易的貨幣
    exclude_currencies = config.position_manage['exclude_currencies']
    _log.info(f"Excluded currencies: {exclude_currencies}")

    crypto = Crypto(config)
    notif = config.spawn_nofification_platform()
    tx_q = queue.Queue()
    rx_q = queue.Queue()

    if notif is not None:
        notif.start_worker_thread(tx_q, rx_q)

    # Analyzers
    rsi_analyzer = RSI_Analyzer(config)
    willr_analyzer = WILLR_Analyzer(config)

    # Data fetched via API
    exchange_info = crypto.get_exchange_info()
    # _log.debug(exchange_info)

    watching_symbols = crypto.get_tradable_symbols(cash_currency, exclude_currencies)
    _log.debug(f"Watching trading symbols: {watching_symbols}")

    equities_balance = crypto.get_equities_balance(watching_symbols, cash_currency)
    record = file_based_asset_positions.AssetPositions(watching_symbols, cash_currency)
    report = CryptoReport(config=config)

    # 印出持倉
    for k, v in record.positions.items():
        if v.open_quantity > 0:
            _log.info(f"Position from save file: {str(v)}")

    keep_loop_running = True

    # 當交易量達到一定數值後，向外發出目前剩餘的現金
    acc_transaction_count_before_notify_free_cash = 0

    while keep_loop_running:
        tic = time.perf_counter()

        # 給這一輪的 transaction 一個 group ID
        round_id = str(time.time_ns())
        _log.debug(f"Starting new round, round_id = {round_id}")

        free_cash = equities_balance[cash_currency].free
        _log.debug(f'Available {cash_currency}: {free_cash}')
        market_price_dict = {}
        transactions_made = []

        for symbol_info in watching_symbols:
            trade_symbol = symbol_info.symbol
            base_asset = symbol_info.base_asset

            asset_balance = equities_balance[base_asset]
            if asset_balance is None:
                # 沒辦法看到該幣餘額，推斷帳號無法交易此幣，所以不計算策略
                _log.warning(f"Cannot get {base_asset} balance in your account, skip analyzing this currency")
                continue

            try:
                _log.debug(f'[{trade_symbol}] Downloading K lines')
                klines = crypto.get_klines(trade_symbol, 250)
                latest_quote = klines[-1].close

                trade_rsi = rsi_analyzer.Analyze(klines)
                trade_willr = willr_analyzer.Analyze(klines, record.positions[base_asset])
                # if trade_rsi == Trade.PASS and trade_willr == Trade.PASS:
                #     continue

                _log.debug(f"[{trade_symbol}] RSI = {trade_rsi}, WILLR = {trade_willr}")
                try:
                    if trade_willr == Trade.BUY:
                        # 確認剩餘的現金是否大於最大投入限額
                        # 若剩餘的現金小於限額，將剩餘現金投入
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
                            __process_order_result(trade_result, report, notif, transactions_made)
                            free_cash = __cal_new_cash_balance(free_cash, cash_currency, trade_result)
                            _log.debug(f'[{trade_symbol}] {cash_currency} bal. after BUY: {free_cash}')
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
                            __process_order_result(trade_result, report, notif, transactions_made)
                            free_cash = __cal_new_cash_balance(free_cash, cash_currency, trade_result)
                            _log.debug(f'[{trade_symbol}] {cash_currency} bal. after SELL: {free_cash}')
                    else:
                        continue
                finally:
                    time.sleep(0.1)
                    market_price_dict[symbol_info] = latest_quote

            except:
                logging.exception(f"[{trade_symbol}] Catched an exception in trading symbol loop")
                time.sleep(3)
            finally:
                if os.path.exists("stoppp"):
                    _log.warning("stop file detected, break trading symbol loop")
                    keep_loop_running = False
                    os.rename("stoppp", "_stoppp")
                    break
        try:
            # 跑完一輪後再一次送出全部的交易通知
            if notif is not None and len(transactions_made) > 0:
                tx_q.put(QueueTask(TaskType.NOTIFY_TX, transactions_made))
        except:
            logging.exception(f"Catched an exception while sending transactions notification")

        report.update_market_price(market_price_dict, record.positions)

        if not keep_loop_running:
            _log.warning("stop file detected, break the outer loop")
            toc = time.perf_counter()
            time_elapsed = toc - tic
            _log.debug(f"Round stopped early, took {time_elapsed:0.4f} seconds")
            break

        try:
            if len(transactions_made) > 0:
                # 有買入或賣出時，從 API 更新餘額，取得最新的剩餘現金
                _log.debug(f"Fetching latest {cash_currency} balance from exchange")
                equities_balance = crypto.get_equities_balance(watching_symbols, cash_currency)

                acc_transaction_count_before_notify_free_cash += len(transactions_made)
                if acc_transaction_count_before_notify_free_cash >= 20:
                    if notif is not None:
                        tx_q.put(QueueTask(TaskType.NOTIFY_CASH_BALANCE, f"{free_cash.normalize():f} {cash_currency}"))
                    acc_transaction_count_before_notify_free_cash = 0

                time.sleep(1)
        except:
            logging.exception(f"Catched an exception while fetching latest {cash_currency} balance from exchange")

        toc = time.perf_counter()
        time_elapsed = toc - tic
        _log.debug(f"Round ended, took {time_elapsed:0.4f} seconds")

        cool_down_time = 60 - time_elapsed
        if cool_down_time > 0:
            _log.debug(f"Sleep {cool_down_time} seconds before next round")
            time.sleep(cool_down_time)

    tx_q.put(QueueTask(TaskType.STOP_WORKER_THREAD, None))
    tx_q.join()
    _log.debug("App exited")
