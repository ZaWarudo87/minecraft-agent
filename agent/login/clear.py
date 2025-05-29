import json
import os

if __name__ == "__main__":
    now_dir = os.path.dirname(__file__)
    info_path = os.path.join(now_dir, "info.json")
    
    with open(info_path, "r", encoding="utf-8") as f:
        info = json.load(f)
    info["access_token"] = ""
    info["username"] = ""
    info["id"] = ""
    info["weird_username"] = ""

    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=4)
    
    print("Login information cleared successfully.")