# my_packets.py
import minecraft.networking.packets as packets
from minecraft.networking.packets import Packet
from minecraft.networking.types import Position, VarInt, Byte

class PlayerDiggingPacket(Packet):
    packet_name = "player_digging"
    definitions = [
        ("status", VarInt),       # 0=開始破壞, 1=放棄破壞, 2=完成破壞, 3=丟棄物品
        ("location", Position),   # 方塊座標
        ("face", Byte),           # 被點擊的方塊面
    ]

class PlayerBlockPlacementPacket(Packet):
    packet_name = "block_place"
    definitions = [
        ("location", Position),   # 你要放在哪個方塊
        ("face", Byte),           # 放到方塊的哪一面
        ("hand", VarInt),         # 0=主手,1=副手
        ("cursor_x", Byte),       # 光標相對方塊面的細分座標 (0-15)
        ("cursor_y", Byte),
        ("cursor_z", Byte),
    ]
