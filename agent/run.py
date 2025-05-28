import csv
import json
import os
import time
from threading import Thread

from minecraft.networking.connection import Connection
from minecraft.networking.packets import Packet
from minecraft.networking.packets.clientbound.play import JoinGamePacket, PlayerListItemPacket, SpawnPlayerPacket, PlayerPositionAndLookPacket, EntityPositionDeltaPacket, ChatMessagePacket
from minecraft.networking.packets.serverbound.play import PositionAndLookPacket, TeleportConfirmPacket

from .login import login

def main():
    now_dir = os.path.dirname(__file__)
    with open(os.path.join(now_dir, "login/info.json"), "r", encoding="utf-8") as f:
        info = json.load(f)
    
    if not info["auth_token"]:
        login.main()
    try:
        conn = Connection(info["server"], info["port"], username=info["username"], auth_token=info["auth_token"], online=True)
        conn.connect()
    except Exception as e:
        print(f"Error connecting to server: {e}")
        if input("Do you want to re-login? (y/n): ").strip().lower() == 'y':
            login.main()
            conn = Connection(info["server"], info["port"], username=info["username"], auth_token=info["auth_token"], online=True)
            conn.connect()
    print(f"Connected to server {info['server']}:{info['port']} as {info['username']}")

if __name__ == "__main__":
    main()