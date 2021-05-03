import json
from importlib import import_module

class Config:
    """參數"""

    def __init__(self):
        """建構式"""

        with open("auth.json", "r+") as json_file:
            self.auth = json.load(json_file)

        with open("analyzer-parameters.json", "r+") as json_file:
            self.analyzer = json.load(json_file)

        # 要排除的貨幣
        with open("exclude-coins.json", "r+") as json_file:
            self.exclude_coins = json.load(json_file)

        with open("bot-parameters.json", "r+") as json_file:
            self.bot = json.load(json_file)

    def spawn_nofification_platform(self):
        """根據設定參數產生通知平台"""

        try:
            module_path = f"notification_platforms.{self.bot['platform']}"
            module = import_module(module_path)
            notif_class = getattr(module, "Bot")
            notif = notif_class(self.bot)
            return notif
        except (ImportError, AttributeError) as e:
            raise ImportError(f"notification_platforms.{self.bot['platform']}.Bot")
