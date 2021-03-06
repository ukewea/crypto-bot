import abc
from enum import Enum
import backtrader as bt
import logging.config


_log = logging.getLogger(__name__)


class Trade(Enum):
    PASS = 0
    BUY = 1
    SELL = 2


class Analyzer(metaclass=abc.ABCMeta):
    # 建構式
    def __init__(self):
        pass

    @abc.abstractmethod
    def analyze(self, klines, position):
        return NotImplemented
