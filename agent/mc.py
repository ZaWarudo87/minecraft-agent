import json
import numpy as np
import os

import nbtlib
from sortedcontainers import SortedDict

from . import move

now_dir = os.path.dirname(__file__)
with open(os.path.join(now_dir, "login/info.json"), "r", encoding="utf-8") as f:
    info = json.load(f)
try:
    with open(os.path.join(now_dir, f"../world_cache/{info["server"]}_{info["port"]}_block.json"), "r", encoding="utf-8") as f:
        block = json.load(f)
except:
    block = {} # block[x][y][z] = block_state_id
block_name_dict = SortedDict()
hotkey = [""] * 9

def extra(ipt: list) -> str:
    ans = ""
    for i in ipt:
        if "text" in i:
            ans += i["text"]
        if "extra" in i:
            ans += extra(i["extra"])
    return ans

def decode(ipt: str) -> tuple[str, str, dict]: #NBT, target, payload
    ipt = json.loads(ipt)
    if "translate" in ipt and "with" in ipt:
        tp = ipt["translate"]
        nm = ipt["with"][0]["insertion"]
        if tp == "chat.type.text":
            pl = {"text": ipt["with"][1]}
        else:
            pl = to_dict(nbtlib.parse_nbt(extra(ipt["with"][1:])).unpack())
        return tp, nm, pl
    else:
        return "error", "none", "Can't decode this message."
    
def to_dict(ipt: nbtlib.Compound) -> dict:
    if isinstance(ipt, dict):
        return {k: to_dict(v) for k, v in ipt.items()}
    elif isinstance(ipt, list):
        return [to_dict(i) for i in ipt]
    elif isinstance(ipt, np.ndarray):
        return ipt.tolist()
    else:
        return ipt
    
def get_block(x: int, y: int, z: int) -> int:
    try:
        return block[str(x)][str(y)][str(z)]
    except KeyError:
        return -1
    
def set_block(x: int, y: int, z: int, id: int) -> None:
    global block
    x, y, z = str(x), str(y), str(z)
    if x not in block:
        block[x] = {}
    if y not in block[x]:
        block[x][y] = {}
    block[x][y][z] = id

def save_block() -> None:
    with open(os.path.join(now_dir, f"../world_cache/{info['server']}_{info['port']}_block.json"), "w", encoding="utf-8") as f:
        json.dump(block, f)

def load_block_name(data: dict) -> None:
    global block_name_dict
    for k, v in data.items():
        block_name_dict[k] = {
            "block_maxStateId": v["block_maxStateId"],
            "block_name": v["block_name"]
        }

def get_block_name(id: int) -> str:
    idx = block_name_dict.bisect_left(id)
    if idx < len(block_name_dict):
        loc = block_name_dict.iloc[idx]
        if block_name_dict[loc]["block_maxStateId"] >= id:
            return block_name_dict[loc]["block_name"]
        else:
            return "error"
    else:
        return "error"
    
def get_item(inv: list, bef: dict) -> dict:
    item = bef.copy()
    for k in item:
        item[k] = -item[k]
    for i in inv:
        i["id"] = i["id"][len("minecraft:"):]
        if 0 <= i["Slot"] <= 8 and hotkey[i["Slot"]] != i["id"]:
            move.tool_num[i["id"]] = i["Slot"] + 1
            hotkey[i["Slot"]] = i["id"]
        if i["id"] in item:
            item[i["id"]] += i["Count"]
        else:
            item[i["id"]] = i["Count"]
    item = {k: v for k, v in item.items() if v != 0}
    return item
    
if __name__ == "__main__":
    if input("Do you want to test decode? (y/n): ").strip().lower() == 'y':
        print(decode(input("Enter SNBT string: ")))

    if input("Do you want to test block? (y/n): ").strip().lower() == 'y':
        print(block)