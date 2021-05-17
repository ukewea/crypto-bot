import logging.config

import backtrader as bt
import numpy
import talib
from config import *

from .analyzer import *

_log = logging.getLogger(__name__)


class RSI_Analyzer(Analyzer):
    def __init__(self, config):
        """建構式"""
        _log.debug("Init RSI_Analyzer")

        self.tag = "RSI"
        self.period = config["RSI"]["period"]
        self.oversell = config["RSI"]["oversell"]
        self.underbuy = config["RSI"]["underbuy"]

    def set_rule(self, period, oversell, underbuy):
        self.period = period
        self.oversell = oversell
        self.underbuy = underbuy

    def backtest(self, klines):
        """回測"""
        cerebro = bt.Cerebro()
        data = klines
        cerebro.adddata(data)
        cerebro.addstrategy(RSI_Strategy)
        cerebro.run()
        cerebro.plot()

    def analyze(self, klines, position):
        """
        RSI Analyzer
        :param klines: K線資料
        :return: 建議交易行為 Trade.SELL || Trade.BUY || Trade.PASS
        """
        closes = [float(candle.close) for candle in klines]
        np_closes = numpy.array(closes)
        rsi = talib.RSI(np_closes, self.period)
        last_rsi = rsi[-1]
        if last_rsi >= self.oversell:
            return Trade.SELL
        elif last_rsi <= self.underbuy:
            return Trade.BUY
        else:
            return Trade.PASS

class RSI_Strategy(bt.Strategy):
    def __init__(self):
        config = Config()
        self.period = config.analyzer["RSI"]["period"]
        self.oversell = config.analyzer["RSI"]["oversell"]
        self.underbuy = config.analyzer["RSI"]["underbuy"]
        self.rsi = bt.indicators.RSI_EMA(self.data, period = self.period)

    def next(self):
        if self.rsi >= self.oversell and self.position: # 已持倉:
            self.order = self.close()

        if self.rsi <= self.underbuy and not self.position: # 未持倉:
            size = self.broker.get_cash() / self.data.close[0]
            self.order = self.buy(size=size)
