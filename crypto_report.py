import pygsheets
import position
import pandas as pd
from crypto import *
from config import *
from binance.enums import *
from decimal import Decimal

class CryptoReport:
    def __init__(self, config):
        self.config = config
        google_sheet_key = config.auth["GOOGLE_SHEET_KEY"]
        goolge_sheet_name= config.auth["GOOGLE_SHEET_NAME"]
        self.sheet = self.__gsheet(google_sheet_key, goolge_sheet_name)

    def __gsheet(self, google_sheet_key, google_sheet_name):
        gc = pygsheets.authorize(service_account_file='credentials.json')
        survey_url = f'https://docs.google.com/spreadsheets/d/{google_sheet_key}/'
        sh = gc.open_by_url(survey_url)

        sheet = sh.worksheet_by_title(google_sheet_name)
        # scopes = ["https://spreadsheets.google.com/feeds"]
        # credentials = ServiceAccountCredentials.from_json_keyfile_name(
        #     "credentials.json", scopes)
        # client = gspread.authorize(credentials)
        # sheet = client.open_by_key(
        #     google_sheet_key).worksheet(google_sheet_name)

        #cells = sheet.get_as_df(start="D1")
        #print(cells)
        #cells.iloc[-1]['利潤'] = 10
        #sheet.set_dataframe(cells, 'D1')
        #print(cells.[-1][''])
        # cells[1].value = 5
        # sheet.update_cells(cells)

        return sheet

    def add_transaction(self, transaction):
        print(transaction)
        # 交易中幣種市價	幣種	幣幣對	買入價格	賣出價格	數量	手續費(USDT)	利潤
        if transaction.activity == SIDE_BUY:
            # 買入就Append一筆新的紀錄
            df = self.sheet.get_as_df(start="D1", numerize=False)
            df = df.append(pd.DataFrame([[transaction.price, transaction.symbol, transaction.trade_symbol, transaction.price, "", transaction.quantity, transaction.commission_as_usdt, ""]], columns=df.columns))
            self.sheet.set_dataframe(df, 'D1')
        elif transaction.activity == SIDE_SELL:
            # 賣出就修改原有的紀錄
            df = self.sheet.get_as_df(start="D1", numerize=False)
            row =df.loc[(df['交易中幣種市價'] != "") & (df['幣種'] == transaction.symbol) & (df['幣幣對'] == transaction.trade_symbol)].head(1)
            profit = Decimal(transaction.price) - Decimal(row['買入價格'].values[0]) - Decimal(row['手續費(USDT)'].values[0])
            df.loc[(df['交易中幣種市價'] != "") & (df['幣種'] == transaction.symbol) & (df['幣幣對'] == transaction.trade_symbol), ['賣出價格', '交易中幣種市價', '利潤']] = [transaction.price, "", profit]
            self.sheet.set_dataframe(df, 'D1')
        else:
            print(f"Unknown transaction activity {transaction.activity}")

    def update_market_price(self, watchingSymbol):
        crypto = Crypto(self.config)
        latest_price = crypto.get_latest_price(watchingSymbol.symbol)
        df = self.sheet.get_as_df(start="D1", numerize=False)
        df.loc[(df['賣出價格'] == "") & (df['幣種'] == watchingSymbol.base_asset) & (df['幣幣對'] == watchingSymbol.symbol), ['交易中幣種市價']] = [latest_price['price']]
        self.sheet.set_dataframe(df, 'D1')

config = Config()
report = CryptoReport(config)
transaction = position.Transaction(1620011227094, SIDE_BUY, "DOGE", "DOGEUSDT", Decimal('36.60000000'), Decimal('0.38157000'), Decimal('0.00001676'), 'BNB', Decimal('0.05'), "4", [])
report.add_transaction(transaction)
report.update_market_price(WatchingSymbol("DOGEUSDT", "DOGE", None))
# transaction = position.Transaction(1620011227094, SIDE_SELL, "DOGE", "DOGEUSDT", Decimal('36.60000000'), Decimal('0.39157000'), Decimal('0.00001676'), 'BNB', Decimal('0.05'), "6", [])
# report.add_transaction(transaction)