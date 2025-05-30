import json
import os

if __name__ == "__main__":
    now_dir = os.path.dirname(__file__)
    info_path = os.path.join(now_dir, "info.json")
    
    info = {
        "server": "localhost",
        "port": 25565,
        "access_token": "",
        "username": "",
        "id": "",
        "weird_username": "",
        "agent_name": "",
        "master_name": ""
    }

    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=4)
    
    print("Login information cleared successfully.")