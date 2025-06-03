import json
import os

Now_dir = os.path.dirname(__file__)
info = {}

conn = None

score_temp = []
score_all = 0
ctrl_agent = False
movement = [
    "jump", "sneak", "offset", "place",
    "walk_W", "sprint_W", "walk_WA", "sprint_WA",
    "walk_A", "sprint_A", "walk_AS", "sprint_AS",
    "walk_S", "sprint_S", "walk_SD", "sprint_SD",
    "walk_D", "sprint_D", "walk_DW", "sprint_DW",
    "break_U", "break_UF", "break_F", "break_DF", "break_D"
]
get = False

tool_num = {}
dir_deg = {
    "W": 0,
    "WA": -45,
    "A": -90,
    "AS": -135,
    "S": -180,
    "SD": 135,
    "D": 90,
    "DW": 45
}
break_deg = {
    "U": -90,
    "UF": -45,
    "F": 0,
    "DF": 45,
    "D": 90
}

pressed_key = set()

TICK = 0.05 # 0.05 seconds per tick, 20 ticks per second
connected = False
f3 = {}
player_list = {}
world_time = 0

def load_info() -> None:
    global info
    with open(os.path.join(Now_dir, "login/info.json"), "r", encoding="utf-8") as f:
        info = json.load(f)

if __name__ == "__main__":
    load_info()
    print("Global variables initialized successfully.")