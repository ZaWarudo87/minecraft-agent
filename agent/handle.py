"""
TODO
- 如果能透過種子碼拿到整張地圖的話，要去解掉 handle_join(pkt) 的註解，以獲取種子碼
- 如果有用Minecraft指令的話，記得完成 handle_chat(pkt) 去接住回傳結果
- 要完成 handle_chat(pkt) 的死亡處理
"""

import csv
import os
import subprocess
import threading
import time
from rich.live import Live
from rich.table import Table

from mcrcon import MCRcon
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from minecraft.networking.packets import Packet, ChatPacket
from minecraft.networking.packets.clientbound.play import (
    BlockChangePacket,
    ChatMessagePacket,
    EntityLookPacket,
    EntityPositionDeltaPacket,
    JoinGamePacket,
    MultiBlockChangePacket,
    PlayerListItemPacket,
    PlayerPositionAndLookPacket,
    SoundEffectPacket,
    SpawnPlayerPacket,
    TimeUpdatePacket
)
from minecraft.networking.packets.serverbound.play import (
    ChatPacket,
    PositionAndLookPacket
)

from .agent import plus, gain_item
from . import mc
from . import global_var as gv
import server.region_to_json as rtj

my_coor = {"x": 0.0, "y": 0.0, "z": 0.0}
look_you = [False, False] # agent_look_master, master_look_agent
receiving = False

now_dir = os.path.dirname(__file__)
pth = os.path.join(now_dir, "../server/world/region")

class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            event_path = os.path.join(pth, event.src_path)
            print(f"New file detected: {event_path}")
            rtj.process_region(event_path, gv.info)

    def on_modified(self, event):
        if not event.is_directory:
            event_path = os.path.join(pth, event.src_path)
            print(f"File modified: {event_path}")
            rtj.process_region(event_path, gv.info)

def handle_spawn_player(pkt: SpawnPlayerPacket) -> None:
    for i in [k for k, v in gv.player_list.items() if v == pkt.player_UUID]:
        gv.player_list[i] = pkt.entity_id
    gv.f3[pkt.entity_id] = {
        "x": pkt.x,
        "y": pkt.y,
        "z": pkt.z,
        "yaw": pkt.yaw,
        "pitch": pkt.pitch,
        # "dx": 0.0,
        # "dy": 0.0,
        # "dz": 0.0,
        "health": 20.0,
        "hungry": 20,
        "block": -1,
        "gaze": -1,
        "pick": "none",
        "item": {},
        "look": [0, 0, 0], 
        "dv": 0.0
    }
    
def handle_self_pos(pkt: PlayerPositionAndLookPacket):
    global my_coor, pth
    my_coor = {"x": pkt.x, "y": pkt.y, "z": pkt.z}

def handle_join(pkt: JoinGamePacket):
    print(f"Connected. Entity ID: {pkt.entity_id}")
    try:
        with MCRcon(gv.info["server"], "doggybot", port=25575) as mcr:
            response = mcr.command(f"op {gv.info["username"]}")
            print(f"RCON Response: {response}")
        cmd("gamemode spectator")
        cmd("gamerule doImmediateRespawn true")
    except Exception as e:
        print(f"Error connecting to RCON: {e}")
        print(f"Remember to set 'op {gv.info["username"]}' in the server.")
    if gv.info["server"] != "localhost":
        abs_dir = os.path.abspath(os.path.join(now_dir, "../server"))
        subprocess.Popen(["cmd.exe", "/c", f"start cmd.exe /k \"cd /d {abs_dir} && python regenerate_with_seed.py --seed {pkt.hashed_seed}\""])
    else:
        region_files = os.listdir(pth)
        for i in region_files:
            region_path = os.path.join(pth, i)
            if os.path.exists(region_path):
                rtj.process_region(region_path, gv.info)
            else:
                print(f"Warning: Region file {region_path} not found, skipping")
    obs = Observer()
    obs.schedule(NewFileHandler(), path=pth, recursive=False)
    obs.start()

def handle_player_list(pkt: PlayerListItemPacket) -> None:
    for action in pkt.actions:
        if isinstance(action, PlayerListItemPacket.AddPlayerAction):
            gv.player_list[action.name] = action.uuid
            print(f"Player {action.name} added with UUID {action.uuid}")
            if action.name == gv.info["agent_name"]:
                gv.connected = True
        elif isinstance(action, PlayerListItemPacket.RemovePlayerAction):
            print(f"Player with UUID {action.uuid} left")

def handle_delta(pkt: EntityPositionDeltaPacket) -> None:
    if pkt.entity_id in gv.f3:
        gv.f3[pkt.entity_id]["dx"] = pkt.delta_x_float
        gv.f3[pkt.entity_id]["dy"] = pkt.delta_y_float
        gv.f3[pkt.entity_id]["dz"] = pkt.delta_z_float
        gv.f3[pkt.entity_id]["x"] += pkt.delta_x_float
        gv.f3[pkt.entity_id]["y"] += pkt.delta_y_float
        gv.f3[pkt.entity_id]["z"] += pkt.delta_z_float

def handle_look(pkt: EntityLookPacket) -> None:
    if pkt.entity_id in gv.f3:
        gv.f3[pkt.entity_id]["yaw"] = pkt.yaw
        gv.f3[pkt.entity_id]["pitch"] = pkt.pitch

def handle_chat(pkt: ChatMessagePacket) -> None:
    payload = pkt.json_data
    cmdt, name, text = mc.decode(payload) # command_type_NBT(?), possible_relative_player, result
    # -----------------------------------------------------------------------------------------
    # | TODO: 想辦法接到你的指令回傳結果，並做出相應處理                                          |
    # |       指令執行結果的 text 只會有值本人而已，我也找不到辦法去抓到是哪條指令發出才得到這個結果 |
    # -----------------------------------------------------------------------------------------
    if cmdt == "commands.data.entity.query":
        if name in gv.player_list and gv.player_list[name] in gv.f3:
            if isinstance(text, list) and len(text) == 3 and all(isinstance(i, float) for i in text):
                gv.f3[gv.player_list[name]]["dv"] = ((text[0] - gv.f3[gv.player_list[name]]["x"]) ** 2 + (text[1] - gv.f3[gv.player_list[name]]["y"]) ** 2 + (text[2] - gv.f3[gv.player_list[name]]["z"]) ** 2) ** 0.5
                gv.f3[gv.player_list[name]]["x"] = text[0]
                gv.f3[gv.player_list[name]]["y"] = text[1]
                gv.f3[gv.player_list[name]]["z"] = text[2]
            elif isinstance(text, float) and text >= 0 and text <= 20:
                if text < gv.f3[gv.player_list[name]]["health"]:
                    plus(2 ** int((gv.f3[gv.player_list[name]]["health"] - text)) * int(20 - text) * -1)
                gv.f3[gv.player_list[name]]["health"] = text
            elif isinstance(text, int) and text >= 0 and text <= 20:
                gv.f3[gv.player_list[name]]["hungry"] = text
            elif isinstance(text, list) and len(text) > 0 and isinstance(text[0], dict) and "Slot" in text[0]:
                not_first = bool(gv.f3[gv.player_list[gv.info["agent_name"]]]["item"])
                diff = mc.get_item(text, gv.f3[gv.player_list[gv.info["agent_name"]]]["item"])
                if diff:
                    for k, v in diff.items():
                        if k not in gv.f3[gv.player_list[gv.info["agent_name"]]]["item"]:
                            gv.f3[gv.player_list[gv.info["agent_name"]]]["item"][k] = v
                        else:
                            gv.f3[gv.player_list[gv.info["agent_name"]]]["item"][k] += v
                        if v > 0:
                            gv.f3[gv.player_list[gv.info["agent_name"]]]["pick"] = k
                    if not_first:
                        gain_item(diff)
            elif text:
                print(f"Chat message received and logged: {cmdt} - {name} - {text}")
        else:
            print(f"Player {name} not found in player list or F3 data.")
    elif "death" in cmdt and name == gv.info["agent_name"]:
        # ----------------------------------------
        # | TODO: agent死亡時，請想辦法讓它自動復活 |
        # ----------------------------------------
        #cmd(f"gamemode survival {gv.info["agent_name"]}")
        plus(-1024)
        with open(os.path.join(now_dir, "../train/death_time.csv"), "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([gv.world_time])
    else:
        print(f"Chat message received and logged: {cmdt} - {name} - {text}")

def handle_block(pkt: BlockChangePacket) -> None:
    mc.set_block(pkt.location.x, pkt.location.y, pkt.location.z, pkt.block_state_id)

def handle_chunk(pkt: MultiBlockChangePacket) -> None:
    #print(pkt)
    global receiving
    receiving = True
    bx = pkt.chunk_section_pos.x * 16
    by = pkt.chunk_section_pos.y * 16
    bz = pkt.chunk_section_pos.z * 16
    for i in pkt.records:
        mc.set_block(bx + i.x, by + i.y, bz + i.z, i.block_state_id)
    receiving = False

def handle_sound(pkt: SoundEffectPacket) -> None:
    print(f"Sound effect received: {pkt.sound_id} in {pkt.sound_category} at {pkt.effect_position} with volume {pkt.volume} and pitch {pkt.pitch}")

def handle_time(pkt: TimeUpdatePacket) -> None:
    gv.world_time = pkt.world_age
    gv.score_temp.append(gv.score_all)

def update_coor() -> Table:
    coor_table = Table(title="Entity Coordinates")
    coor_table.add_column("ID")
    coor_table.add_column("X")
    coor_table.add_column("Y")
    coor_table.add_column("Z")
    coor_table.add_column("Yaw")
    coor_table.add_column("Pitch")
    coor_table.add_column("Health")
    coor_table.add_column("Hungry")
    coor_table.add_column("Block")
    coor_table.add_column("Gaze")
    coor_table.add_column("Pick")

    for k, v in gv.f3.items():
        v["block"] = mc.get_block(v["x"], v["y"] - 1, v["z"])
        v["gaze"] = mc.get_gaze_block(v["x"], v["y"] + 1, v["z"], v["yaw"], v["pitch"], look_you, v["look"])
        coor_table.add_row(
            str(k),
            f"{v["x"]:.2f}",
            f"{v["y"]:.2f}",
            f"{v["z"]:.2f}",
            f"{v["yaw"]:.2f}",
            f"{v["pitch"]:.2f}",
            f"{v["health"]:.2f}",
            f"{v["hungry"]}",
            f"{mc.get_block_name(v["block"])}({v["block"]})",
            f"{mc.get_block_name(v["gaze"])}({v["gaze"]})",
            v["pick"]
        )
    return coor_table

def print_f3() -> None:
    with Live(update_coor(), refresh_per_second=10, screen=False) as live:
        while True:
            time.sleep(gv.TICK)
            if not receiving and gv.ctrl_agent:
                if gv.info["agent_name"] in gv.player_list:
                    cmd(f"data get entity {gv.info["agent_name"]} Pos")
                    cmd(f"data get entity {gv.info["agent_name"]} Health")
                    cmd(f"data get entity {gv.info["agent_name"]} foodLevel")
                    cmd(f"data get entity {gv.info["agent_name"]} Inventory")
                if gv.info["master_name"] in gv.player_list:
                    cmd(f"data get entity {gv.info["master_name"]} Pos")
            live.update(update_coor())

def keep_around() -> None:
    global my_coor
    while True:
        if gv.connected:
            #cmd(f"data get entity {info["agent_name"]} Inventory")
            if gv.info["agent_name"] in gv.player_list:
                speed = 1
                while True:
                    dx = gv.f3[gv.player_list[gv.info["agent_name"]]]["x"] - my_coor["x"]
                    dy = gv.f3[gv.player_list[gv.info["agent_name"]]]["y"] - my_coor["y"]
                    dz = gv.f3[gv.player_list[gv.info["agent_name"]]]["z"] - my_coor["z"]
                    if dx == 0 and dy == 0 and dz == 0:
                        break

                    abs_dx = abs(dx)
                    abs_dy = abs(dy)
                    abs_dz = abs(dz)
                    if dx != 0:
                        my_coor["x"] += [dx, speed * (dx / abs_dx)][abs_dx > speed]
                    if dy != 0:
                        my_coor["y"] += [dy, speed * (dy / abs_dy)][abs_dy > speed]
                    if dz != 0:
                        my_coor["z"] += [dz, speed * (dz / abs_dz)][abs_dz > speed]

                    pkt = PositionAndLookPacket()
                    pkt.x = my_coor["x"]
                    pkt.feet_y = my_coor["y"]
                    pkt.z = my_coor["z"]
                    pkt.yaw = 0
                    pkt.pitch = 0
                    pkt.on_ground = False
                    gv.conn.write_packet(pkt)
                    time.sleep(0.1)
        time.sleep(30)

def cmd(line: str) -> None:
    gv.conn.write_packet(ChatPacket(message=f"/{line}"))

def get_dist() -> float:
    if gv.info["agent_name"] in gv.player_list and gv.info["master_name"] in gv.player_list:
        agent_id = gv.player_list[gv.info["agent_name"]]
        master_id = gv.player_list[gv.info["master_name"]]
        agent_pos = gv.f3[agent_id]
        master_pos = gv.f3[master_id]
        return ((agent_pos["x"] - master_pos["x"]) ** 2 + (agent_pos["y"] - master_pos["y"]) ** 2 + (agent_pos["z"] - master_pos["z"]) ** 2) ** 0.5
    return -1

def handle() -> None:
    gv.conn.register_packet_listener(handle_spawn_player, SpawnPlayerPacket)
    gv.conn.register_packet_listener(handle_test, Packet)
    gv.conn.register_packet_listener(handle_join, JoinGamePacket)
    gv.conn.register_packet_listener(handle_player_list, PlayerListItemPacket)
    #gv.conn.register_packet_listener(handle_delta, EntityPositionDeltaPacket)
    gv.conn.register_packet_listener(handle_look, EntityLookPacket)
    gv.conn.register_packet_listener(handle_self_pos, PlayerPositionAndLookPacket)
    gv.conn.register_packet_listener(handle_chat, ChatMessagePacket)
    gv.conn.register_packet_listener(handle_block, BlockChangePacket)
    gv.conn.register_packet_listener(handle_chunk, MultiBlockChangePacket)
    gv.conn.register_packet_listener(handle_time, TimeUpdatePacket)
    #gv.conn.register_packet_listener(handle_sound, SoundEffectPacket)

    threading.Thread(target=print_f3, daemon=True).start()
    threading.Thread(target=keep_around, daemon=True).start()

def handle_test(pkt: Packet) -> None:
    pkt_name = pkt.__class__.__name__
    lint_off = [ # This is all that appears before and I've tried to use.
        "Packet",
        "BlockChangePacket",
        "ChatMessagePacket",
        "EncryptionRequestPacket",
        "EntityPositionDeltaPacket", 
        "EntityVelocityPacket", 
        "EntityLookPacket",
        "JoinGamePacket",
        "KeepAlivePacket",
        "LoginSuccessPacket",
        "MultiBlockChangePacket",
        "PlayerPositionAndLookPacket",
        "PlayerListItemPacket",
        "PluginMessagePacket",
        "ResponsePacket",
        "ServerDifficultyPacket",
        "SetCompressionPacket",
        "SoundEffectPacket",
        "SpawnObjectPacket",
        "SpawnPlayerPacket",
        "TimeUpdatePacket",
        "UpdateHealthPacket",
    ]
    if pkt_name not in lint_off:
        print(f"[ALL] {pkt_name}")

if __name__ == "__main__":
    print("Please connect to a server first.")