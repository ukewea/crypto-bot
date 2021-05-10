import logging.config
from . import bot_abc

_log = logging.getLogger(__name__)


class Bot:
    def __init__(self, config):
        _log.debug("init a Discord bot")

    def start_worker_thread(self, rx_q, tx_q):
        def worker():
            while True:
                try:
                    item = rx_q.get()
                    if item.task_type == queue_task.TaskType.STOP_WORKER_THREAD:
                        break
                    elif item.task_type == queue_task.TaskType.NOTIFY_TX:
                        _log.debug("Sending transactions notification")
                        self.notify_transactions(item.payload)
                    elif item.task_type == queue_task.TaskType.NOTIFY_CASH_BALANCE:
                        self.send_message(f"Cash balance: {item.payload}")
                    else:
                        _log.error(f"Unknown TaskType {item.task_type}")
                except:
                    _log.exception("Error while processing queue")
                finally:
                    rx_q.task_done()

        # turn-on the worker thread
        threading.Thread(target=worker, daemon=True).start()

    def send_messages(self, texts):
        text = ''
        for t in texts:
            text = text + t + "\n"

        self.send_message(text.rstrip())

    def notify_transactions(self, transactions):
        text = ''
        for t in transactions:
            text = text + t.to_str(withdate=False) + "\n"

        self.send_message(text.rstrip())

    def send_message(self, text):
        # self.bot.sendMessage(chat_id=self.channel_id, text=text)
        raise Exception
