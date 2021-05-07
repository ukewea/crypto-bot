import logging.config


_log = logging.getLogger(__name__)


class Bot:
    def __init__(self, config):
        _log.debug("init a Discord bot")
