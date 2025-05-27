import csv
import json
import os

def init_h_block():
    dir = ["W", "WA", "A", "AS", "S", "SD", "D", "DW"]
    act = ["jump", "sneak"]
    for i in dir:
        act.append(f"walk_{i}")
        act.append(f"sprint_{i}")
    for i in range(3):
        act.append(f"break_{i}")

    with open("MCdata/blocks.json", "r", encoding="utf-8") as f:
        fin = json.load(f)
    block = []
    for i in fin:
        block.append({
            "minStateId": i["minStateId"],
            "maxStateId": i["maxStateId"],
            "name": i["name"]
        })
    
    with open("heuristic_block.csv", "w", newline="") as f:
        fout = csv.writer(f)
        fout.writerow(["action", "block_minStateId", "block_maxStateId", "block_name", "score"])
        for i in act:
            for j in block:
                fout.writerow([i, j["minStateId"], j["maxStateId"], j["name"], 0])

def init_h_entity():
    with open("MCdata/entities.json", "r", encoding="utf-8") as f:
        fin = json.load(f)
    entity = []
    for i in fin:
        entity.append({
            "id": i["id"],
            "name": i["name"]
        })
    
    with open("heuristic_entity.csv", "w", newline="") as f:
        fout = csv.writer(f)
        fout.writerow(["entity_id", "entity_name", "killable", "score"])
        for i in entity:
            fout.writerow([i["id"], i["name"], 0, 0])

def init_rarity():
    with open("MCdata/items.json", "r", encoding="utf-8") as f:
        fin = json.load(f)
    item = []
    for i in fin:
        item.append({
            "id": i["id"],
            "name": i["name"]
        })
    
    with open("item_rarity.csv", "w", newline="") as f:
        fout = csv.writer(f)
        fout.writerow(["item_id", "item_name", "rarity"])
        for i in item:
            fout.writerow([i["id"], i["name"], 0])

if __name__ == "__main__":
    if not os.path.exists("heuristic_block.csv"):
        print("Initializing heuristic block data...")
        init_h_block()
        print("Heuristic block data initialized.")
    else:
        print("Heuristic block data already exists.")

    if not os.path.exists("heuristic_entity.csv"):
        print("Initializing heuristic entity data...")
        init_h_entity()
        print("Heuristic entity data initialized.")
    else:
        print("Heuristic entity data already exists.")

    if not os.path.exists("item_rarity.csv"):
        print("Initializing item rarity data...")
        init_rarity()
        print("Item rarity data initialized.")
    else:
        print("Item rarity data already exists.")