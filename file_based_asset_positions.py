import os, sys
from position import *
import json

class AssetPositions:
    """帳號下資產的倉位"""

    BASE_DIR = "asset_positions"

    def __init__(self, watching_symbols, cash_asset):
        os.makedirs(AssetPositions.BASE_DIR, mode=0o755, exist_ok=True)
        self.positions = dict()

        self.__read_file(cash_asset)
        for symbol in watching_symbols:
            self.__read_file(symbol.base_asset)

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
