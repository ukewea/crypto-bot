import json
import logging.config
import os

from position import *

_log = logging.getLogger(__name__)


class AssetPositions:
    """基於檔案儲存的、帳號下的資產倉位"""

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

    def cal_total_open_position_count(self):
        total_open_count = int(0)

        for k, v in self.positions.items():
            if v.open_quantity > 0:
                total_open_count += 1

        return total_open_count

    def cal_total_open_cost(self):
        total_open_cost = Decimal(0)

        for k, v in self.positions.items():
            if v.open_cost > 0:
                total_open_cost += v.open_cost

        return total_open_cost

    def __read_file(self, asset_symbol):
        record_path = AssetPositions.__get_record_path(asset_symbol)

        if not os.path.exists(record_path):
            self.positions[asset_symbol] = Position(
                asset_symbol, self.__on_position_update, None)
            _log.debug(
                f"{asset_symbol} position file does not exist, skip loading ({record_path})")
            return

        with open(record_path, "r+") as json_file:
            _log.debug(
                f"{asset_symbol} position file exists, loading ({record_path})")
            self.positions[asset_symbol] = Position(
                asset_symbol, self.__on_position_update, json.load(json_file))

    def __on_position_update(self, asset_symbol):
        record_path = AssetPositions.__get_record_path(asset_symbol)
        _log.debug(f"__on_position_update, writing to {record_path}")

        with open(record_path, 'w') as outfile:
            position = self.positions[asset_symbol]
            json.dump(position.to_dict(), outfile)

    def __get_record_path(asset_symbol):
        return os.sep.join([AssetPositions.BASE_DIR, f"{asset_symbol}.json"])
