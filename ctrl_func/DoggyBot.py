# DoggyBot.py
import time
import json
from threading import Thread

from minecraft.networking.connection import Connection
from minecraft.networking.packets import Packet

# ===== clientbound play 封包 =====
from minecraft.networking.packets.clientbound.play import *

# ===== serverbound play 封包 =====
from minecraft.networking.packets.serverbound.play import *
from my_packets import PlayerDiggingPacket, PlayerBlockPlacementPacket

# === 參數設定 ===
SERVER          = '140.113.95.112'
PORT            = 25565
BOT_NAME        = 'DoggyBot'
TARGET_NAME     = 'Kurosaki0719'
FOLLOW_DISTANCE = 3.0    # 格
STEP_SIZE       = 0.2    # 每步距離 (格)
SLEEP_INTERVAL  = 0.1    # 跟隨間隔 (秒)

# === 全域狀態 ===
conn             = Connection(SERVER, PORT, username=BOT_NAME)
current_pos      = {'x':0.0,'y':0.0,'z':0.0}
player_positions = {}    # entity_id -> {'x','y','z'}
player_deltas   = {}    # entity_id -> {'dx','dy','dz'}
target_id        = None
following        = False
tpid = None  # 用來追蹤目標的 Entity ID

# 0. (Debug) 印出所有封包
def handle_all(pkt: Packet):
    print(f"[ALL] {pkt.__class__.__name__}")
#conn.register_packet_listener(handle_all, Packet)

# 1. 取得目標 Entity ID
def handle_player_list(pkt: PlayerListItemPacket):
    print(f"[🔔] 處理玩家列表封包")
    global target_id
    for action in pkt.actions:
        if isinstance(action, PlayerListItemPacket.AddPlayerAction):
            print(f"[加入] 玩家 {action.name} (UUID: {action.uuid})")
            if action.name == TARGET_NAME:
                target_id = action.uuid
                print(f"[🔔] 找到玩家 {action.name}，UUID={target_id}")
        elif isinstance(action, PlayerListItemPacket.RemovePlayerAction):
            print(f"[離開] 玩家 (UUID: {action.uuid})")
        elif isinstance(action, PlayerListItemPacket.UpdateGameModeAction):
            print(f"[更新] {action.uuid} 模式改成 {action.gamemode}")
conn.register_packet_listener(handle_player_list, PlayerListItemPacket)

# 2. 初始座標
def handle_spawn(pkt: SpawnPlayerPacket):
    global target_id
    print(f"[🔔] 處理玩家生成封包：{pkt.entity_id} - {pkt.player_UUID}")
    if pkt.player_UUID == target_id:
        target_id = pkt.entity_id
        player_positions[target_id] = {'x':pkt.x,'y':pkt.y,'z':pkt.z}
        print(f"[🔔] 初始座標：({pkt.x:.2f},{pkt.y:.2f},{pkt.z:.2f})")
conn.register_packet_listener(handle_spawn, SpawnPlayerPacket)

# 3. 更新自己位置
def handle_self_pos(pkt: PlayerPositionAndLookPacket):
    global current_pos, tpid
    print(f"[🔄] 更新自己位置：({pkt.x:.2f},{pkt.y:.2f},{pkt.z:.2f})")
    current_pos['x'], current_pos['y'], current_pos['z'] = pkt.x, pkt.y, pkt.z
    tpid = pkt.teleport_id
conn.register_packet_listener(handle_self_pos, PlayerPositionAndLookPacket)

# 4. 追蹤目標微移
def handle_delta(pkt: EntityPositionDeltaPacket):
    global player_deltas
    if pkt.entity_id == target_id:
        player_deltas[target_id] = {
            'x': pkt.delta_x_float,
            'y': pkt.delta_y_float,
            'z': pkt.delta_z_float
        }
        print(f"[🔄] delta：{pkt.entity_id}, x = {pkt.delta_x_float:.2f}, y = {pkt.delta_y_float:.2f}, z = {pkt.delta_z_float:.2f}")
conn.register_packet_listener(handle_delta, EntityPositionDeltaPacket)

# 5. 聊天指令
def handle_chat(pkt: ChatMessagePacket):
    print(f"[💬] 處理聊天封包：{pkt.json_data}")
    global following
    raw = pkt.json_data
    if isinstance(raw, str):
        try: raw = json.loads(raw)
        except: raw = {'text':raw}
    if 'text' in raw:
        text = raw['text']
    elif 'translate' in raw and 'with' in raw:
        w = raw['with'][-1]
        text = w.get('text') if isinstance(w,dict) else str(w)
    else:
        text = ''
    cmd = text.strip().lower()
    if cmd == '!follow':
        following = True; print('[▶] 已啟動尾隨')
    elif cmd == '!stop':
        following = False; print('[■] 已停止尾隨')
    elif cmd.startswith('!dig '):
        _, xs, ys, zs = cmd.split()
        dig_block(int(xs),int(ys),int(zs))
    elif cmd.startswith('!place '):
        _, xs, ys, zs = cmd.split()
        place_block(int(xs),int(ys),int(zs))
    elif cmd == '!coor':
        print(f"[🚀] 目前位置：x = {player_positions[target_id]['x']:.2f}, y = {player_positions[target_id]['y']:.2f}, z = {player_positions[target_id]['z']:.2f}")

conn.register_packet_listener(handle_chat, ChatMessagePacket)

# 6. 挖/放函式
def dig_block(x,y,z,face=1):
    pkt = PlayerDiggingPacket(); pkt.status=0; pkt.location=(x,y,z); pkt.face=face
    conn.write_packet(pkt); time.sleep(0.1)
    pkt.status=2; conn.write_packet(pkt)
    print(f"[🔨] 挖除方塊：({x},{y},{z})")

def place_block(x,y,z,face=1,hand=0):
    pkt = PlayerBlockPlacementPacket()
    pkt.location=(x,y,z); pkt.face=face; pkt.hand=hand
    pkt.cursor_x=pkt.cursor_y=pkt.cursor_z=8
    conn.write_packet(pkt)
    print(f"[🧱] 放置方塊：({x},{y},{z})")

# 7. 模仿踏步移動
def move_step(dx,dz):
    pkt = PositionAndLookPacket()
    pkt.x = current_pos['x']+dx
    pkt.feet_y=current_pos['y']
    pkt.z=current_pos['z']+dz
    pkt.yaw=pkt.pitch=0
    pkt.on_ground=False
    conn.write_packet(pkt)

# 8. 跟隨執行緒
def follow_loop():
    global target_id, following, player_positions, player_deltas
    while True:
        if target_id in player_positions and target_id in player_deltas:
            p = player_positions[target_id]
            d = player_deltas[target_id]
            p['x'] += d['x']
            p['y'] += d['y']
            p['z'] += d['z']
            if following:
                tx,tz = p['x'], p['z']
                cx,cz = current_pos['x'], current_pos['z']
                dx, dz = tx-cx, tz-cz
                dist = (dx*dx+dz*dz)**0.5
                if dist > FOLLOW_DISTANCE:
                    step_dx, step_dz = dx/dist*STEP_SIZE, dz/dist*STEP_SIZE
                    move_step(step_dx, step_dz)
                    print(f"[DEBUG] 走一步 Δ=({step_dx:.2f},{step_dz:.2f}) 距離={dist:.2f}")
        time.sleep(SLEEP_INTERVAL)

# 9. on_join 啟動
def on_join(pkt: JoinGamePacket):
    print(f"[✅] {BOT_NAME} 已登入，輸入 !follow / !stop / !dig / !place")
    Thread(target=follow_loop, daemon=True).start()
conn.register_packet_listener(on_join, JoinGamePacket)

# 10. 開始連線
print(f"[🚀] 連線到 {SERVER}:{PORT}，身份 {BOT_NAME}")
conn.connect()
while True: time.sleep(1)
