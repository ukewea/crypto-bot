import talib
import numpy
from .analyzer import *
from config import *
import backtrader as bt

class WILLR_Analyzer(Analyzer):
    # 建構式
    def __init__(self, config):
        self.PERIOD = config.analyzer["WILLR"]["period"]
        self.OVERSELL = config.analyzer["WILLR"]["oversell"]
        self.UNDERBUY = config.analyzer["WILLR"]["underbuy"]

    def SetRule(self, PERIOD, OVERSELL, UNDERBUY):
        self.PERIOD = PERIOD
        self.OVERSELL = OVERSELL
        self.UNDERBUY = UNDERBUY

    def Analyze(self, klines):
        """
        WILLR - Williams' %R Analyzer
        :param klines: K線資料
        :return: 建議交易行為 Trade.SELL || Trade.BUY || Trade.PASS
        """
        highs, lows, closes = zip(*[(candle.high, candle.low, candle.close) for candle in klines])
        willrs = talib.WILLR(numpy.array(highs), numpy.array(lows), numpy.array(closes), self.PERIOD)
        last_willr = willrs[-2]
        if last_willr >= self.OVERSELL:
            return Trade.SELL
        elif last_willr <= self.UNDERBUY:
            return Trade.BUY
        else:
            return Trade.PASS
    
    def Backtest(self, klines):
        cerebro = bt.Cerebro()
        data = klines
        cerebro.adddata(data)
        cerebro.addstrategy(WILLR_Strategy)
        cerebro.run()
        cerebro.plot()         

class WILLR_Strategy(bt.Strategy):
    def __init__(self):
        config = Config()
        self.PERIOD = config.analyzer["WILLR"]["period"]
        self.OVERSELL = config.analyzer["WILLR"]["oversell"]
        self.UNDERBUY = config.analyzer["WILLR"]["underbuy"]
        self.WILLR = bt.indicators.WilliamsR(self.data, period = self.PERIOD)

    def next(self):
        if self.WILLR >= self.OVERSELL and self.position: # 已持倉:
            self.close()

        if self.WILLR <= self.UNDERBUY and not self.position: # 未持倉:
            size = self.broker.get_cash() / self.data.close[0]
            self.order = self.buy(size=size)