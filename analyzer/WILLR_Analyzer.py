import logging.config

import backtrader as bt
import numpy
import talib
from config import *

from .analyzer import *

_log = logging.getLogger(__name__)


class WILLR_Analyzer(Analyzer):
    def __init__(self, config):
        """建構式"""
        _log.debug("Init WILLR_Analyzer")

        self.tag = "WILLR"
        self.period = config["WILLR"]["period"]
        self.oversell = config["WILLR"]["oversell"]
        self.underbuy = config["WILLR"]["underbuy"]

    def set_rule(self, period, oversell, underbuy):
        self.period = period
        self.oversell = oversell
        self.underbuy = underbuy

    def analyze(self, klines, position):
        """
        WILLR - Williams' %R Analyzer
        :param klines: K線資料
        :return: 建議交易行為 Trade.SELL || Trade.BUY || Trade.PASS
        """
        highs, lows, closes = zip(
            *[(float(candle.high), float(candle.low), float(candle.close)) for candle in klines])
        willrs = talib.WILLR(numpy.array(highs), numpy.array(
            lows), numpy.array(closes), self.period)
        # upper, middle, lower = talib.BBANDS(numpy.array(closes), timeperiod=200, nbdevup=2, nbdevdn=2, matype=0)
        last_willr = willrs[-1]
        if last_willr >= self.oversell and position.open_quantity > 0:
            # buyPrice = 0
            # buyQuantity = 0
            # for transaction in position.transactions:
            #     buyPrice += transaction.price
            #     buyQuantity += transaction.quantity

            # buyPrice = buyPrice/buyQuantity
            # if closes[-1] < middle[-1] and closes[-1] > buyPrice:
            #     return Trade.PASS
            # else:
            return Trade.SELL
        elif last_willr <= self.underbuy:
            return Trade.BUY
        else:
            return Trade.PASS

    def backtest(self, klines):
        """回測"""
        cerebro = bt.Cerebro()
        data = klines
        cerebro.adddata(data)
        cerebro.addstrategy(WILLR_Strategy)
        cerebro.run()
        cerebro.plot()


class WILLR_Strategy(bt.Strategy):
    def __init__(self):
        config = Config()
        self.period = config.analyzer["WILLR"]["period"]
        self.oversell = config.analyzer["WILLR"]["oversell"]
        self.underbuy = config.analyzer["WILLR"]["underbuy"]
        self.WILLR = bt.indicators.WilliamsR(self.data, period=self.period)
        self.boll = bt.indicators.BollingerBands(period=200, devfactor=2)

    def next(self):
        if self.WILLR[0] >= self.oversell and self.position:  # 已持倉:
            if self.data.close[0] < self.boll.lines.mid[0] and self.data.close[0] > self.position.price:  # 賺錢
                return
            else:  # 虧錢
                self.close()

        if self.WILLR[0] <= self.underbuy and not self.position:  # 未持倉:
            size = self.broker.get_cash() / self.data.close[0]
            self.order = self.buy(size=size)

        # if  self.position: # 已持倉:
        #     data = self.WILLR[-1] + self.WILLR[-2] + self.WILLR[-3] + self.WILLR[-4] + self.WILLR[-5]
        #     if data/5 <= self.oversell:
        #         return

        #     if self.WILLR[0] >= self.oversell:
        #         self.close()

        # if  not self.position: # 未持倉:
        #     data = self.WILLR[-1] + self.WILLR[-2] + self.WILLR[-3] + self.WILLR[-4] + self.WILLR[-5]
        #     if data/5 >= self.underbuy:
        #         return

        #     if self.WILLR[0] <= self.underbuy:
        #         size = self.broker.get_cash() / self.data.close[0]
        #         self.order = self.buy(size=size)

    # def next(self):
    #     orders = self.broker.get_orders_open()
    #     # Cancel open orders so we can track the median line
    #     if orders:
    #         for order in orders:
    #             self.broker.cancel(order)
    #     # sum = 0
    #     # for i in range(1, 5):
    #     #     sum += self.sma5[-i] - self.sma10[-i]

    #     # if abs(sum/self.sma5[-i]) < 0.08:
    #     #     return

    #     if not self.position:
    #         if self.sma5[0] - self.sma10[0] >= 0 and self.sma5[-1] - self.sma10[-1] < 0:
    #             size = self.broker.get_cash() / self.data.close[0]
    #             self.buy(size=size)

    #     else:
    #         if self.sma5[0] - self.sma10[0] <= 0 and self.sma5[-1] - self.sma10[-1] > 0:
    #             self.close()

    # def next(self):

    #     orders = self.broker.get_orders_open()
    #     # Cancel open orders so we can track the median line
    #     if orders:
    #         for order in orders:
    #             self.broker.cancel(order)

    #     if not self.position:
    #         if self.WILLR[0] <= self.underbuy and self.data.close < self.boll.lines.bot:
    #             size = self.broker.get_cash() / self.data.close[0]
    #             self.buy(size=size)

    #     else:
    #         if self.WILLR[0] >= self.oversell and self.data.close > self.boll.lines.top:
    #             self.close()
