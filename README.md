# crypto-bot
Trading cryptocurrencies on Binance 24 hours a day, 7 days a week.

## Features
- Put your money Binance on the line
- 可用 Python 實作自訂的買入/賣出策略 (基於加密貨幣過去的 K 線紀錄)
- 交易報表 on Google Sheet
- Transaction notification
- 可放在 Docker container 內執行 (搭配[特定 image](https://hub.docker.com/r/wuuker/python-bot-env))
- 交易歷史、倉位紀錄保存在本地 json 文字檔，方便 version control
- Works on Windows/Linux

## Want to take a deep look into the source code?
- `get_data.py`: entry point of the bot, where the big endless while loop is here
- `crypto_report.py`: business logic related to updating transaction history to Google Sheet
- `send_order.py`: 與幣安 API 的串接
- `config.py` configuration files loader
- `file_based_asset_positions.py`: crypto position management module
- `notification_platforms/` folders where push notification implementations are

## How to get started?

### Setup environment
- Python3 is required
- Run `pip install -r requirements.txt` or equivalent command to install dependencies.

### Prepare service API key/token
- [Binance API](https://www.binance.com/en/support/faq/360002502072)
- Telegram/Discord bot API key (if you want transaction notification features enabled)
- [Google Sheets API](https://handsondataviz.org/google-sheets-api-key.html)

### Configuration
- 將 `user-config/` 內的除了 `credentials.example.json` 以外的檔案原地複製一份，並拿掉檔名的 `example.` 文字 (e.g., 複製一份 `user-config/analyzer.example.json` 到 `user-config/analyzer.json`)
- Change parameters in these files
  * `analyzer.json` - Set to you the buy/sell strategies you want to use.
  * `auth.json` - Put you Binance API key, Google Sheet API key and name of the sheet to keep your Transaction history here
  * `bot.json` - Optional, if you want transaction push notification
  * `credentials.json` - This file will be replaced by the file you download while applying Google Sheet API
  * `logging.ini` - parameters related to program behavior tracking, useful when debugging
  * `position-manage.json` - Set your cash currency, inclusion/exclusion lists of cryptos you want to trade.


## Entry point?
Run `python get_data.py`

## How to quit the app?
**NEVER** use `kill -9` command or other means to force termintate the program, otherwise position management and record on Google Sheet may become corrupt.

Use one of the following methods instead:
- put a file named `stoppp` in the root folder of the app (works on both Windows and Linux)
- `Ctrl+C`, since `SIGINT` signal is handled (only tested on Linux)
- a plain `kill` command, since `SIGTERM` is handled (only tested on Linux)

If you run the bot inside a Docker container, stop the container with `-t` option to allow the bot to update transactions to Google Sheet
- e.g., to tell Docker wait up to 60 seconds before force stop the container, use `docker stop -t 60 __CONTAINER_NAME__`
