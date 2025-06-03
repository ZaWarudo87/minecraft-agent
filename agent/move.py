"""
TODO
- 完成 move(cmd)
- 切視角請用 move_mouse_relative(dx, dy)，這邊不能用 MouseController，只有點擊時才行
- switch_tool(tool) 可以切過去快捷欄裡面有的指定工具
- 不建議直接拿 move 系列的函式使用
- 經過實測，move_forward(0.2317) 可以往前走接近剛好一格，turn_right(0.105) 可以剛好把頭右轉接近45度
"""

import ctypes
import json
import math
import os
import time

from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController

from . import mc
from . import global_var as gv
from .handle import cmd as CMD

TURN_45_DEG = 0.105
# Data from Minecraft Wiki
WALK_SPEED = 0.21585
SPRINT_SPEED = 0.2806
JUMP_HEIGHT = 1.2522
EAT_SPEED = 1.6

kb = KeyboardController()
mouse = MouseController()
status = {
    "pressing_w": False,
    "sprinting": False,
    "sneaking": False
}

now_dir = os.path.dirname(__file__)
block_info = {}
with open(os.path.join(now_dir, "../train/MCdata/blocks.json"), "r", encoding="utf-8") as f:
    fin = json.load(f)
    for i in fin:
        block_info[i["minStateId"]] = {
            "maxStateId": i["maxStateId"],
            "name": i["name"],
            "tool": [j[len("mineable/"):] for j in i["material"].split(";") if j.startswith("mineable/")]
        }

user32 = ctypes.windll.user32 # Windows API for mouse input

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("_input", _INPUT),
    ]

def move_mouse_relative(dx: int, dy: int) -> None:
    ipt = INPUT(
        type=0, # input type for mouse
        mi=MOUSEINPUT(
            dx=dx,
            dy=dy,
            mouseData=0,
            dwFlags=0x0001,  # mouse move flag
            time=0,
            dwExtraInfo=None
        )
    )
    ctypes.windll.user32.SendInput(1, ctypes.byref(ipt), ctypes.sizeof(ipt))

def move(cmd: str) -> None:
    # ------------------------------------------------------------------------------------------------------------------------------
    # | TODO: 解析以下動作並執行之，如果能連續使用按鍵的話就不會放開，例如連續收到兩次"walk_W"時，中間不會放開w鍵                          |
    # |       - "jump"                                                  // 跳起                                                    |
    # |       - "sneak"                                                 // 蹲下，有其他動作後要自動解除                              |
    # |       - "place"                                                 // 在自己腳下放置方塊（跳起來然後放）                         |
    # |       - "walk_W", "sprint_W"                                    // 向 yaw = 0 的方向 [走, 跑] 前進                          |
    # |       - "walk_WA", "sprint_WA"                                  // 向 yaw = -45 的方向 [走, 跑] 前進                        |
    # |       - "walk_A", "sprint_A"                                    // 向 yaw = -90 的方向 [走, 跑] 前進                        |
    # |       - "walk_AS", "sprint_AS"                                  // 向 yaw = -135 的方向 [走, 跑] 前進                       |
    # |       - "walk_S", "sprint_S"                                    // 向 yaw = -180 的方向 [走, 跑] 前進                       |
    # |       - "walk_SD", "sprint_SD"                                  // 向 yaw = 135 的方向 [走, 跑] 前進                        |
    # |       - "walk_D", "sprint_D"                                    // 向 yaw = 90 的方向 [走, 跑] 前進                         |
    # |       - "walk_DW", "sprint_DW"                                  // 向 yaw = 45 的方向 [走, 跑] 前進                         |
    # |       - "break_U", "break_UF", "break_F", "break_DF", "break_D" // 選擇對應工具破壞 pitch = [-90, -45, 0, 45, 90] 瞄準的方塊 |
    # |       然後還要想辦法能選到對應工具，switch_tool(tool) 可以切過去那樣工具（如果快捷欄裡面有的話）                                 |
    # ------------------------------------------------------------------------------------------------------------------------------
    global status
    status = {
        "pressing_w": "w" in gv.pressed_key,
        "sprinting": gv.f3[gv.player_list[gv.info["agent_name"]]]["dv"] > WALK_SPEED,
        "sneaking": "shift" in gv.pressed_key
    }

    if cmd == "sneak":
        if not status["sneaking"]:
            if status["pressing_w"]:
                kb.release("w")
                status["pressing_w"] = False
                status["sprinting"] = False
            kb.press(Key.shift)
            status["sneaking"] = True
        if gv.f3[gv.player_list[gv.info["agent_name"]]]["hungry"] < 17:
            for i in gv.tool_num:
                if "cooked" in i:
                    switch_tool(i)
                    click_right(EAT_SPEED)
                    break
            else:
                CMD("I need cooked food!")
    else:
        if status["sneaking"]:
            kb.release(Key.shift)
            status["sneaking"] = False
        if cmd == "jump" or cmd == "place":
            jump()
            if cmd == "place":
                if status["pressing_w"]:
                    kb.release("w")
                    status["pressing_w"] = False
                    status["sprinting"] = False
                turn_down(TURN_45_DEG * 2)
                for i in gv.tool_num:
                    if not any(j in i for j in ("hoe", "shovel", "axe", "sword", "cooked")):
                        switch_tool(i)
                        for i in range(10):
                            #print("click")
                            click_right()
                            time.sleep(gv.TICK)
                        break
                else:
                    CMD("I need blocks to place!")
                turn_down(TURN_45_DEG * -2)
        elif cmd.startswith("sprint_") or cmd.startswith("walk_"):
            dir = [cmd[len("sprint_"):], cmd[len("walk_"):]][cmd[0] == "w"]
            if not status["pressing_w"]:
                kb.press("w")
                status["pressing_w"] = True
            if cmd.startswith("sprint_") and not status["sprinting"]:
                sprint()
                status["sprinting"] = True
            deg = gv.dir_deg[dir]
            turn_right(TURN_45_DEG * (deg // 45))
        elif cmd.startswith("break_"):
            if status["pressing_w"]:
                kb.release("w")
                status["pressing_w"] = False
                status["sprinting"] = False
            dir = cmd[len("break_"):]
            deg = gv.break_deg[dir]
            turn_down(TURN_45_DEG * (deg // 45))
            target = mc.get_block_min(gv.f3[gv.player_list[gv.info["agent_name"]]]["gaze"])
            print(f"Target block: {target}")
            tar_coor = gv.f3[gv.player_list[gv.info["agent_name"]]]["look"]
            if not mc.is_empty_block(target):
                for i in gv.tool_num:
                    if block_info[target]["tool"] and i in block_info[target]["tool"]:
                        switch_tool(i)
                        break
                mouse.press(Button.left)
                bef = gv.f3[gv.player_list[gv.info["agent_name"]]]["item"]
                while not mc.is_empty_block(mc.get_block(tar_coor[0], tar_coor[1], tar_coor[2])) and bef != gv.f3[gv.player_list[gv.info["agent_name"]]]["item"]:
                    time.sleep(gv.TICK)
                    bef = gv.f3[gv.player_list[gv.info["agent_name"]]]["item"]
                mouse.release(Button.left)
            turn_down(TURN_45_DEG * (deg // 45) * -1)

def move_sim(x: float, y: float, z: float, cmd: str) -> tuple[float, float, float, int]:
    # ----------------------------------------------------------------------------------------------------------------------------
    # | TODO: 解析上述動作，並回傳若執行後會到的座標，以及腳下方塊的block_state_id會變成什麼，可用 mc.get_block(x, y, z) 取得，y記得減1 |
    # ----------------------------------------------------------------------------------------------------------------------------
    # return next_x, next_y, next_z, block_state_id
    nx, ny, nz = x, y, z
    valid = True
    if cmd == "jump":
        ny += JUMP_HEIGHT
    elif cmd == "place":
        ny += JUMP_HEIGHT
        valid = mc.is_empty_block(x, y, z)
    elif cmd.startswith("walk_") or cmd.startswith("sprint_"):
        if cmd.startswith("walk_"):
            dir = cmd[len("walk_"):]
            speed = WALK_SPEED
        else:
            dir = cmd[len("sprint_"):]
            speed = SPRINT_SPEED
        nx += speed * math.cos(math.radians(gv.dir_deg[dir]))
        nz += speed * math.sin(math.radians(gv.dir_deg[dir]))
    elif cmd.startswith("break_"):
        dir = cmd[len("break_"):]
        valid = not mc.is_empty_block(mc.get_gaze_block(x, y, z, gv.f3[gv.player_list[gv.info["agent_name"]]]["yaw"], gv.break_deg[dir]))
    valid = valid and mc.is_empty_block(nx, ny, nz) and mc.is_empty_block(nx, ny + 1, nz)
    bid = mc.get_block(nx, ny - 1, nz)
    return nx, ny, nz, [-2, bid][valid]

def switch_tool(tool: str, t: float = gv.TICK) -> None:
    if tool in gv.tool_num:
        kb.press(str(gv.tool_num[tool]))
        time.sleep(t)
        kb.release(str(gv.tool_num[tool]))
    else:
        print(f"Tool '{tool}' not recognized. Available tools: {list(gv.tool_num.keys())}")

def jump(t: float = gv.TICK) -> None:
    kb.press(Key.space)
    time.sleep(t)
    kb.release(Key.space)

def sprint(t: float = gv.TICK) -> None:
    kb.press(Key.ctrl)
    time.sleep(t)
    kb.release(Key.ctrl)

def click_right(t: float = gv.TICK) -> None:
    mouse.press(Button.right)
    time.sleep(t)
    mouse.release(Button.right)

def turn_right(t: float, p: int = 15, s: float = 0.005) -> None:
    if t < 0:
        p = -p
        t = -t
    for _ in range(int(t / s)):
        move_mouse_relative(p, 0)
        time.sleep(s)

def turn_down(t: float, p: int = 15, s: float = 0.005) -> None:
    if t < 0:
        p = -p
        t = -t
    for _ in range(int(t / s)):
        move_mouse_relative(0, p)
        time.sleep(s)

def back_to_game(t: float = gv.TICK) -> None:
    kb.press(Key.esc)
    time.sleep(t)
    kb.release(Key.esc)

if __name__ == "__main__":
    print("Please start Minecraft and focus the game window.")
    one_block_time = 0.2317
    one_turn_time = 0.105
    while True:
        cmd = input("Enter command (jump/sneak/place/walk_X/sprint_X/break_X/exit): ")
        if cmd == "exit":
            break
        print("please click the Minecraft window, enter the game, and wait for 3 seconds.")
        time.sleep(3)
        move(cmd)