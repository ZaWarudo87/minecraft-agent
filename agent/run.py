import csv
import json
import time
from threading import Thread

from minecraft.networking.connection import Connection
from minecraft.networking.packets import Packet
from minecraft.networking.packets.clientbound.play import JoinGamePacket, PlayerListItemPacket, SpawnPlayerPacket, PlayerPositionAndLookPacket, EntityPositionDeltaPacket, ChatMessagePacket
from minecraft.networking.packets.serverbound.play import PositionAndLookPacket, TeleportConfirmPacket