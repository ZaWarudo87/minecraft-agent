import json
import os
import re
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
    PlayerListItemPacket,
    PlayerPositionAndLookPacket,
    SpawnPlayerPacket,
)
from minecraft.networking.packets.serverbound.play import (
    PositionAndLookPacket,
)

from . import mc_cmd

connected = False
f3 = {}
player_list = {}
my_coor = {'x': 0.0, 'y': 0.0, 'z': 0.0}
connect = None

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
        "dx": 0.0,
        "dy": 0.0,
        "dz": 0.0
    }
    print(f"{pkt.entity_id} - X: {pkt.x:.2f}, Y: {pkt.y:.2f}, Z: {pkt.z:.2f}, Yaw: {pkt.yaw:.2f}, Pitch: {pkt.pitch:.2f}")

def handle_self_pos(pkt: PlayerPositionAndLookPacket):
    global my_coor
    print(f"Self Position - X: {pkt.x:.2f}, Y: {pkt.y:.2f}, Z: {pkt.z:.2f}")
    my_coor = {"x": pkt.x, "y": pkt.y, "z": pkt.z}

def handle_test(pkt: Packet) -> None:
    pkt_name = pkt.__class__.__name__
    lint_off = [
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
        "PlayerPositionAndLookPacket",
        "PlayerListItemPacket",
        "PluginMessagePacket",
        "ResponsePacket",
        "ServerDifficultyPacket",
        "SetCompressionPacket",
        "SpawnObjectPacket",
        "SpawnPlayerPacket",
        "TimeUpdatePacket",
        "UpdateHealthPacket",
    ]
    if pkt_name not in lint_off:
        print(f"[ALL] {pkt_name}")

def handle_join(pkt: JoinGamePacket):
    print(f"Connected. Entity ID: {pkt.entity_id}")
    try:
        with MCRcon(info["server"], "doggybot", port=25575) as mcr:
            response = mcr.command(f"op {info["username"]}")
            print(f"RCON Response: {response}")
        cmd("gamemode spectator")
        cmd(f"data get entity {info["agent_name"]} Health")
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
    payload = pkt.json_data
    cmdt, text = mc_cmd.decode(payload)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = json.loads(payload)
    with open(os.path.join(now_dir, "other/chat_log.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)
    with open(os.path.join(now_dir, "other/chat_log.txt"), "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Chat message received and logged: {cmdt}")

def handle_block(pkt: BlockChangePacket) -> None:
    print(f"Block changed at ({pkt.location.x}, {pkt.location.y}, {pkt.location.z}) to {pkt.block_state_id}")

def update_coor() -> Table:
    global f3
    coor_table = Table(title="Entity Coordinates")
    coor_table.add_column("ID")
    coor_table.add_column("X")
    coor_table.add_column("Y")
    coor_table.add_column("Z")
    coor_table.add_column("Yaw")
    coor_table.add_column("Pitch")

    for k, v in f3.items():
        coor_table.add_row(
            str(k),
            f"{v['x']:.2f}",
            f"{v['y']:.2f}",
            f"{v['z']:.2f}",
            f"{v['yaw']:.2f}",
            f"{v['pitch']:.2f}"
        )
    return coor_table

def print_f3() -> None:
    with Live(update_coor(), refresh_per_second=10, screen=False) as live:
        while True:
            time.sleep(0.05)
            live.update(update_coor())

def keep_around() -> None:
    global connect, my_coor, f3, player_list, info, connected
    while True:
        if connected:
            cmd(f"data get entity {info["agent_name"]}")
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
    conn.register_packet_listener(handle_delta, EntityPositionDeltaPacket)
    conn.register_packet_listener(handle_look, EntityLookPacket)
    conn.register_packet_listener(handle_self_pos, PlayerPositionAndLookPacket)
    conn.register_packet_listener(handle_chat, ChatMessagePacket)
    conn.register_packet_listener(handle_block, BlockChangePacket)

    threading.Thread(target=print_f3, daemon=True).start()
    threading.Thread(target=keep_around, daemon=True).start()

if __name__ == "__main__":
    print("Please connect to a server first.")