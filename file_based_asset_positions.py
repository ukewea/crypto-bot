import os, sys
from position import *
import json

class AssetPositions:
    """基於檔案儲存的、帳號下的資產倉位"""
    """
    已實現總利潤
    已實現報酬率(%)
    未實現總利潤
    未實現報酬率(%)
    交易勝利次數
    交易失敗次數
    交易勝率
    交易平均損益
    交易平均時間
    """
    BASE_DIR = "asset_positions"

    def __init__(self, watching_symbols, cash_asset):
        os.makedirs(AssetPositions.BASE_DIR, mode=0o755, exist_ok=True)
        self.positions = dict()

        self.__read_file(cash_asset)
        for symbol in watching_symbols:
            self.__read_file(symbol.base_asset)

    def get_total_commision_as_usdt(self):
        """取得總手續費 (USDT)"""
        sum = Decimal(0.0)
        for pos in self.positions.values():
            sum += pos.total_commission_as_usdt

        return sum

    def get_transactions_count(self):
        """取得交易完成總數"""
        sum = int(0)
        for pos in self.positions.values():
            sum += pos.get_transactions_count()

        return sum

    def __read_file(self, asset_symbol):
        record_path = AssetPositions.__get_record_path(asset_symbol)

        if not os.path.exists(record_path):
            self.positions[asset_symbol] = Position(asset_symbol, self.__on_position_update, None)
            return

        with open(record_path, "r+") as json_file:
            self.positions[asset_symbol] = Position(asset_symbol, self.__on_position_update, json.load(json_file))

    def __on_position_update(self, asset_symbol):
        record_path = AssetPositions.__get_record_path(asset_symbol)

        with open(record_path, 'w') as outfile:
            position = self.positions[asset_symbol]
            json.dump(position.to_dict(), outfile)

    def __get_record_path(asset_symbol):
        return os.sep.join([AssetPositions.BASE_DIR, f"{asset_symbol}.json"])
