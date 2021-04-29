import talib
import numpy
from analyzer import *

class RSI_Analyzer(Analyzer):
    # 建構式
    def __init__(self):
        self.RSI_PERIOD = 14
        self.RSI_OVERSELL = 70
        self.RSI_UNDERBUY = 30
    
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
