import json
import os
import sys

from minecraft.networking.connection import Connection
from minecraft.networking.packets.clientbound.play import (
    JoinGamePacket,
    PlayerListItemPacket,
    SpawnPlayerPacket,
    PlayerPositionAndLookPacket,
    EntityPositionDeltaPacket,
    ChatMessagePacket,
)
from minecraft.networking.packets.serverbound.play import (
    KeepAlivePacket,
)

connected = False
f3 = {
    "x": 1,
    "y": 1,
    "z": 4,
    "yaw": 5,
    "pitch": 14
}
player_list = {}

now_dir = os.path.dirname(__file__)
with open(os.path.join(now_dir, "login/info.json"), "r", encoding="utf-8") as f:
    info = json.load(f)

def handle_f3(pkt: PlayerPositionAndLookPacket) -> None:
    global f3
    f3 = {
        "x": pkt.x,
        "y": pkt.y,
        "z": pkt.z,
        "yaw": pkt.yaw,
        "pitch": pkt.pitch
    }
    print(f"F3 Data - X: {f3['x']:.2f}, Y: {f3['y']:.2f}, Z: {f3['z']:.2f}, Yaw: {f3['yaw']:.2f}, Pitch: {f3['pitch']:.2f}")

def print_f3() -> None:
    global f3
    sys.stdout.write(
        f"\rF3 Data - X: {f3['x']:.2f}, Y: {f3['y']:.2f}, Z: {f3['z']:.2f}, "
        f"Yaw: {f3['yaw']:.2f}, Pitch: {f3['pitch']:.2f}"
    )
    sys.stdout.flush()

def handle_test(pkt: SpawnPlayerPacket) -> None:
    print(f"Spawned Player - Entity ID: {pkt.entity_id}, X: {pkt.x:.2f}, Y: {pkt.y:.2f}, Z: {pkt.z:.2f}")

def handle_join(pkt: JoinGamePacket):
    print(f"Connected. Entity ID: {pkt.entity_id}")

def handle_player_list(pkt: PlayerListItemPacket) -> None:
    global connected, player_list
    for action in pkt.actions:
        if isinstance(action, PlayerListItemPacket.AddPlayerAction):
            player_list[action.name] = action.uuid
            if action.name == info["agent_name"]:
                connected = True
        elif isinstance(action, PlayerListItemPacket.RemovePlayerAction):
            if action.name in player_list:
                del player_list[action.name]
            if action.name == info["agent_name"]:
                connected = False

def handle(conn: Connection) -> None:
    conn.register_packet_listener(handle_f3, PlayerPositionAndLookPacket)
    #conn.register_packet_listener(handle_test, SpawnPlayerPacket)
    conn.register_packet_listener(handle_join, JoinGamePacket)

if __name__ == "__main__":
    print("Please connect to a server first.")