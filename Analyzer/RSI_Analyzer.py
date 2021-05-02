import talib
import numpy
from .analyzer import *

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
