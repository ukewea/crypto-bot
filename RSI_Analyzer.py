import talib
import numpy
from analyzer import *

class RSI_Analyzer(Analyzer):
    # 建構式
    def __init__(self, config):
        self.RSI_PERIOD = config.analyzer["RSI"]["period"]
        self.RSI_OVERSELL = config.analyzer["RSI"]["oversell"]
        self.RSI_UNDERBUY = config.analyzer["RSI"]["underbuy"]

    def SetRule(self, RSI_PERIOD, RSI_UNDERBUY, RSI_OVERSELL):
        self.RSI_PERIOD = RSI_PERIOD
        self.RSI_OVERSELL = RSI_OVERSELL
        self.RSI_UNDERBUY = RSI_UNDERBUY

    def Analyze(self, closes):
        np_closes = numpy.array(closes)
        rsi = talib.RSI(np_closes, self.RSI_PERIOD)
        last_rsi = rsi[-2]
        if last_rsi >= self.RSI_OVERSELL:
            return Trade.SELL
        elif last_rsi <= self.RSI_UNDERBUY:
            return Trade.BUY
        else:
            return Trade.PASS
