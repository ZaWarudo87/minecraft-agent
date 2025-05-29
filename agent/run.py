import csv
import json
import os
import threading
import time

from minecraft.authentication import AuthenticationToken
from minecraft.networking.connection import Connection
from minecraft.networking.packets import Packet, DisconnectPacket
from minecraft.networking.packets.clientbound.play import JoinGamePacket, PlayerListItemPacket, SpawnPlayerPacket, PlayerPositionAndLookPacket, EntityPositionDeltaPacket, ChatMessagePacket
from minecraft.networking.packets.serverbound.play import PositionAndLookPacket, TeleportConfirmPacket

from .login import login

now_dir = os.path.dirname(__file__)
with open(os.path.join(now_dir, "login/info.json"), "r", encoding="utf-8") as f:
    info = json.load(f)

def connect() -> None:
    token = AuthenticationToken(info["username"], info["access_token"], " ")
    token.profile.name = info["username"]
    token.profile.id_ = info["id"]
    if not token.authenticated:
        print("You haven't logged in yet, please login first.")
        relogin()
        return
    conn = Connection(info["server"], info["port"], username=info["username"], auth_token=token)
    conn.connect()
    conn.register_packet_listener(handle_disconnect, DisconnectPacket)
    conn.exception_handler = handle_exception
    print(f"Connected to server {info['server']}:{info['port']} as {info['username']}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt(ctrl+c) received, shutting down...")
        conn.disconnect()
    except Exception as e:
        print(f"Error during connection: {e}")
        conn.disconnect()
        relogin()

def relogin() -> None:
    if input("Do you want to login? (y/n): ").strip().lower() == 'y':
        login.main()
        with open(os.path.join(now_dir, "login/info.json"), "r", encoding="utf-8") as f:
            global info
            info = json.load(f)
        connect()

def handle_disconnect(pkt: Packet) -> None:
    print(f"Disconnected from server: {pkt.reason}")
    relogin()

def handle_exception(pkt: Packet) -> None:
    print(f"Exception occurred: {pkt.exception}")
    relogin()

def main() -> None:
    try:
        connect()
    except KeyboardInterrupt:
        print("KeyboardInterrupt(ctrl+c) received, shutting down...")
        return
    except Exception as e:
        print(f"Error connecting to server: {e}")
        relogin()

if __name__ == "__main__":
    main()