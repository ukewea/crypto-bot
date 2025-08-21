import logging.config
import time
from .analyzer import *

_log = logging.getLogger(__name__)


class DCA_Buy_Analyzer(Analyzer):
    """
    Dollar Cost Averaging (DCA) Buy Analyzer
    Always buys at regular intervals regardless of price, implementing DCA buy strategy.
    """
    
    def __init__(self, config):
        """建構式"""
        _log.debug("Init DCA_Buy_Analyzer")
        
        self.tag = "DCA"
        self.min_interval_between_buy = config["DCA"]["min_interval_between_buy"]
        
        # In-memory storage for last buy times per asset (symbol -> timestamp)
        self._last_buy_times = {}
        
        _log.info(f"DCA_Buy_Analyzer initialized with min_interval_between_buy: {self.min_interval_between_buy} seconds")

    def analyze(self, klines, position):
        """
        DCA Analysis - Always buy if enough time has passed since last buy
        :param klines: K線資料 (not used for DCA, but required by interface)
        :param position: Position information containing asset symbol
        :return: Trade.BUY if interval passed, Trade.PASS otherwise
        """
        # Extract asset symbol from the position object
        asset_symbol = position.asset_symbol
        
        current_time = time.time()
        last_buy_time = self._last_buy_times.get(asset_symbol, 0)
        time_since_last_buy = current_time - last_buy_time
        
        _log.debug(f"[DCA] {asset_symbol}: Time since last buy: {time_since_last_buy:.0f}s, Required interval: {self.min_interval_between_buy}s")
        
        if time_since_last_buy >= self.min_interval_between_buy:
            _log.info(f"[DCA] {asset_symbol}: DCA interval reached, recommending BUY")
            return Trade.BUY
        else:
            remaining_time = self.min_interval_between_buy - time_since_last_buy
            _log.debug(f"[DCA] {asset_symbol}: Still {remaining_time:.0f}s until next DCA buy")
            return Trade.PASS
    
    def record_successful_buy(self, asset_symbol):
        """
        Record a successful buy to update the timer
        This should be called by the trading system after a successful purchase
        """
        current_time = time.time()
        self._last_buy_times[asset_symbol] = current_time
        _log.info(f"[DCA] {asset_symbol}: Recorded successful buy at {current_time}")
    
    def get_last_buy_time(self, asset_symbol):
        """Get the last buy time for an asset (for debugging/monitoring)"""
        return self._last_buy_times.get(asset_symbol, 0)
    
    def get_time_until_next_buy(self, asset_symbol):
        """Get seconds remaining until next buy is allowed"""
        current_time = time.time()
        last_buy_time = self._last_buy_times.get(asset_symbol, 0)
        time_since_last_buy = current_time - last_buy_time
        remaining = max(0, self.min_interval_between_buy - time_since_last_buy)
        return remaining