import csv
import json
import os

now_dir = os.path.dirname(__file__)

def init_h_block() -> None:
    dir = ["W", "WA", "A", "AS", "S", "SD", "D", "DW"]
    act = ["jump", "sneak", "offset", "place"]
    for i in dir:
        act.append(f"walk_{i}")
        act.append(f"sprint_{i}")
    for i in ["U", "UF", "F", "DF", "D"]:
        act.append(f"break_{i}")

    with open(os.path.join(now_dir, "MCdata/blocks.json"), "r", encoding="utf-8") as f:
        fin = json.load(f)
    block = [{
        "minStateId": -1,
        "maxStateId": -1,
        "name": "unknown"
    }]
    for i in fin:
        block.append({
            "minStateId": i["minStateId"],
            "maxStateId": i["maxStateId"],
            "name": i["name"]
        })
    
    with open(os.path.join(now_dir, "heuristic_block.csv"), "w", newline="") as f:
        fout = csv.writer(f)
        fout.writerow(["action", "block_minStateId", "block_maxStateId", "block_name", "score"])
        for i in act:
            for j in block:
                fout.writerow([i, j["minStateId"], j["maxStateId"], j["name"], 0])

def init_h_entity() -> None:
    with open(os.path.join(now_dir, "MCdata/entities.json"), "r", encoding="utf-8") as f:
        fin = json.load(f)
    entity = []
    for i in fin:
        entity.append({
            "id": i["id"],
            "name": i["name"]
        })
    
    with open(os.path.join(now_dir, "heuristic_entity.csv"), "w", newline="") as f:
        fout = csv.writer(f)
        fout.writerow(["entity_id", "entity_name", "killable", "score"])
        for i in entity:
            fout.writerow([i["id"], i["name"], 0, 0])

def init_rarity() -> None:
    with open(os.path.join(now_dir, "MCdata/items.json"), "r", encoding="utf-8") as f:
        fin = json.load(f)
    item = []
    for i in fin:
        item.append({
            "id": i["id"],
            "name": i["name"]
        })
    
    with open(os.path.join(now_dir, "item_rarity.csv"), "w", newline="") as f:
        fout = csv.writer(f)
        fout.writerow(["item_id", "item_name", "rarity"])
        for i in item:
            fout.writerow([i["id"], i["name"], 0])

if __name__ == "__main__":
    if not os.path.exists(os.path.join(now_dir, "heuristic_block.csv")):
        print("Initializing heuristic block data...")
        init_h_block()
        print("Heuristic block data initialized.")
    else:
        print("Heuristic block data already exists.")

    if not os.path.exists(os.path.join(now_dir, "heuristic_entity.csv")):
        print("Initializing heuristic entity data...")
        init_h_entity()
        print("Heuristic entity data initialized.")
    else:
        print("Heuristic entity data already exists.")

    if not os.path.exists(os.path.join(now_dir, "item_rarity.csv")):
        print("Initializing item rarity data...")
        init_rarity()
        print("Item rarity data initialized.")
    else:
        print("Item rarity data already exists.")