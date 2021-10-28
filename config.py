import json
import logging.config
import os
from importlib import import_module

_log = logging.getLogger(__name__)


class Config:
    """使用者參數"""

    def __init__(self):
        """建構式"""

        self.config_dir = os.path.join(
            os.path.dirname(__file__), 'user-config')

        # API key/secret
        with open(os.path.join(self.config_dir, "auth.json"), "r+") as json_file:
            self.auth = json.load(json_file)

        # 技術分析參數
        with open(os.path.join(self.config_dir, "analyzer.json"), "r+") as json_file:
            self.analyzer = json.load(json_file)

        # 倉位管理
        with open(os.path.join(self.config_dir, "position-manage.json"), "r+") as json_file:
            self.position_manage = json.load(json_file)

        # bot 參數
        with open(os.path.join(self.config_dir, "bot.json"), "r+") as json_file:
            self.bot = json.load(json_file)

    def spawn_nofification_platform(self):
        """根據設定參數產生通知平台"""

        # 若未指定通知平台，就不產生
        if 'platform' not in self.bot or len(self.bot['platform']) < 1:
            _log.warning("No notification platform specified, skip spawning")
            return None

        try:
            module_path = f"notification_platforms.{self.bot['platform']}"
            module = import_module(module_path)
            notif_class = getattr(module, "Bot")
            notif = notif_class(self.bot)
            return notif
        except (ImportError, AttributeError) as e:
            raise ImportError(
                f"notification_platforms.{self.bot['platform']}.Bot")

    def spawn_analyzer(self):
        """根據設定參數產生 Analyzer"""

        if 'type' not in self.analyzer or len(self.analyzer['type']) < 1:
            raise RuntimeError('type is not specified in analyzer.json config file')

        module_path = f"analyzer.{self.analyzer['type']}_Analyzer"
        class_name = f"{self.analyzer['type']}_Analyzer"

        try:
            module = import_module(module_path)
            analyzer_class = getattr(module, class_name)
            analyzer = analyzer_class(self.analyzer)
            return analyzer
        except (ImportError, AttributeError) as e:
            raise ImportError(
                f"{module_path}.{class_name}")
