from enum import Enum


class TaskType(Enum):
    STOP_WORKER_THREAD = 0
    NOTIFY_TX = 1
    NOTIFY_CASH_BALANCE = 2


class QueueTask:
    def __init__(self, task_type, payload):
        self.task_type = task_type
        self.payload = payload
