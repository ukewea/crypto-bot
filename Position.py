def Position:
"""倉位"""

    def init(self, asset_symbol, transactions):
    """
    asset_symbol: 貨幣代號
    transaction: 交易紀錄
    """
        self.asset_symbol = asset_symbol

    def cal_realized_gain(self):
    """推算已實現損益"""

        pass

def Transaction:
    def __init__(self, time, activity, symbol, quantity, price):
        self.time = time
        self.activity = activity
        self.symbol = symbol
        self.quantity = quantity
        self.price = price

        self.new_average_price = None
        self.realized_gain = None
