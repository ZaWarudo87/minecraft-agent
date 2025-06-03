"""
TODO
- 如果能透過種子碼拿到整張地圖的話，就去做 load_world(seed)（然後就可以無視 get_block(x, y, z) 的TODO）
- 否則想辦法完成 get_block(x, y, z) 的TODO
- 要用PyCraft的話就搭配 handle.py，要用MineCraft指令的話用 handle.cmd(line)，例如 handle.cmd('gamemode survival')，並且要去編輯 handle.py 接住指令回傳結果
"""

import json
import math
import numpy as np
import os
import threading
import time

import nbtlib
from sortedcontainers import SortedDict
from minecraft.networking.types import Position

from . import global_var as gv

now_dir = os.path.dirname(__file__)
block = {} # block[x][y][z] = block_state_id
block_name_dict = SortedDict()
hotkey = [""] * 9
loading = False
fname = f"../world_cache/block.json"

def load_world() -> None:
    global block, loading, fname
    loading = True
    fname = f"../world_cache/{gv.info['server']}_{gv.info['port']}_block_{int(gv.f3[gv.player_list[gv.info['agent_name']]]['x'] // 512)}_{int(gv.f3[gv.player_list[gv.info['agent_name']]]['z'] // 512)}.json"
    print(f"Loading world from {fname}...")
    try:
        with open(os.path.join(now_dir, fname), "r", encoding="utf-8") as f:
            block = json.load(f)
    except Exception as e:
        print(f"Error loading world: {e}")
        block = {}
        time.sleep(60)
    loading = False

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
        if "insertion" in ipt["with"][0]:
            nm = ipt["with"][0]["insertion"]
        else:
            nm = "none"
        if tp == "chat.type.text":
            pl = {"text": ipt["with"][1]}
        else:
            try:
                pl = to_dict(nbtlib.parse_nbt(extra(ipt["with"][1:])).unpack())
            except:
                pl = "Can't decode this message."
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
    
def get_block(x: float, y: float, z: float) -> int:
    x, y, z = int(math.floor(x)), int(round(y)), int(math.floor(z))
    try:
        return block[str(x)][str(y)][str(z)]
    except KeyError:
        if not loading:
            threading.Thread(target=load_world).start()
        return -1
    
def get_gaze_block(x: float, y: float, z: float, yaw: float, pitch: float, look: list = [False, False], look_coor: list = [0, 0, 0], mx: float = 4, s: float = 0.1) -> int:
    ya = math.radians(yaw)
    pi = math.radians(pitch)
    vx = -math.sin(ya) * math.cos(pi)
    vy = -math.sin(pi)
    vz =  math.cos(ya) * math.cos(pi)
    nx, ny, nz = x, y, z

    for i in range(int(mx / s)):
        nx += vx * s
        ny += vy * s
        nz += vz * s
        bx, by, bz = int(math.floor(nx)), int(round(ny)), int(math.floor(nz))
        #print(f"gazing at ({bx}, {by}, {bz})")
        # TODO: check whether agent and master is look at each other
        bid = get_block(bx, by, bz)
        if not is_empty_block(bid):
            look_coor = [bx, by, bz]
            return bid
    return bid
    
def set_block(x: int, y: int, z: int, id: int) -> None:
    #print(f"set block ({x}, {y}, {z}) to {get_block_name(id)}")
    global block
    x, y, z = str(x), str(y), str(z)
    if x not in block:
        block[x] = {}
    if y not in block[x]:
        block[x][y] = {}
    block[x][y][z] = id

def save_block() -> None:
    with open(os.path.join(now_dir, fname), "w", encoding="utf-8") as f:
        json.dump(block, f)

def load_block_name(data: dict) -> None:
    global block_name_dict
    for k, v in data.items():
        block_name_dict[k] = {
            "block_maxStateId": v["block_maxStateId"],
            "block_name": v["block_name"]
        }

def get_block_min(id: int) -> int:
    idx = block_name_dict.bisect_right(id)
    if idx < len(block_name_dict):
        loc = block_name_dict.iloc[idx - 1]
        if block_name_dict[loc]["block_maxStateId"] >= id:
            return loc
        else:
            return -1
        
def get_block_name(id: int) -> str:
    return block_name_dict[get_block_min(id)]["block_name"]
    
def get_item(inv: list, bef: dict) -> dict:
    item = bef.copy()
    for k in item:
        item[k] = -item[k]
    for i in inv:
        i["id"] = i["id"][len("minecraft:"):]
        if 0 <= i["Slot"] <= 8 and hotkey[i["Slot"]] != i["id"]:
            gv.tool_num[i["id"]] = i["Slot"] + 1
            hotkey[i["Slot"]] = i["id"]
        if i["id"] in item:
            item[i["id"]] += i["Count"]
        else:
            item[i["id"]] = i["Count"]
    item = {k: v for k, v in item.items() if v != 0}
    return item
    
def is_empty_block(*args) -> bool:
    if len(args) == 1:
        bid = args[0]
    elif len(args) == 3:
        bid = get_block(*args)
    return bid <= 0 or 34 <= bid <= 49 or 50 <= bid <= 65

if __name__ == "__main__":
    if input("Do you want to test decode? (y/n): ").strip().lower() == 'y':
        print(decode(input("Enter SNBT string: ")))

    if input("Do you want to test block? (y/n): ").strip().lower() == 'y':
        print(block)