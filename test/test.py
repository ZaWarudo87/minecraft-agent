import json

with open("../agent/other/chat_log.json", "r", encoding="utf-8") as f:
    chat_log = json.load(f)

for k, v in chat_log.items():
    print(k)