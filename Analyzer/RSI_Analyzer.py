import talib
import numpy
from .analyzer import *
from config import *
import backtrader as bt

class RSI_Analyzer(Analyzer):
    # 建構式
    def __init__(self, config):
        self.PERIOD = config.analyzer["RSI"]["period"]
        self.OVERSELL = config.analyzer["RSI"]["oversell"]
        self.UNDERBUY = config.analyzer["RSI"]["underbuy"]

    def SetRule(self, PERIOD, OVERSELL, UNDERBUY):
        self.PERIOD = PERIOD
        self.OVERSELL = OVERSELL
        self.UNDERBUY = UNDERBUY

    def Backtest(self, klines):
        cerebro = bt.Cerebro()
        data = klines
        cerebro.adddata(data)
        cerebro.addstrategy(RSI_Strategy)
        cerebro.run()
        cerebro.plot()         

    def Analyze(self, klines):
        """
        RSI Analyzer
        :param klines: K線資料
        :return: 建議交易行為 Trade.SELL || Trade.BUY || Trade.PASS
        """
        closes = [candle.close for candle in klines]
        np_closes = numpy.array(closes)
        rsi = talib.RSI(np_closes, self.PERIOD)
        last_rsi = rsi[-2]
        if last_rsi >= self.OVERSELL:
            return Trade.SELL
        elif last_rsi <= self.UNDERBUY:
            return Trade.BUY
        else:
            return Trade.PASS

class RSI_Strategy(bt.Strategy):
    def __init__(self):
        config = Config()
        self.PERIOD = config.analyzer["RSI"]["period"]
        self.OVERSELL = config.analyzer["RSI"]["oversell"]
        self.UNDERBUY = config.analyzer["RSI"]["underbuy"]
        self.rsi = bt.indicators.RSI_EMA(self.data, period = self.PERIOD)

    def next(self):
        if self.rsi >= self.OVERSELL and self.position: # 已持倉:
            self.order = self.close()

        if self.rsi <= self.UNDERBUY and not self.position: # 未持倉:
            size = self.broker.get_cash() / self.data.close[0]
            self.order = self.buy(size=size)