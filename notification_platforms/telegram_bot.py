import telegram
import logging.config


_log = logging.getLogger(__name__)


class Bot:
    def __init__(self, config):
        _log.debug("init a Telegram bot")
        self.bot = telegram.Bot(token=config['telegram_bot']['bot_token'])
        self.channel_id = config['telegram_bot']['channel_id']

    def send_messages(self, texts):
        text = ''
        for t in texts:
            text = text + t + "\n\n"

        self.send_message(text.rstrip())

    def notify_transactions(self, transactions):
        text = ''
        for t in transactions:
            text = text + t.to_str(withdate=False) + "\n\n"

        self.send_message(text.rstrip())

    def send_message(self, text):
        self.bot.sendMessage(chat_id=self.channel_id, text=text)
