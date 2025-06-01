"""
TODO
- 如果能透過種子碼拿到整張地圖的話，要去解掉 handle_join(pkt) 的註解，以獲取種子碼
- 如果有用Minecraft指令的話，記得完成 handle_chat(pkt) 去接住回傳結果
- 要完成 handle_chat(pkt) 的死亡處理
"""

import csv
import json
import math
import os
import threading
import time
from rich.live import Live
from rich.table import Table

from mcrcon import MCRcon
from minecraft.networking.connection import Connection
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

from . import agent
from . import mc

connected = False
f3 = {}
player_list = {}
my_coor = {"x": 0.0, "y": 0.0, "z": 0.0}
connect = None
look_you = [False, False] # agent_look_master, master_look_agent
receiving = False
world_time = 0

now_dir = os.path.dirname(__file__)
with open(os.path.join(now_dir, "login/info.json"), "r", encoding="utf-8") as f:
    info = json.load(f)

def handle_spawn_player(pkt: SpawnPlayerPacket) -> None:
    global f3
    for i in [k for k, v in player_list.items() if v == pkt.player_UUID]:
        player_list[i] = pkt.entity_id
    f3[pkt.entity_id] = {
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
        "item": {}
    }
    
def handle_self_pos(pkt: PlayerPositionAndLookPacket):
    global my_coor
    my_coor = {"x": pkt.x, "y": pkt.y, "z": pkt.z}

def handle_join(pkt: JoinGamePacket):
    print(f"Connected. Entity ID: {pkt.entity_id}")
    # mc.load_world(pkt.hashed_seed)
    try:
        with MCRcon(info["server"], "doggybot", port=25575) as mcr:
            response = mcr.command(f"op {info["username"]}")
            print(f"RCON Response: {response}")
        cmd("gamemode spectator")
    except Exception as e:
        print(f"Error connecting to RCON: {e}")
        print(f"Remember to set 'op {info["username"]}' in the server.")

def handle_player_list(pkt: PlayerListItemPacket) -> None:
    global connected, player_list
    for action in pkt.actions:
        if isinstance(action, PlayerListItemPacket.AddPlayerAction):
            player_list[action.name] = action.uuid
            print(f"Player {action.name} added with UUID {action.uuid}")
            if action.name == info["agent_name"]:
                connected = True
        elif isinstance(action, PlayerListItemPacket.RemovePlayerAction):
            print(f"Player with UUID {action.uuid} left")

def handle_delta(pkt: EntityPositionDeltaPacket) -> None:
    global f3
    if pkt.entity_id in f3:
        f3[pkt.entity_id]["dx"] = pkt.delta_x_float
        f3[pkt.entity_id]["dy"] = pkt.delta_y_float
        f3[pkt.entity_id]["dz"] = pkt.delta_z_float
        f3[pkt.entity_id]["x"] += pkt.delta_x_float
        f3[pkt.entity_id]["y"] += pkt.delta_y_float
        f3[pkt.entity_id]["z"] += pkt.delta_z_float

def handle_look(pkt: EntityLookPacket) -> None:
    global f3
    if pkt.entity_id in f3:
        f3[pkt.entity_id]["yaw"] = pkt.yaw
        f3[pkt.entity_id]["pitch"] = pkt.pitch

def handle_chat(pkt: ChatMessagePacket) -> None:
    global f3, player_list
    payload = pkt.json_data
    cmdt, name, text = mc.decode(payload) # command_type_NBT(?), possible_relative_player, result
    # -----------------------------------------------------------------------------------------
    # | TODO: 想辦法接到你的指令回傳結果，並做出相應處理                                          |
    # |       指令執行結果的 text 只會有值本人而已，我也找不到辦法去抓到是哪條指令發出才得到這個結果 |
    # -----------------------------------------------------------------------------------------
    if cmdt == "commands.data.entity.query":
        if name in player_list and player_list[name] in f3:
            if isinstance(text, list) and len(text) == 3 and all(isinstance(i, float) for i in text):
                f3[player_list[name]]["x"] = text[0]
                f3[player_list[name]]["y"] = text[1]
                f3[player_list[name]]["z"] = text[2]
            elif isinstance(text, float) and text >= 0 and text <= 20:
                if text < f3[player_list[name]]["health"]:
                    agent.minus(2 ** int((f3[player_list[name]]["health"] - text)) * int(20 - text))
                f3[player_list[name]]["health"] = text
            elif isinstance(text, int) and text >= 0 and text <= 20:
                f3[player_list[name]]["hungry"] = text
            elif isinstance(text, list) and len(text) > 0 and isinstance(text[0], dict) and "Slot" in text[0]:
                not_first = bool(f3[player_list[info["agent_name"]]]["item"])
                diff = mc.get_item(text, f3[player_list[info["agent_name"]]]["item"])
                if diff:
                    for k, v in diff.items():
                        if k not in f3[player_list[info["agent_name"]]]["item"]:
                            f3[player_list[info["agent_name"]]]["item"][k] = v
                        else:
                            f3[player_list[info["agent_name"]]]["item"][k] += v
                        if v > 0:
                            f3[player_list[info["agent_name"]]]["pick"] = k
                    if not_first:
                        agent.gain_item(diff)
            elif text:
                print(f"Chat message received and logged: {cmdt} - {name} - {text}")
        else:
            print(f"Player {name} not found in player list or F3 data.")
    elif "death" in cmdt and name == info["agent_name"]:
        # ----------------------------------------
        # | TODO: agent死亡時，請想辦法讓它自動復活 |
        # ----------------------------------------
        agent.minus(1024)
        with open(os.path.join(now_dir, "../train/death_time.csv"), "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([world_time])
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
    global world_time
    world_time = pkt.world_age
    agent.score_temp.append(agent.score_all)

def update_coor() -> Table:
    global f3
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

    for k, v in f3.items():
        v["block"] = mc.get_block(math.floor(v["x"]), math.floor(v["y"]) - 1, math.floor(v["z"]))
        v["gaze"] = mc.get_gaze_block(v["x"], v["y"] + 1, v["z"], v["yaw"], v["pitch"], look_you)
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
            time.sleep(0.05) # 1 tick
            if not receiving and agent.ctrl_agent:
                if info["agent_name"] in player_list:
                    cmd(f"data get entity {info["agent_name"]} Pos")
                    cmd(f"data get entity {info["agent_name"]} Health")
                    cmd(f"data get entity {info["agent_name"]} foodLevel")
                    cmd(f"data get entity {info["agent_name"]} Inventory")
                if info["master_name"] in player_list:
                    cmd(f"data get entity {info["master_name"]} Pos")
            live.update(update_coor())

def keep_around() -> None:
    global connect, my_coor, f3, player_list, info, connected
    while True:
        if connected:
            #cmd(f"data get entity {info["agent_name"]} Inventory")
            if info["agent_name"] in player_list:
                speed = 1
                while True:
                    dx = f3[player_list[info["agent_name"]]]["x"] - my_coor["x"]
                    dy = f3[player_list[info["agent_name"]]]["y"] - my_coor["y"]
                    dz = f3[player_list[info["agent_name"]]]["z"] - my_coor["z"]
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
                    connect.write_packet(pkt)
                    time.sleep(0.1)
        time.sleep(30)

def cmd(line: str) -> None:
    connect.write_packet(ChatPacket(message=f"/{line}"))

def handle(conn: Connection) -> None:
    global connect
    connect = conn

    conn.register_packet_listener(handle_spawn_player, SpawnPlayerPacket)
    conn.register_packet_listener(handle_test, Packet)
    conn.register_packet_listener(handle_join, JoinGamePacket)
    conn.register_packet_listener(handle_player_list, PlayerListItemPacket)
    #conn.register_packet_listener(handle_delta, EntityPositionDeltaPacket)
    conn.register_packet_listener(handle_look, EntityLookPacket)
    conn.register_packet_listener(handle_self_pos, PlayerPositionAndLookPacket)
    conn.register_packet_listener(handle_chat, ChatMessagePacket)
    conn.register_packet_listener(handle_block, BlockChangePacket)
    conn.register_packet_listener(handle_chunk, MultiBlockChangePacket)
    conn.register_packet_listener(handle_time, TimeUpdatePacket)
    #conn.register_packet_listener(handle_sound, SoundEffectPacket)

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