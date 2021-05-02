class Position:
    """倉位"""

    def __init__(self, asset_symbol, on_update, dict):
        """
        asset_symbol: 貨幣代號
        transaction: 交易紀錄
        """
        self.asset_symbol = asset_symbol

        if dict is None:
            self.quantity = 0.0
            self.cost = 0.0
            self.realized_gain = 0.0
            return

        self.quantity = float(dict['quantity'])
        self.cost = float(dict['cost'])
        self.realized_gain = float(dict['realizedGain'])

    def update(self, transaction):
        pass

    def cal_realized_gain(self):
        """推算已實現損益"""

        pass

    def __str__(self):
        if self.quantity > 0:
            return f"{self.asset_symbol}: {self.quantity} @{self.cost}, realized = {self.realized_gain}"

        return f"{self.asset_symbol}: no position, realized = {self.realized_gain}"

class Transaction:
    def __init__(self, time, activity, symbol, quantity, price):
        self.time = time
        self.activity = activity
        self.symbol = symbol
        self.quantity = quantity
        self.price = price

        self.new_average_price = None
        self.realized_gain = None
