import abc
from enum import Enum
import backtrader as bt

class Trade(Enum):
     PASS = 0
     BUY = 1
     SELL = 2

class Analyzer(metaclass=abc.ABCMeta):
    # 建構式
    def __init__(self):
        pass

    @abc.abstractmethod
    def Analyze(self, klines):
        return NotImplemented
