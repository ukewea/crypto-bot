import abc
from typing import List

class Bot(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def send_messages(self, texts: List[str]):
        return NotImplemented

    @abc.abstractmethod
    def notify_transactions(self, transactions):
        return NotImplemented

    @abc.abstractmethod
    def send_message(self, text):
        return NotImplemented
