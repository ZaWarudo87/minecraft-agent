import csv
import json
import os
import threading
import time

import pygetwindow as gw
from sortedcontainers import SortedKeyList
from minecraft.authentication import AuthenticationToken
from minecraft.networking.connection import Connection

from . import handle
from . import move
from . import keyboard_listener as kbl

now_dir = os.path.dirname(__file__)
heuristic_block = {}
heuristic_entity = {}
item_rarity = {}
info = {}
ctrl_agent = False
connect = None

def read_file() -> None:
    global heuristic_block, heuristic_entity, item_rarity, info
    with open(os.path.join(now_dir, "../train/heuristic_block.csv"), "r", encoding="utf-8") as f:
        fin = csv.reader(f)
        for i in fin:
            if i[0] == "action":
                continue
            block_min = int(i[1])
            if block_min not in heuristic_block:
                heuristic_block[block_min] = {
                    "block_maxStateId": int(i[2]),
                    "action": {}
                }
            heuristic_block[block_min]["action"][i[0]] = {
                "block_name": i[3],
                "score": int(i[4])
            }
        for i in heuristic_block:
            heuristic_block[i]["action"] = SortedKeyList(heuristic_block[i]["action"].items(), key=lambda x: -x[1]["score"])

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
            item_rarity[i[0]] = {
                "item_name": i[1],
                "rarity": int(i[2])
            }

    with open(os.path.join(now_dir, "login/info.json"), "r", encoding="utf-8") as f:
        info = json.load(f)
    print("Heuristic data loaded successfully.")

def save_file(get_token: bool = True) -> None:
    global heuristic_block, heuristic_entity, item_rarity
    with open(os.path.join(now_dir, "../train/heuristic_block.csv"), "w", newline="", encoding="utf-8") as f:
        fout = csv.writer(f)
        fout.writerow(["action", "block_minStateId", "block_maxStateId", "block_name", "score"])
        for block_min, block_data in heuristic_block.items():
            block_max = block_data["block_maxStateId"]
            for action, data in block_data["action"]:
                fout.writerow([action, block_min, block_max, data["block_name"], data["score"]])

    with open(os.path.join(now_dir, "../train/heuristic_entity.csv"), "w", newline="", encoding="utf-8") as f:
        fout = csv.writer(f)
        fout.writerow(["entity_id", "entity_name", "killable", "score"])
        for entity_id, entity_data in heuristic_entity.items():
            fout.writerow([entity_id, entity_data["entity_name"], int(entity_data["killable"]), entity_data["score"]])

    if get_token:
        with open(os.path.join(now_dir, "login/info.json"), "w", encoding="utf-8") as f:
            info["access_token"] = connect.auth_token.access_token
            json.dump(info, f, indent=4)
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
                if not kbl.game_test():
                    move.back_to_game()
                print("Minecraft window is active, agent control enabled.")
            else:
                print("Minecraft window is not active, agent control disabled.")
        time.sleep(1)

def start(conn: Connection) -> None:
    global connect
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
            time.sleep(1)
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