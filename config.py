import json

class Config:
    # 建構式
    def __init__(self):
        json_file = open("auth.json", "r+")
        self.auth = json.load(json_file)
        json_file.close()