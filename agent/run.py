import csv
import json
import sys
import time
from threading import Thread

from minecraft.networking.connection import Connection
from minecraft.networking.packets import Packet
from minecraft.networking.packets.clientbound.play import JoinGamePacket, PlayerListItemPacket, SpawnPlayerPacket, PlayerPositionAndLookPacket, EntityPositionDeltaPacket, ChatMessagePacket
from minecraft.networking.packets.serverbound.play import PositionAndLookPacket, TeleportConfirmPacket

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python run.py <server> <port>")
        sys.exit(1)