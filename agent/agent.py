"""
TODO
- 完成 move.py, handle.py, mc.py 之後，取消 start(conn) 裡面的註解，並註解目前頂著的 time.sleep(1)
- 附近生物影響判斷那些完全還沒寫
"""

import csv
import json
import os
import random
import threading
import time

import pygetwindow as gw
from sortedcontainers import SortedKeyList, SortedDict
from minecraft.authentication import AuthenticationToken
from minecraft.networking.connection import Connection

from . import move
from . import keyboard_listener as kbl
from . import mc
from . import global_var as gv

now_dir = os.path.dirname(__file__)
heuristic_block = SortedDict()
heuristic_entity = {}
item_rarity = {}
last_op = [None, None] # block, movement

def read_file() -> None:
    global heuristic_block, heuristic_entity, item_rarity
    with open(os.path.join(now_dir, "../train/heuristic_block.csv"), "r", encoding="utf-8") as f:
        fin = csv.reader(f)
        for i in fin:
            if i[0] == "action":
                continue
            block_min = int(i[1])
            if block_min not in heuristic_block:
                heuristic_block[block_min] = {
                    "block_maxStateId": int(i[2]),
                    "block_name": i[3],
                    "action": {}
                }
            heuristic_block[block_min]["action"][i[0]] = {
                "score": float(i[4]),
                "num": int(i[5])
            }
        mc.load_block_name(heuristic_block)

    with open(os.path.join(now_dir, "../train/heuristic_entity.csv"), "r", encoding="utf-8") as f:
        fin = csv.reader(f)
        for i in fin:
            if i[0] == "entity_id":
                continue
            heuristic_entity[i[0]] = {
                "entity_name": i[1],
                "killable": bool(int(i[2])),
                "score": float(i[3]),
                "num": int(i[4])
            }

    with open(os.path.join(now_dir, "../train/item_rarity.csv"), "r", encoding="utf-8") as f:
        fin = csv.reader(f)
        for i in fin:
            if i[0] == "item_id":
                continue
            item_rarity[i[1]] = {
                "item_id": i[0],
                "rarity": int(i[2])
            }

    with open(os.path.join(now_dir, "../train/score.csv"), "rb") as f:
        f.seek(-2, 2)
        try:
            while f.read(1) != b"\n":
                f.seek(-2, 1)
        except:
            f.seek(-1, 1)
        gv.score_all = float(f.readline().decode())
    print("Heuristic data loaded successfully.")

def save_file(get_token: bool = True) -> None:
    global heuristic_block, heuristic_entity, item_rarity
    with open(os.path.join(now_dir, "../train/heuristic_block.csv"), "w", newline="", encoding="utf-8") as f:
        fout = csv.writer(f)
        fout.writerow(["action", "block_minStateId", "block_maxStateId", "block_name", "score", "num"])
        for block_min, block_data in heuristic_block.items():
            for action, data in block_data["action"].items():
                fout.writerow([action, block_min, block_data["block_maxStateId"], block_data["block_name"], data["score"], data["num"]])

    with open(os.path.join(now_dir, "../train/heuristic_entity.csv"), "w", newline="", encoding="utf-8") as f:
        fout = csv.writer(f)
        fout.writerow(["entity_id", "entity_name", "killable", "score", "num"])
        for entity_id, entity_data in heuristic_entity.items():
            fout.writerow([entity_id, entity_data["entity_name"], int(entity_data["killable"]), entity_data["score"], entity_data["num"]])

    with open(os.path.join(now_dir, "../train/score.csv"), "a", newline="", encoding="utf-8") as f:
        fout = csv.writer(f)
        for i in gv.score_temp:
            fout.writerow([i])
        gv.score_temp = []

    if get_token:
        with open(os.path.join(now_dir, "login/info.json"), "w", encoding="utf-8") as f:
            gv.info["access_token"] = gv.conn.auth_token.access_token
            json.dump(gv.info, f, indent=4)
    #mc.save_block()
    print("Heuristic data saved successfully.")

def save_file_thread() -> None:
    while True:
        time.sleep(300)
        save_file()
        print("Heuristic data auto-saved.")

def check_window() -> None:
    while True:
        bef = gv.ctrl_agent
        try:
            window = gw.getWindowsWithTitle("Minecraft 1.18")[0]
            gv.ctrl_agent = gv.connected and not window.isMinimized and window.isActive
        except IndexError:
            gv.ctrl_agent = False
        except Exception as e:
            gv.ctrl_agent = False
            print(f"Error checking Minecraft window: {e}")
            break

        if bef != gv.ctrl_agent:
            if gv.ctrl_agent:
                # if not kbl.game_test():
                #     move.back_to_game()
                print("Minecraft window is active, agent control enabled.")
            else:
                print("Minecraft window is not active, agent control disabled.")
        time.sleep(1)

def gain_item(item: dict) -> None:
    score = 0
    for k, v in item.items():
        score += 2 ** item_rarity[k]["rarity"] * v
    if score > 0:
        plus(score)

def plus(s: int) -> None:
    global heuristic_block
    print(f"Score change: {s}")
    if last_op[0] and last_op[1]:
        heuristic_block[mc.get_block_min(last_op[0])]["action"][last_op[1]]["num"] += 1
        heuristic_block[mc.get_block_min(last_op[0])]["action"][last_op[1]]["score"] += (s - heuristic_block[mc.get_block_min(last_op[0])]["action"][last_op[1]]["score"]) * (1 / heuristic_block[mc.get_block_min(last_op[0])]["action"][last_op[1]]["num"])
        idx = mc.get_block_min(gv.f3[gv.player_list[gv.info["agent_name"]]]["block"])
        heuristic_block[idx]["action"]["offset"]["num"] += 1
        heuristic_block[idx]["action"]["offset"]["score"] += (s - heuristic_block[idx]["action"]["offset"]["score"]) * (1 / heuristic_block[idx]["action"]["offset"]["num"])
        gv.score_all += s

def dfs(x: float, y: float, z: float, sim: list = gv.movement, dep: int = 2) -> tuple[list, float]:
    if dep <= 0:
        return sim, heuristic_block[mc.get_block_min(mc.get_block(x, y, z))]["action"]["offset"]["score"]
    
    ans = []
    score = float("-inf")
    for i in sim:
        nx, ny, nz, sim_block = move.move_sim(x, y, z, i)
        if sim_block == -2:
            continue
        choice = heuristic_block[mc.get_block_min(sim_block)]["action"]
        for k, v in choice.items():
            if k != "offset":
                _, aft = dfs(nx, ny, nz, sim, dep - 1)
                nows = v["score"] + aft
                if nows > score:
                    score = nows
                    ans = [k]
                elif nows == score:
                    ans.append(k)
    return ans, score

def start() -> None:
    global last_op
    read_file()
    from .handle import handle, get_dist
    handle()
    threading.Thread(target=save_file_thread, daemon=True).start()
    print("**Packet catcher started, waiting for starting Minecraft...**")
    while True:
        window = gw.getWindowsWithTitle("Minecraft 1.18")
        if window and gv.connected:
            threading.Thread(target=kbl.kb_listen, daemon=True).start()
            threading.Thread(target=check_window, daemon=True).start()
            window[0].restore()
            window[0].activate()
            break
        time.sleep(1)
    print("**Please ensure that you are in the game, not pausing, chatting, or using the inventory.**")
    time.sleep(3)
    print("Agent started successfully.")

    try:
        last_dist = -1
        stuck = 0
        while True:
            while not gv.ctrl_agent:
                time.sleep(1)
            if random.random() < 0.3:
                choice = gv.movement
                status = 0
                #print("Random pick.")
            else:
                x, y, z = gv.f3[gv.player_list[gv.info["agent_name"]]]["x"], gv.f3[gv.player_list[gv.info["agent_name"]]]["y"], gv.f3[gv.player_list[gv.info["agent_name"]]]["z"]
                choice, status = dfs(x, y, z)
                #print(f"choices: {choice}, score: {status}")
            if not choice:
                choice = gv.movement
            result = random.choice(choice)
            last_op = [gv.f3[gv.player_list[gv.info["agent_name"]]]["block"], result]
            move.move(result)
            now_dist = get_dist()
            if now_dist != -1 and now_dist < last_dist:
                plus((last_dist - now_dist) * last_dist)
            if gv.f3[gv.player_list[gv.info["agent_name"]]]["dv"] < 0.1:
                stuck += 0.01
                plus(-stuck)
            else:
                stuck = 0
            last_dist = now_dist
    except KeyboardInterrupt:
        print("KeyboardInterrupt(ctrl+c) received, shutting down...")
        save_file(False)
        gv.conn.disconnect()

if __name__ == "__main__":
    print("Please connect to a server first.")

    if input("Do you want to test read_file()? (y/n): ").strip().lower() == 'y':
        read_file()

    if input("Do you want to test save_file()? (y/n): ").strip().lower() == 'y':
        save_file()