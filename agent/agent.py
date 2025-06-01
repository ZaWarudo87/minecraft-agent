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

from . import handle
from . import move
from . import keyboard_listener as kbl
from . import mc

now_dir = os.path.dirname(__file__)
heuristic_block = SortedDict()
heuristic_entity = {}
item_rarity = {}
score_temp = []
score_all = 0
info = {}
ctrl_agent = False
connect = None
movement = [
    "jump", "sneak", "offset", "place",
    "walk_W", "sprint_W", "walk_WA", "sprint_WA",
    "walk_A", "sprint_A", "walk_AS", "sprint_AS",
    "walk_S", "sprint_S", "walk_SD", "sprint_SD",
    "walk_D", "sprint_D", "walk_DW", "sprint_DW",
    "break_U", "break_UF", "break_F", "break_DF", "break_D"
]
last_op = [None, None] # block, movement

def read_file() -> None:
    global heuristic_block, heuristic_entity, item_rarity, info, score_all
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
            heuristic_block[block_min]["action"][i[0]] = int(i[4])
        for i in heuristic_block:
            heuristic_block[i]["action"] = SortedKeyList(heuristic_block[i]["action"].items(), key=lambda x: -x[1])
        mc.load_block_name(heuristic_block)

    with open(os.path.join(now_dir, "../train/heuristic_entity.csv"), "r", encoding="utf-8") as f:
        fin = csv.reader(f)
        for i in fin:
            if i[0] == "entity_id":
                continue
            heuristic_entity[i[0]] = {
                "entity_name": i[1],
                "killable": bool(int(i[2])),
                "score": int(i[3])
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

    with open(os.path.join(now_dir, "login/info.json"), "r", encoding="utf-8") as f:
        info = json.load(f)

    with open(os.path.join(now_dir, "../train/score.csv"), "rb") as f:
        f.seek(-2, 2)
        try:
            while f.read(1) != b"\n":
                f.seek(-2, 1)
        except:
            f.seek(-1, 1)
        score_all = int(f.readline().decode())
    print("Heuristic data loaded successfully.")

def save_file(get_token: bool = True) -> None:
    global heuristic_block, heuristic_entity, item_rarity, score_temp
    with open(os.path.join(now_dir, "../train/heuristic_block.csv"), "w", newline="", encoding="utf-8") as f:
        fout = csv.writer(f)
        fout.writerow(["action", "block_minStateId", "block_maxStateId", "block_name", "score"])
        for block_min, block_data in heuristic_block.items():
            for action, data in block_data["action"]:
                fout.writerow([action, block_min, block_data["block_maxStateId"], block_data["block_name"], data])

    with open(os.path.join(now_dir, "../train/heuristic_entity.csv"), "w", newline="", encoding="utf-8") as f:
        fout = csv.writer(f)
        fout.writerow(["entity_id", "entity_name", "killable", "score"])
        for entity_id, entity_data in heuristic_entity.items():
            fout.writerow([entity_id, entity_data["entity_name"], int(entity_data["killable"]), entity_data["score"]])
    
    with open(os.path.join(now_dir, "../train/score.csv"), "a", newline="", encoding="utf-8") as f:
        fout = csv.writer(f)
        for i in score_temp:
            fout.writerow([i])
        score_temp = []

    if get_token:
        with open(os.path.join(now_dir, "login/info.json"), "w", encoding="utf-8") as f:
            info["access_token"] = connect.auth_token.access_token
            json.dump(info, f, indent=4)
    mc.save_block()
    print("Heuristic data saved successfully.")

def save_file_thread() -> None:
    while True:
        time.sleep(300)
        save_file()
        print("Heuristic data auto-saved.")

def check_window() -> None:
    global ctrl_agent
    while True:
        bef = ctrl_agent
        try:
            window = gw.getWindowsWithTitle("Minecraft 1.18")[0]
            ctrl_agent = handle.connected and not window.isMinimized and window.isActive
        except IndexError:
            ctrl_agent = False
        except Exception as e:
            ctrl_agent = False
            print(f"Error checking Minecraft window: {e}")
            break

        if bef != ctrl_agent:
            if ctrl_agent:
                # if not kbl.game_test():
                #     move.back_to_game()
                print("Minecraft window is active, agent control enabled.")
            else:
                print("Minecraft window is not active, agent control disabled.")
        time.sleep(1)

def gain_item(item: dict) -> None:
    global score_all, heuristic_block
    score = 0
    for k, v in item.items():
        score += 2 ** item_rarity[k]["rarity"] * v
    if score > 0:
        print(f"Score gained: {score}")
        if last_op[0] and last_op[1]:
            heuristic_block[mc.get_block_min(last_op[0])][last_op[1]] += score
            heuristic_block[handle.f3[handle.player_list[info["agent_name"]]]["block"]]["offset"] += score
            score_all += score

def minus(s: int) -> None:
    global score_all, heuristic_block
    print(f"Score minus: {s}")
    if last_op[0] and last_op[1]:
        heuristic_block[mc.get_block_min(last_op[0])][last_op[1]] -= s
        heuristic_block[handle.f3[handle.player_list[info["agent_name"]]]["block"]]["offset"] -= s
        score_all += s

def dfs(x: float, y: float, z: float, sim: list = movement, dep: int = 3) -> tuple[list, int]:
    if dep <= 0:
        return [], heuristic_block[mc.get_block_min(mc.get_block(x, y, z))]["offset"]
    
    ans = []
    for i in sim:
        nx, ny, nz, sim_block = move.move_sim(x, y, z, i)
        choice = heuristic_block[mc.get_block_min(sim_block)]["action"]
        score = 0
        for k, v in choice.items():
            if k != "offset":
                _, aft = dfs(nx, ny, nz, sim, dep - 1)
                nows = v + aft
                if nows > score:
                    score = nows
                    ans = [k]
                elif nows == score:
                    ans.append(k)
    return ans, score

def start(conn: Connection) -> None:
    global connect, last_op
    connect = conn
    read_file()
    handle.handle(conn)
    threading.Thread(target=save_file_thread, daemon=True).start()
    print("**Packet catcher started, waiting for starting Minecraft...**")
    while True:
        window = gw.getWindowsWithTitle("Minecraft 1.18")
        if window and handle.connected:
            threading.Thread(target=kbl.kb_listen, daemon=True).start()
            threading.Thread(target=check_window, daemon=True).start()
            window[0].restore()
            window[0].activate()
            break
        time.sleep(1)
    print("Agent started successfully.")

    try:
        while True:
            while not ctrl_agent:
                time.sleep(1)
            time.sleep(1) # remember to comment this!!!
            # if random.random() < 0.05:
            #     choice = movement
            #     status = 0
            #     print("Random pick.")
            # else:
            #     x, y, z = handle.f3[handle.player_list[info["agent_name"]]]["x"], handle.f3[handle.player_list[info["agent_name"]]]["y"], handle.f3[handle.player_list[info["agent_name"]]]["z"]
            #     choice, status = dfs(x, y, z)
            #     print(f"choices: {choice}, score: {status}")
            # result = random.choice(choice)
            # last_op = [handle.f3[handle.player_list[info["agent_name"]]]["block"], result]
            # move.move(result)
    except KeyboardInterrupt:
        print("KeyboardInterrupt(ctrl+c) received, shutting down...")
        save_file(False)
        conn.disconnect()

if __name__ == "__main__":
    print("Please connect to a server first.")

    if input("Do you want to test read_file()? (y/n): ").strip().lower() == 'y':
        read_file()

    if input("Do you want to test save_file()? (y/n): ").strip().lower() == 'y':
        save_file()