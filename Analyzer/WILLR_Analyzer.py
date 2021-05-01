import talib
import numpy
from .analyzer import *

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
        highs, lows, closes = zip(*[(float(candle.high), float(candle.low), float(candle.close)) for candle in klines])
        willrs = talib.WILLR(numpy.array(highs), numpy.array(lows), numpy.array(closes), self.PERIOD)
        last_willr = willrs[-2]
        if last_willr >= self.OVERSELL:
            return Trade.SELL
        elif last_willr <= self.UNDERBUY:
            return Trade.BUY
        else:
            return Trade.PASS
