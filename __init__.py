import logging.config
import os

# initialize logger before importing any other modules
os.makedirs('logs', mode=0o755, exist_ok=True)
os.makedirs('logs-debug', mode=0o755, exist_ok=True)

logging.config.fileConfig(os.path.join('user-config', 'logging.ini'))
