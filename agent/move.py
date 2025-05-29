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

f3 = {
    "x": 1,
    "y": 1,
    "z": 4,
    "yaw": 5,
    "pitch": 14
}

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

def handle(conn: Connection) -> None:
    conn.register_packet_listener(handle_f3, PlayerPositionAndLookPacket)
    #conn.register_packet_listener(handle_test, SpawnPlayerPacket)
    conn.register_packet_listener(handle_join, JoinGamePacket)

if __name__ == "__main__":
    print("Please connect to a server first.")