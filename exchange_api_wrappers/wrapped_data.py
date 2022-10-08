from decimal import Decimal

"""
包裝、處理過的、來自交易所的資料
"""

class AssetBalance:
    """資產餘額"""

    def __init__(self, dict):
        """
        dict: {
            'asset': 'BTC', // 資產名
            'free': '0.00000000', // 可動用
            'locked': '0.00000000' // 交易凍結
        }
        """
        self.asset = dict['asset']
        self.free = Decimal(dict['free'])
        self.locked = Decimal(dict['locked'])

    def __str__(self):
        return (
            f"{{asset: '{self.asset}', "
            f"free: '{self.free.normalize():f}', "
            f"locked: '{self.locked.normalize():f}'}}"
        )

    def __repr__(self):
        return (
            f"{{asset: '{self.asset}', "
            f"free: '{self.free.normalize():f}', "
            f"locked: '{self.locked.normalize():f}'}}"
        )


class WatchingSymbol:
    """監視中的交易對"""

    def __init__(self, symbol, base_asset, info):
        """
        symbol: 交易對名稱
        base_asset: 資產名稱
        info: 交易所 API 取得的相關交易限制或參數
        """

        self.symbol = symbol
        self.base_asset = base_asset
        self.info = info

    def __str__(self):
        return f"{{symbol: '{self.symbol}', base_asset: '{self.base_asset}'}}"

    def __repr__(self):
        return f"{{symbol: '{self.symbol}', base_asset: '{self.base_asset}'}}"


class Kline:
    """K 線"""

    def __init__(self, dict):
        """
        [
            1499040000000,      # Open time
            "0.01634790",       # Open
            "0.80000000",       # High
            "0.01575800",       # Low
            "0.01577100",       # Close
            "148976.11427815",  # Volume
            1499644799999,      # Close time
            "2434.19055334",    # Quote asset volume
            308,                # Number of trades
            "1756.87402397",    # Taker buy base asset volume
            "28.46694368",      # Taker buy quote asset volume
            "17928899.62484339" # Can be ignored
        ]
        """

        self.open_time = int(dict[0])
        self.open = Decimal(dict[1])
        self.high = Decimal(dict[2])
        self.low = Decimal(dict[3])
        self.close = Decimal(dict[4])
        self.volume = Decimal(dict[5])
        self.close_time = int(dict[6])
        self.quote_asset_volume = Decimal(dict[7])
        self.number_of_trades = int(dict[8])
        self.taker_buy_base_asset_volume = Decimal(dict[9])
        self.taker_buy_quote_asset_volume = Decimal(dict[10])
