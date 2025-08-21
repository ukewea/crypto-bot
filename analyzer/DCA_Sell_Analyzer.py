import logging.config
import time
from .analyzer import *

_log = logging.getLogger(__name__)


class DCA_Sell_Analyzer(Analyzer):
    """
    Dollar Cost Averaging (DCA) Sell Analyzer
    Always sells at regular intervals regardless of price, implementing DCA sell strategy.
    Only sells if there are positions to sell.
    """
    
    def __init__(self, config):
        """建構式"""
        _log.debug("Init DCA_Sell_Analyzer")
        
        self.tag = "DCA_SELL"
        self.min_interval_between_sell = config["DCA"]["min_interval_between_sell"]
        
        # In-memory storage for last sell times per asset (symbol -> timestamp)
        self._last_sell_times = {}
        
        _log.info(f"DCA_Sell_Analyzer initialized with min_interval_between_sell: {self.min_interval_between_sell} seconds")

    def analyze(self, klines, position):
        """
        DCA Sell Analysis - Always sell if enough time has passed since last sell and there are positions
        :param klines: K線資料 (not used for DCA, but required by interface)
        :param position: Position information containing asset symbol and quantities
        :return: Trade.SELL if interval passed and has positions, Trade.PASS otherwise
        """
        # Extract asset symbol from the position object
        asset_symbol = position.asset_symbol
        
        # Check if we have any positions to sell
        if position.open_quantity <= 0:
            _log.debug(f"[DCA_SELL] {asset_symbol}: No positions to sell")
            return Trade.PASS
        
        current_time = time.time()
        last_sell_time = self._last_sell_times.get(asset_symbol, 0)
        time_since_last_sell = current_time - last_sell_time
        
        _log.debug(f"[DCA_SELL] {asset_symbol}: Time since last sell: {time_since_last_sell:.0f}s, Required interval: {self.min_interval_between_sell}s")
        
        if time_since_last_sell >= self.min_interval_between_sell:
            _log.info(f"[DCA_SELL] {asset_symbol}: DCA sell interval reached, recommending SELL")
            return Trade.SELL
        else:
            remaining_time = self.min_interval_between_sell - time_since_last_sell
            _log.debug(f"[DCA_SELL] {asset_symbol}: Still {remaining_time:.0f}s until next DCA sell")
            return Trade.PASS
    
    def record_successful_sell(self, asset_symbol):
        """
        Record a successful sell to update the timer
        This should be called by the trading system after a successful sale
        """
        current_time = time.time()
        self._last_sell_times[asset_symbol] = current_time
        _log.info(f"[DCA_SELL] {asset_symbol}: Recorded successful sell at {current_time}")
    
    def get_last_sell_time(self, asset_symbol):
        """Get the last sell time for an asset (for debugging/monitoring)"""
        return self._last_sell_times.get(asset_symbol, 0)
    
    def get_time_until_next_sell(self, asset_symbol):
        """Get seconds remaining until next sell is allowed"""
        current_time = time.time()
        last_sell_time = self._last_sell_times.get(asset_symbol, 0)
        time_since_last_sell = current_time - last_sell_time
        remaining = max(0, self.min_interval_between_sell - time_since_last_sell)
        return remaining