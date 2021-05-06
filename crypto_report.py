import pygsheets
import position
import pandas as pd
from crypto import *
from config import *
from binance.enums import *
from decimal import Decimal
import logging.config
from datetime import datetime

log = logging.getLogger(__name__)


class CryptoReport:
    def __init__(self, config):
        self.config = config
        google_sheet_key = config.auth["GOOGLE_SHEET_KEY"]
        goolge_sheet_name= config.auth["GOOGLE_SHEET_NAME"]
        self.sheet = self.__gsheet(google_sheet_key, goolge_sheet_name)

    def __gsheet(self, google_sheet_key, google_sheet_name):
        gc = pygsheets.authorize(service_account_file=os.path.join(self.config.config_dir, 'credentials.json'))
        survey_url = f'https://docs.google.com/spreadsheets/d/{google_sheet_key}/'
        sh = gc.open_by_url(survey_url)

        sheet = sh.worksheet_by_title(google_sheet_name)
        return sheet

    def add_transaction(self, transactions):
        if len(transactions) <= 0:
            return

        trade_average_price = Decimal(0)
        trade_quantity = Decimal(0)
        trade_commission = Decimal(0)
        trade_total_cost = Decimal(0)
        for transaction in transactions:
            trade_total_cost += transaction.price * transaction.quantity
            trade_quantity += transaction.quantity
            trade_commission += transaction.commission_as_usdt

        trade_average_price = trade_total_cost / trade_quantity
        if trade_commission == 0:
            trade_commission = Decimal(0)

        # 未實現損益 交易中幣種市價	幣種 幣幣對	買入成本 買入價格 賣出價格 買入時間	賣出時間 數量 手續費(USDT) 利潤
        if transactions[0].activity == SIDE_BUY:
            # 買入就Append一筆新的紀錄
            df = self.sheet.get_as_df(start="D1", numerize=False)
            df = df.append(pd.DataFrame([["",
                                        "",
                                        transactions[0].symbol,
                                        transactions[0].trade_symbol,
                                        trade_average_price * trade_quantity,
                                        trade_average_price,
                                        "",
                                        trade_quantity,
                                        trade_commission,
                                        "",
                                        datetime.utcfromtimestamp(transactions[0].time/1000).strftime('%Y-%m-%d %H:%M:%S'),
                                        ""]], columns=df.columns))
            self.sheet.set_dataframe(df, 'D1')
        elif transactions[0].activity == SIDE_SELL:
            # 賣出就修改原有的紀錄
            try:
                df = self.sheet.get_as_df(start="D1", numerize=False)
                row =df.loc[(df['交易中幣種市價'] != "") & (df['幣種'] == transactions[0].symbol) & (df['幣幣對'] == transactions[0].trade_symbol)].head(1)
                fee = Decimal(row['手續費(USDT)'].values[0]) + trade_commission
                profit = Decimal((Decimal(trade_average_price) - Decimal(row['買入價格'].values[0])) * Decimal(trade_quantity) - fee)
                df.loc[(df['交易中幣種市價'] != "") & (df['幣種'] == transactions[0].symbol) & (df['幣幣對'] == transactions[0].trade_symbol), ['未實現損益', '賣出價格', '交易中幣種市價', '利潤', '手續費(USDT)', '賣出時間']] = ["", trade_average_price, "", profit, fee, datetime.utcfromtimestamp(transactions[0].time/1000).strftime('%Y-%m-%d %H:%M:%S')]
                self.sheet.set_dataframe(df, 'D1')
            except Exception as e:
                pass
        else:
            log.error(f"Unknown transaction activity {transactions[0].activity}")

    def update_market_price(self, market_price_dict):
        df = self.sheet.get_as_df(start="D1", numerize=False)
        for watching_symbol, latest_price in market_price_dict.items():
            try:
                row =df.loc[(df['賣出價格'] == "") & (df['幣種'] == watching_symbol.base_asset) & (df['幣幣對'] == watching_symbol.symbol)].head(1)
                profit = Decimal('{:f}'.format((Decimal(row['數量'].values[0]) * (Decimal(latest_price) - Decimal(row['買入價格'].values[0])) - Decimal(row['手續費(USDT)'].values[0]))))
                if profit == 0:
                    profit = Decimal(0)
                df.loc[(df['賣出價格'] == "") & (df['幣種'] == watching_symbol.base_asset) & (df['幣幣對'] == watching_symbol.symbol), ['未實現損益', '交易中幣種市價']] = [profit, latest_price]
            except Exception as e:
                print(e)
                pass

        log.debug(f'df:{df}')
        self.sheet.set_dataframe(df, 'D1')


if __name__ == '__main__':
    # do some test
    config = Config()
    report = CryptoReport(config)
    transaction = position.Transaction(1620011227094, SIDE_BUY, "DOGE", "DOGEUSDT", Decimal('36.60000000'), Decimal('0.38157000'), Decimal('0.00001676'), 'BNB', Decimal('0.05'), "1", "4", [])
    report.add_transaction(transaction)
    report.update_market_price(WatchingSymbol("DOGEUSDT", "DOGE", None))
    transaction = position.Transaction(1620011227094, SIDE_SELL, "DOGE", "DOGEUSDT", Decimal('36.60000000'), Decimal('0.39157000'), Decimal('0.00001676'), 'BNB', Decimal('0.05'), "10", "6", [])
    report.add_transaction(transaction)
