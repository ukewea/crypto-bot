import logging.config
from datetime import datetime
from decimal import Decimal

from binance.enums import *

_log = logging.getLogger(__name__)


class Position:
    """單一種貨幣的倉位"""

    def __init__(self, asset_symbol, on_update, dict):
        """
        從資料來源 (dict) 還原倉位紀錄到 memory
        asset_symbol: 貨幣代號
        transaction: 交易紀錄
        """
        self.asset_symbol = asset_symbol
        self.__on_update_transaction = on_update
        self.transactions = list()

        if dict is None:
            self.open_quantity = Decimal(0.0)
            self.open_cost = Decimal(0.0)
            self.realized_gain = Decimal(0.0)
            self.total_commission_as_usdt = Decimal(0.0)
            return

        # print(dict)
        self.open_quantity = Decimal(dict['open_quantity'])
        self.open_cost = Decimal(dict['open_cost'])
        self.realized_gain = Decimal(dict['realized_gain'])
        self.total_commission_as_usdt = Decimal(
            dict['total_commission_as_usdt'])

        for transact in dict['transactions']:
            # print(transact)
            round_id = None
            if 'round_id' in transact and transact['round_id'] != "None":
                round_id = transact['round_id']

            self.transactions.append(Transaction(
                time=int(transact['time']),
                activity=transact['activity'],
                symbol=transact['symbol'],
                trade_symbol=transact['trade_symbol'],
                quantity=Decimal(transact['quantity']),
                price=Decimal(transact['price']),
                commission=Decimal(transact['commission']),
                commission_asset=transact['commission_asset'],
                commission_as_usdt=Decimal(transact['commission_as_usdt']),
                round_id=round_id,
                order_id=transact['order_id'],
                trade_id=transact['trade_id'],
                closed_trade_ids=transact['closed_trade_ids']))

    def to_dict(self):
        # 輸出全部轉 string，保留數字精度
        return {
            'open_quantity': str(self.open_quantity),
            'open_cost': str(self.open_cost),
            'realized_gain': str(self.realized_gain),
            'total_commission_as_usdt': str(self.total_commission_as_usdt),
            'transactions': [t.to_dict() for t in self.transactions],
        }

    def add_transaction(self, transaction):
        if transaction.activity == SIDE_BUY:
            self.open_quantity += transaction.quantity
            self.open_cost += transaction.quantity * transaction.price

            # 如果手續費是從購買的貨幣中內扣，將這些手續費從 open_quantity 中去除
            if transaction.commission_asset == transaction.symbol:
                self.open_quantity -= transaction.commission

        elif transaction.activity == SIDE_SELL:
            current_avg_price = self.open_cost / self.open_quantity
            purchase_cost = (transaction.quantity *
                             self.open_cost) / self.open_quantity
            realized_gain = (transaction.price -
                             current_avg_price) * transaction.quantity

            # print(f"current_avg_price = {current_avg_price}")
            # print(f"purchase_cost = {purchase_cost}")
            # print(f"realized_gain = {realized_gain}")

            self.open_quantity -= transaction.quantity
            self.open_cost -= purchase_cost
            self.realized_gain += realized_gain
        else:
            raise Exception("Unknown transaction activity")

        self.total_commission_as_usdt += transaction.commission_as_usdt
        self.transactions.append(transaction)
        self.__on_update_transaction(self.asset_symbol)

    def get_transactions_count(self):
        """取得交易完成總數"""
        return len(self.transactions)

    def __str__(self):
        if self.open_quantity > 0:
            return f"{str(self.asset_symbol)}: {self.open_quantity.normalize():f} @{self.open_cost.normalize():f}"
            f", realized = {self.realized_gain.normalize():f}"

        return f"{str(self.asset_symbol)}: no position, realized = {self.realized_gain.normalize():f}"


class Transaction:
    def __init__(
        self,
        time: int,
        activity: str,
        symbol: str,
        trade_symbol: str,
        quantity: Decimal,
        price: Decimal,
        commission: Decimal,
        commission_asset: str,
        commission_as_usdt: Decimal,
        round_id: str,
        order_id: str,
        trade_id: str,
        closed_trade_ids: list
    ):
        self.time = time
        self.activity = activity
        self.symbol = symbol
        self.trade_symbol = trade_symbol
        self.quantity = quantity
        self.price = price
        self.commission = commission
        self.commission_asset = commission_asset
        self.commission_as_usdt = commission_as_usdt
        self.round_id = round_id
        self.order_id = order_id
        self.trade_id = trade_id

        if activity == SIDE_SELL and (closed_trade_ids is None or len(closed_trade_ids) < 1):
            # _log.warning(f"closed_trade_ids in SELL transaction {trade_id} is empty")
            pass
        if closed_trade_ids is None:
            self.closed_trade_ids = []
        else:
            self.closed_trade_ids = closed_trade_ids

    def to_dict(self):
        # 輸出全部轉 string，保留數字精度
        return {
            'time': str(self.time),
            'activity': str(self.activity),
            'symbol': str(self.symbol),
            'trade_symbol': str(self.trade_symbol),
            'quantity': str(self.quantity),
            'price': str(self.price),
            'commission': str(self.commission),
            'commission_asset': str(self.commission_asset),
            'commission_as_usdt': str(self.commission_as_usdt),
            'round_id': self.round_id,
            'order_id': str(self.order_id),
            'trade_id': str(self.trade_id),
            'closed_trade_ids': self.closed_trade_ids
        }

    def to_str(self, withdate=True):
        s = (
            f"TX {self.activity} {self.quantity.normalize():f} {self.symbol} "
            f"@{self.price.normalize():f} {self.trade_symbol[len(self.symbol):]} FEE {self.commission_as_usdt.normalize():f} USDT "
        )

        if withdate:
            s += f"on {datetime.utcfromtimestamp(self.time/1000).strftime('%Y-%m-%d %H:%M:%S')} UTC"

        return s

    def __str__(self):
        return self.to_str(withdate=True)

    def __repr__(self):
        return self.to_str(withdate=True)
