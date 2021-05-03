import json
from binance.enums import *
from decimal import Decimal

class Position:
    """倉位"""

    def __init__(self, asset_symbol, on_update, dict):
        """
        asset_symbol: 貨幣代號
        transaction: 交易紀錄
        """
        self.asset_symbol = asset_symbol
        self.__on_update_transaction = on_update
        self.transactions = list()

        if dict is None:
            self.quantity = Decimal(0.0)
            self.cost = Decimal(0.0)
            self.realized_gain = Decimal(0.0)
            return

        # print(dict)
        self.quantity = Decimal(dict['quantity'])
        self.cost = Decimal(dict['cost'])
        self.realized_gain = Decimal(dict['realized_gain'])

        for transact in dict['transactions']:
            # print(transact)
            self.transactions.append(Transaction(int(transact['time']),
                transact['activity'], transact['symbol'], transact['trade_symbol'],
                Decimal(transact['quantity']), Decimal(transact['price']),
                Decimal(transact['comission']), transact['commission_asset']))

    def to_dict(self):
        return {
            'quantity': str(self.quantity),
            'cost': str(self.cost),
            'realized_gain': str(self.realized_gain),
            'transactions': [t.to_dict() for t in self.transactions],
        }

    def add_transaction(self, transaction):
        if transaction.activity == SIDE_BUY:
            self.quantity += transaction.quantity
            self.cost += transaction.quantity * transaction.price
        elif transaction.activity == SIDE_SELL:
            current_avg_price = self.cost / self.quantity
            print(f"current_avg_price = {current_avg_price}")
            purchase_cost = transaction.quantity * current_avg_price
            print(f"purchase_cost = {purchase_cost}")
            realized_gain = (transaction.price - current_avg_price) * transaction.quantity
            print(f"realized_gain = {realized_gain}")

            self.quantity -= transaction.quantity
            self.cost -= purchase_cost
            self.realized_gain += realized_gain
        else:
            raise Exception("Unknown transaction")

        self.transactions.append(transaction)
        self.__on_update_transaction(self.asset_symbol)

    def __str__(self):
        if self.quantity > 0:
            return f"{str(self.asset_symbol)}: {str(self.quantity)} @{str(self.cost)}"
            f", realized = {str(self.realized_gain)}"

        return f"{str(self.asset_symbol)}: no position, realized = {str(self.realized_gain)}"

class Transaction:
    def __init__(self, time, activity, symbol, trade_symbol, quantity, price, comission, commission_asset):
        self.time = time
        self.activity = activity
        self.symbol = symbol
        self.trade_symbol = trade_symbol
        self.quantity = quantity
        self.price = price
        self.comission = comission
        self.commission_asset = commission_asset

    def to_dict(self):
        return {
            'time': str(self.time),
            'activity': str(self.activity),
            'symbol': str(self.symbol),
            'trade_symbol': str(self.trade_symbol),
            'quantity': str(self.quantity),
            'price': str(self.price),
            'comission': str(self.comission),
            'commission_asset': str(self.commission_asset),
        }
