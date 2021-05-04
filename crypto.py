from binance.client import Client
from binance.enums import *
from decimal import Decimal

class Crypto:
    # 建構式
    def __init__(self, config):
        self.client = Client(
            config.auth["API_KEY"], config.auth["API_SECRET"], testnet=True)

    def get_exchange_info(self):
        exchange_info = self.client.get_exchange_info()
        return exchange_info

    def get_latest_price(self, trade_symbol):
        """取得指定交易對的最新報價"""
        symbol_ticker = self.client.get_symbol_ticker(trade_symbol)
        return symbol_ticker

    def get_tradable_symbols(self, quote_asset, exclude_assets):
        """找出以 quote_asset 報價，且目前可交易、可送市價單、非槓桿型的交易對"""

        exchange_info = self.get_exchange_info()
        # print(type(exchange_info))
        # with open('exchange_info.json', 'w') as outfile:
        #     json.dump(exchange_info, outfile, indent=4)

        trade_with_quote_asset = [item for item in exchange_info['symbols']
                                  if item['quoteAsset'].upper() == quote_asset]

        return [WatchingSymbol(symbol['symbol'], symbol['baseAsset'], symbol)
                for symbol in trade_with_quote_asset
                if symbol['status'].upper() == "TRADING"
                and not symbol['baseAsset'] in exclude_assets
                and "MARKET" in symbol['orderTypes']
                and not "LEVERAGED" in symbol['permissions']]

    def get_klines(self, symbol, klines_limit=100, interval=Client.KLINE_INTERVAL_15MINUTE):
        """
        Get klines data
        :param symbol: symbol e.g., BTCUSDT、DOGEUSDT
        :param klines_limit: K線的數量限制
        :param interval: 幾分的K線資料
        :return: klines data
        """

        klines = self.client.get_klines(
            symbol=symbol,
            interval=Client.KLINE_INTERVAL_15MINUTE,
            limit=klines_limit)
        if len(klines) < klines_limit:
            raise Exception(
                f"No enough data for {symbol} (only {len(klines)})")

        return [Kline(data) for data in klines]

    # def get_closed_prices(self, symbol, klines_limit = 100, interval=Client.KLINE_INTERVAL_15MINUTE):
    #     klines = self.get_klines(symbol, klines_limit, interval)
    #     return [kline.close for kline in klines]

    def get_account(self):
        account = self.client.get_account()
        return account

    def get_historical_klines(self, symbol, KLINE_INTERVAL, fromdate, todate):
        return self.client.get_historical_klines(symbol, KLINE_INTERVAL, fromdate, todate)
        print(self.client.response)

    def get_equities_balance(self, watching_symbols, cash_asset):
        """取得所有資產的餘額，交易用的現金 (aka. cash_asset) 餘額也會包含在內"""

        account = self.get_account()
        balances = account['balances']
        ret = dict()

        asset_balance = [x for x in balances if x['asset'] == cash_asset]
        if len(asset_balance) < 1:
            raise Exception(f"Cannot get {cash_asset} balance in your account")

        balance = AssetBalance(asset_balance[0])
        ret[cash_asset] = balance

        for watching_symbol in watching_symbols:
            base_asset = watching_symbol.base_asset
            asset_balance = [x for x in balances if x['asset'] == base_asset]
            if len(asset_balance) < 1:
                print(f"Cannot get {base_asset} balance in your account")
                continue

            balance = AssetBalance(asset_balance[0])
            ret[base_asset] = balance

        return ret

    def order_qty(self, side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
        """送出指定交易數量的訂單"""
        try:
            print("sending order")
            order = self.client.create_test_order(
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity)

            print(order)
            return (True, order)
        except Exception as e:
            print("an exception occured - {}".format(e))
            return (False, None)


    def order_quote_qty(self, side, quoteOrderQty, symbol, order_type=ORDER_TYPE_MARKET):
        """送出指定成交額的訂單"""
        try:
            print("sending order")
            order = self.client.create_test_order(
                symbol=symbol,
                side=side,
                type=order_type,
                quoteOrderQty=quoteOrderQty)

            print(order)
            return (True, order)
        except Exception as e:
            print("an exception occured - {}".format(e))
            return (False, None)


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
        self.open = float(dict[1])
        self.high = float(dict[2])
        self.low = float(dict[3])
        self.close = float(dict[4])
        self.volume = float(dict[5])
        self.close_time = int(dict[6])
        self.quote_asset_volume = float(dict[7])
        self.number_of_trades = int(dict[8])
        self.taker_buy_base_asset_volume = float(dict[9])
        self.taker_buy_quote_asset_volume = float(dict[10])


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


class WatchingSymbol:
    """監視中的交易對"""

    def __init__(self, symbol, base_asset, info):
        """symbol: 交易對名稱，base_asset: 資產名稱"""

        self.symbol = symbol
        self.base_asset = base_asset
        self.info = info

    def __str__(self):
        return f"{self.symbol} ({self.base_asset})"
