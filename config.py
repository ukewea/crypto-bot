import json

class Config:
    # 建構式
    def __init__(self):
        with open("auth.json", "r+") as json_file:
            self.auth = json.load(json_file)

        with open("analyzer-parameters.json", "r+") as json_file:
            self.analyzer = json.load(json_file)

        # 要排除的貨幣
        with open("exclude-coins.json", "r+") as json_file:
            self.exclude_coins = json.load(json_file)
