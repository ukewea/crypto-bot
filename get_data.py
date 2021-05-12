import logging.config
import os

# initialize logger before importing any other modules
os.makedirs('logs', mode=0o755, exist_ok=True)
os.makedirs('logs-debug', mode=0o755, exist_ok=True)

logging.config.fileConfig(os.path.join('user-config', 'logging.ini'))

from os import listdir
from os.path import isfile, join
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


class TradeLoopRunner:
    def __init__(self, config):
        self.__config = config

        # 交易用的貨幣，等同於買股票用的現金
        self.__cash_currency = config.position_manage['cash_currency']
        _log.info(f"Cash currency: {self.__cash_currency}")

        # 每個幣種最多投入的資金
        self.__max_fund_per_currency = Decimal(config.position_manage['max_fund_per_currency'])
        _log.info(f"Max fund per currency: {self.__max_fund_per_currency}")

        # 最多開倉的貨幣數量
        self.__max_open_positions = None
        if "max_open_positions" in config.position_manage:
            self.__max_open_positions = int(config.position_manage['max_open_positions'])
            _log.info(f"Max open positions: {self.__max_open_positions}")

        # 最大投入成本
        self.__max_total_open_cost = None
        if "max_total_open_cost" in config.position_manage:
            self.__max_total_open_cost = Decimal(config.position_manage['max_total_open_cost'])
            _log.info(f"Max total open cost: {self.__max_total_open_cost}")

        # 要排除、不交易的貨幣
        self.__exclude_currencies = config.position_manage['exclude_currencies']
        _log.info(f"Excluded currencies: {self.__exclude_currencies}")

        self.__crypto = Crypto(config)
        self.__notif = config.spawn_nofification_platform()
        self.__tx_q = queue.Queue()
        self.__rx_q = queue.Queue()

        if self.__notif is not None:
            self.__notif.start_worker_thread(self.__tx_q, self.__rx_q)

        # Analyzers
        self.__rsi_analyzer = RSI_Analyzer(config)
        self.__willr_analyzer = WILLR_Analyzer(config)

        # 需要使用交易所 API，延後於 start_loop() 內取得
        self.__watching_symbols = None
        self.__record = None
        self.__free_cash = None


    def start_loop(self):
        """啟動分析全部交易對的迴圈"""
        # exchange_info = self.__crypto.get_exchange_info()
        # _log.debug(exchange_info)

        self.__watching_symbols = self.__crypto.get_tradable_symbols(self.__cash_currency, self.__exclude_currencies)
        _log.debug(f"Watching trading symbols: {self.__watching_symbols}")

        equities_balance = self.__crypto.get_equities_balance(self.__watching_symbols, self.__cash_currency)
        self.__record = file_based_asset_positions.AssetPositions(self.__watching_symbols, self.__cash_currency)

        # Google Sheet 報表 client
        report = CryptoReport(config=self.__config)

        # 印出持倉
        for k, v in self.__record.positions.items():
            if v.open_quantity > 0:
                _log.info(f"Position from save file: {str(v)}")

        # 當交易量達到一定數值後，向外發出目前剩餘的現金
        acc_transaction_count_before_notify_free_cash = 0

        self.__free_cash = equities_balance[self.__cash_currency].free
        keep_loop_running = True

        while keep_loop_running:
            tic = time.perf_counter()

            # 給這一輪的 transaction 一個 group ID
            round_id = str(time.time_ns())
            _log.debug(f"Starting new round, round_id = {round_id}")

            _log.debug(f'Available {self.__cash_currency}: {self.__free_cash}')
            market_price_dict = {}
            transactions_made = []

            for symbol_info in self.__watching_symbols:
                self.__analyze_a_currency(
                    symbol_info=symbol_info,
                    equities_balance=equities_balance,
                    report=report,
                    round_id=round_id,
                    market_price_dict=market_price_dict,
                    transactions_made=transactions_made,
                )

                if os.path.exists("stoppp"):
                    _log.warning("Stop file detected, stop trading symbol loop")
                    keep_loop_running = False
                    os.rename("stoppp", "_stoppp")
                    break

            self.__try_notify_transactions(transactions_made)
            report.update_market_price(market_price_dict, self.__record.positions)

            if not keep_loop_running:
                _log.warning("Stop file detected, stop the outer loop")
                toc = time.perf_counter()
                time_elapsed = toc - tic
                _log.debug(f"Round stopped early, took {time_elapsed:0.4f} seconds")
                break

            try:
                # 從 API 更新餘額，取得最新剩餘現金
                _log.debug(f"Fetching latest {self.__cash_currency} balance from exchange")
                equities_balance = self.__crypto.get_equities_balance(self.__watching_symbols, self.__cash_currency)
                self.__free_cash = equities_balance[self.__cash_currency].free

                if len(transactions_made) > 0:
                    _log.info(f"Cash balance = {self.__free_cash} after transactions are made")

                # 累計交易數量夠多時，向外通知目前剩餘的現金
                acc_transaction_count_before_notify_free_cash += len(transactions_made)
                if acc_transaction_count_before_notify_free_cash >= 20:
                    if self.__notif is not None:
                        self.__tx_q.put(QueueTask(TaskType.NOTIFY_CASH_BALANCE, f"{self.__free_cash.normalize():f} {self.__cash_currency}"))
                    acc_transaction_count_before_notify_free_cash = 0

                time.sleep(1)
            except:
                _log.exception(f"Catched an exception while fetching latest {self.__cash_currency} balance from exchange")

            toc = time.perf_counter()
            time_elapsed = toc - tic
            _log.debug(f"Round ended, took {time_elapsed:0.4f} seconds")

            cool_down_time = 60 - time_elapsed
            if cool_down_time > 0:
                _log.debug(f"Sleep {cool_down_time} seconds before next round")
                time.sleep(cool_down_time)

        self.__tx_q.put(QueueTask(TaskType.STOP_WORKER_THREAD, None))
        self.__tx_q.join()

    def close_all_positions(self):
        """平倉記錄的所有部位"""
        _log.info("----- Closing all positions -----")

        self.__watching_symbols = self.__crypto.get_tradable_symbols(self.__cash_currency, self.__exclude_currencies)
        _log.debug(f"Watching trading symbols: {self.__watching_symbols}")

        equities_balance = self.__crypto.get_equities_balance(self.__watching_symbols, self.__cash_currency)
        self.__record = file_based_asset_positions.AssetPositions(self.__watching_symbols, self.__cash_currency)

        # Google Sheet 報表 client
        report = CryptoReport(config=self.__config)

        self.__free_cash = equities_balance[self.__cash_currency].free
        market_price_dict = {}
        transactions_made = []

        # 給這一輪的 transaction 一個 group ID
        round_id = str(time.time_ns())

        try:
            for symbol_info in self.__watching_symbols:
                trade_symbol = symbol_info.symbol
                base_asset = symbol_info.base_asset

                _log.debug(f"[{trade_symbol}] Selling all {base_asset} for {self.__cash_currency}")

                self.__do_action_by_analysis_result(
                    symbol_info=symbol_info,
                    equities_balance=equities_balance,
                    report=report,
                    round_id=round_id,
                    market_price_dict=market_price_dict,
                    transactions_made=transactions_made,
                    buy_sell_action=Trade.SELL,
                )

                if os.path.exists("stoppp"):
                    _log.warning("Stop file detected, stop trading symbol loop")
                    keep_loop_running = False
                    os.rename("stoppp", "_stoppp")
                    break

                time.sleep(0.1)
        except:
            _log.exception(f"[{trade_symbol}] Catched an exception while selling all {base_asset} for {self.__cash_currency}")

        self.__try_notify_transactions(transactions_made)
        _log.info("----- Done closing all positions -----")


    def __analyze_a_currency(
        self,
        symbol_info: WatchingSymbol,
        equities_balance,
        report: CryptoReport,
        round_id: str,
        market_price_dict,
        transactions_made,
    ):
        """分析某一貨幣走勢，並根據分析結果向交易所送出相應訂單"""
        trade_symbol = symbol_info.symbol
        base_asset = symbol_info.base_asset

        asset_balance = equities_balance[base_asset]
        if asset_balance is None:
            # 沒辦法看到該幣餘額，推斷帳號無法交易此幣，所以不計算策略
            _log.warning(f"Cannot get {base_asset} balance in your account, skip analyzing this currency")
            return

        try:
            _log.debug(f'[{trade_symbol}] Downloading K lines')
            klines = self.__crypto.get_klines(trade_symbol, 20, Client.KLINE_INTERVAL_1DAY)
            if klines is None:
                return

            latest_quote = klines[-1].close

            # trade_rsi = self.__rsi_analyzer.Analyze(klines)
            trade_willr = self.__willr_analyzer.Analyze(klines, self.__record.positions[base_asset])
            # if trade_rsi == Trade.PASS and trade_willr == Trade.PASS:
            #     continue

            # _log.debug(f"[{trade_symbol}] RSI = {trade_rsi}, WILLR = {trade_willr}")
            _log.debug(f"[{trade_symbol}] WILLR = {trade_willr}")

            self.__do_action_by_analysis_result(
                symbol_info=symbol_info,
                equities_balance=equities_balance,
                report=report,
                round_id=round_id,
                market_price_dict=market_price_dict,
                transactions_made=transactions_made,
                buy_sell_action=trade_willr,
            )

            time.sleep(0.1)
            market_price_dict[symbol_info] = latest_quote
        except:
            _log.exception(f"[{trade_symbol}] Catched an exception in trading symbol loop")
            time.sleep(3)


    def __do_action_by_analysis_result(
        self,
        symbol_info: WatchingSymbol,
        equities_balance,
        report: CryptoReport,
        round_id: str,
        market_price_dict,
        transactions_made,
        buy_sell_action,
    ):
        trade_symbol = symbol_info.symbol
        base_asset = symbol_info.base_asset

        if buy_sell_action == Trade.BUY:
            can_send_buy_order = self.__can_send_buy_order_permitted_by_config(
                trade_symbol=trade_symbol,
            )

            if can_send_buy_order:
                # 確認剩餘的現金是否大於最大投入限額
                # 若剩餘的現金小於限額，將剩餘現金投入
                max_fund = self.__free_cash.min(self.__max_fund_per_currency)

                trade_result = send_order.open_position_with_max_fund(
                    api_client=self.__crypto,
                    base_asset=base_asset,
                    trade_symbol=trade_symbol,
                    cash_asset=self.__cash_currency,
                    max_fund=max_fund,
                    asset_position=self.__record.positions[base_asset],
                    symbol_info=symbol_info,
                    round_id=round_id,
                )

                self.__process_order_result(trade_result, trade_symbol, report, transactions_made)
        elif buy_sell_action == Trade.SELL:
            trade_result = send_order.close_all_position(
                api_client=self.__crypto,
                base_asset=base_asset,
                trade_symbol=trade_symbol,
                cash_asset=self.__cash_currency,
                asset_position=self.__record.positions[base_asset],
                symbol_info=symbol_info,
                round_id=round_id,
            )

            self.__process_order_result(trade_result, trade_symbol, report, transactions_made)
        else:
            return


    def __process_order_result(
        self,
        trade_result: send_order.OrderResult,
        trade_symbol: str,
        report: CryptoReport,
        tx_made: List[position.Transaction],
    ):
        if not trade_result.ok:
            return

        report.add_transaction(trade_result.transactions)
        for tx in trade_result.transactions:
            _log.info(tx)
            tx_made.append(tx)

        self.__cal_new_cash_balance(trade_result)
        _log.debug(f'[{trade_symbol}] {self.__cash_currency} bal. after {trade_result.side}: {self.__free_cash}')


    def __cal_new_cash_balance(
        self,
        trade_result: send_order.OrderResult
    ) -> Decimal:
        """更新此輪剩餘現金"""

        if not trade_result.ok:
            return

        total_cost_cash = Decimal('0')
        total_commission_cash = Decimal('0')

        for transact in trade_result.transactions:
            # 在此輪結束前還是會向交易所取得最新的餘額，所以計算有些微誤差應可接受
            total_cost_cash = transact.quantity * transact.price

            # 若手續費使用現金幣支付也要計入
            if transact.commission_asset == self.__cash_currency:
                total_commission_cash += transact.commission

        if trade_result.side == SIDE_BUY:
            self.__free_cash -= total_cost_cash
        elif trade_result.side == SIDE_SELL:
            self.__free_cash += total_cost_cash
        else:
            log.error(f"Cannot calculate new cash balance due to unknown trade_result.side '{trade_result.side}'")
            return

        self.__free_cash -= total_commission_cash


    def __can_send_buy_order_permitted_by_config(
        self,
        trade_symbol: str,
    ) -> bool:
        """依照 config 限制，目前狀況是否還允許送出買單至交易所"""
        if self.__max_open_positions is not None:
            cur_open_count = self.__record.cal_total_open_position_count()
            if cur_open_count >= self.__max_open_positions:
                _log.warning(
                    f"[{trade_symbol}] Current opened position count exceeds limit, skip the BUY"
                    f" (limit = {self.__max_open_positions}, current open = {cur_open_count}"
                )
                return False

        if self.__max_total_open_cost is not None:
            cur_total_open_cost = self.__record.cal_total_open_cost()
            if cur_total_open_cost >= self.__max_total_open_cost:
                _log.warning(
                    f"[{trade_symbol}] Current total open cost exceeds limit, skip the BUY"
                    f" (limit = {self.__max_total_open_cost}, current open = {cur_total_open_cost}"
                )
                return False

        return True

    def __try_notify_transactions(self, transactions_made):
        try:
            # 跑完一輪後再一次送出全部的交易通知
            if self.__notif is not None and len(transactions_made) > 0:
                self.__tx_q.put(QueueTask(TaskType.NOTIFY_TX, transactions_made))
        except:
            _log.exception(f"Catched an exception while sending transactions notification")


if __name__ == '__main__':
    _log.info("App starts")

    # Some objects load from local file
    config = Config()

    trade_loop_runner = TradeLoopRunner(config)
    trade_loop_runner.start_loop()
    # trade_loop_runner.close_all_positions()

    _log.debug("App exited")
