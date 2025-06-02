"""
TODO
- 完成 move(cmd)
- 切視角請用 move_mouse_relative(dx, dy)，這邊不能用 MouseController，只有點擊時才行
- switch_tool(tool) 可以切過去快捷欄裡面有的指定工具
- 不建議直接拿 move 系列的函式使用
- 經過實測，move_forward(0.2317) 可以往前走接近剛好一格，turn_right(0.105) 可以剛好把頭右轉接近45度
"""

import ctypes
import time

from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController

from . import mc

kb = KeyboardController()
mouse = MouseController()
tool_num = {}
WALK_1_BLOCK = 0.2317
TURN_45_DEG = 0.105

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
    global _current_keys, _current_sprinting, _sneaking

    cmd = cmd.strip()

    # 1) "jump"：先放開所有移動鍵與 sneaking，再執行跳
    if cmd == "jump":
        for k in list(_current_keys):
            kb.release(k)
        _current_keys.clear()
        if _current_sprinting:
            kb.release(Key.ctrl)
            _current_sprinting = False
        if _sneaking:
            kb.release(Key.shift)
            _sneaking = False
        kb.press(Key.space)
        time.sleep(0.1)
        kb.release(Key.space)
        return

    # 2) "sneak"：先放開移動鍵與 sprint，然後按住 Shift
    if cmd == "sneak":
        for k in list(_current_keys):
            kb.release(k)
        _current_keys.clear()
        if _current_sprinting:
            kb.release(Key.ctrl)
            _current_sprinting = False
        if _sneaking:
            kb.release(Key.shift)
            time.sleep(0.02)
        kb.press(Key.shift)
        _sneaking = True
        return

    # 3) "place"：先放開所有移動鍵與 sneaking，跳一下再右鍵放置
    if cmd == "place":
        for k in list(_current_keys):
            kb.release(k)
        _current_keys.clear()
        if _current_sprinting:
            kb.release(Key.ctrl)
            _current_sprinting = False
        if _sneaking:
            kb.release(Key.shift)
            _sneaking = False
        kb.press(Key.space)
        time.sleep(0.1)
        kb.release(Key.space)
        mouse.press(Button.right)
        time.sleep(0.1)
        mouse.release(Button.right)
        return

    # 4) "walk_X" 或 "sprint_X"
    is_sprint = False
    direction = None
    if cmd.startswith("sprint_"):
        is_sprint = True
        direction = cmd[len("sprint_"):]
    elif cmd.startswith("walk_"):
        is_sprint = False
        direction = cmd[len("walk_"):]
    else:
        direction = None

    if direction is not None:
        if _sneaking:
            kb.release(Key.shift)
            _sneaking = False
        if is_sprint and not _current_sprinting:
            kb.press(Key.ctrl)
            _current_sprinting = True
            time.sleep(0.02)
        if (not is_sprint) and _current_sprinting:
            kb.release(Key.ctrl)
            _current_sprinting = False
            time.sleep(0.02)

        wanted_keys = set()
        for ch in direction:
            if ch == "W":
                wanted_keys.add("w")
            elif ch == "A":
                wanted_keys.add("a")
            elif ch == "S":
                wanted_keys.add("s")
            elif ch == "D":
                wanted_keys.add("d")

        for k in list(_current_keys):
            if k not in wanted_keys:
                kb.release(k)
                _current_keys.remove(k)
                time.sleep(0.01)
        for k in wanted_keys:
            if k not in _current_keys:
                kb.press(k)
                _current_keys.add(k)
                time.sleep(0.01)
        return

    # 5) "break_*"
    if cmd.startswith("break_"):
        for k in list(_current_keys):
            kb.release(k)
        _current_keys.clear()
        if _current_sprinting:
            kb.release(Key.ctrl)
            _current_sprinting = False
        if _sneaking:
            kb.release(Key.shift)
            _sneaking = False

        parts = cmd.split("_", 1)
        if len(parts) == 2:
            pitch_code = parts[1]
            # switch_tool("pickaxe")
            if pitch_code == "U":
                turn_up(TURN_45_DEG * 2)
            elif pitch_code == "UF":
                turn_up(TURN_45_DEG)
            elif pitch_code == "F":
                pass
            elif pitch_code == "DF":
                turn_down(TURN_45_DEG)
            elif pitch_code == "D":
                turn_down(TURN_45_DEG * 2)

            time.sleep(0.05)
            mouse.press(Button.left)
            time.sleep(0.15)
            mouse.release(Button.left)

            if pitch_code == "U":
                turn_down(TURN_45_DEG * 2)
            elif pitch_code == "UF":
                turn_down(TURN_45_DEG)
            elif pitch_code == "DF":
                turn_up(TURN_45_DEG)
            elif pitch_code == "D":
                turn_up(TURN_45_DEG * 2)
        return

    # 6) 其他：停止所有移動與 sneaking
    for k in list(_current_keys):
        kb.release(k)
    _current_keys.clear()
    if _current_sprinting:
        kb.release(Key.ctrl)
        _current_sprinting = False
    if _sneaking:
        kb.release(Key.shift)
        _sneaking = False
    return NotImplementedError

def move_sim(x: float, y: float, z: float, cmd: str) -> tuple[float, float, float, int]:
    # ----------------------------------------------------------------------------------------------------------------------------
    # | TODO: 解析上述動作，並回傳若執行後會到的座標，以及腳下方塊的block_state_id會變成什麼，可用 mc.get_block(x, y, z) 取得，y記得減1 |
    # ----------------------------------------------------------------------------------------------------------------------------
    # return next_x, next_y, next_z, block_state_id
    cmd = cmd.strip()

    # 1) "jump"
    if cmd == "jump":
        next_x, next_y, next_z = x, y + 1, z
        block_id = mc.get_block(x, y - 1, z)
        return next_x, next_y, next_z, block_id

    # 2) "sneak"
    if cmd == "sneak":
        block_id = mc.get_block(x, y - 1, z)
        return x, y, z, block_id

    # 3) "place"
    if cmd == "place":
        placed_block_id = 1
        try:
            mc.set_block(x, y - 1, z, placed_block_id)
        except AttributeError:
            pass
        return x, y, z, placed_block_id

    # 4) "walk_X" 或 "sprint_X"
    direction = None
    if cmd.startswith("walk_"):
        direction = cmd[len("walk_"):]
    elif cmd.startswith("sprint_"):
        direction = cmd[len("sprint_"):]

    if direction is not None:
        if direction == "W":
            dx, dz = 0, 1
        elif direction == "WA":
            dx, dz = -1, 1
        elif direction == "A":
            dx, dz = -1, 0
        elif direction == "AS":
            dx, dz = -1, -1
        elif direction == "S":
            dx, dz = 0, -1
        elif direction == "SD":
            dx, dz = 1, -1
        elif direction == "D":
            dx, dz = 1, 0
        elif direction == "DW":
            dx, dz = 1, 1
        else:
            return NotImplementedError

        if abs(dx) == 1 and abs(dz) == 1:
            length = (2 ** 0.5)
            ndx = dx / length
            ndz = dz / length
        else:
            ndx = dx
            ndz = dz

        next_x = x + ndx
        next_y = y
        next_z = z + ndz
        block_id = mc.get_block(next_x, next_y - 1, next_z)
        return next_x, next_y, next_z, block_id

    # 5) "break_*"
    if cmd.startswith("break_"):
        block_id = mc.get_block(x, y - 1, z)
        return x, y, z, block_id

    # 6) 其他
    return NotImplementedError

def switch_tool(tool: str, t: float = 0.1) -> None:
    if tool in tool_num:
        kb.press(str(tool_num[tool]))
        time.sleep(t)
        kb.release(str(tool_num[tool]))
    else:
        print(f"Tool '{tool}' not recognized. Available tools: {list(tool_num.keys())}")

def move_forward(t: float) -> None:
    kb.press("w")
    time.sleep(t)
    kb.release("w")

def move_backward(t: float) -> None:
    kb.press("s")
    time.sleep(t)
    kb.release("s")

def move_left(t: float) -> None:
    kb.press("a")
    time.sleep(t)
    kb.release("a")

def move_right(t: float) -> None:
    kb.press("d")
    time.sleep(t)
    kb.release("d")

def jump(t: float = 0.1) -> None:
    kb.press(Key.space)
    time.sleep(t)
    kb.release(Key.space)

def sneak(t: float) -> None:
    kb.press(Key.shift)
    time.sleep(t)
    kb.release(Key.shift)

def sprint(t: float = 0.1) -> None:
    kb.press(Key.ctrl)
    time.sleep(t)
    kb.release(Key.ctrl)

def click_left(t: float = 0.1) -> None:
    mouse.press(Button.left)
    time.sleep(t)
    mouse.release(Button.left)

def click_right(t: float = 0.1) -> None:
    mouse.press(Button.right)
    time.sleep(t)
    mouse.release(Button.right)

def turn_left(t: float, p: int = 15, s: float = 0.005) -> None:
    for _ in range(int(t / s)):
        move_mouse_relative(-p, 0)
        time.sleep(s)

def turn_right(t: float, p: int = 15, s: float = 0.005) -> None:
    for _ in range(int(t / s)):
        move_mouse_relative(p, 0)
        time.sleep(s)

def turn_up(t: float, p: int = 15, s: float = 0.005) -> None:
    for _ in range(int(t / s)):
        move_mouse_relative(0, -p)
        time.sleep(s)

def turn_down(t: float, p: int = 15, s: float = 0.005) -> None:
    for _ in range(int(t / s)):
        move_mouse_relative(0, p)
        time.sleep(s)

def attack(t: float = 0.1) -> None:
    switch_tool("sword")
    click_left(t)

def back_to_game(t: float = 0.1) -> None:
    kb.press(Key.esc)
    time.sleep(t)
    kb.release(Key.esc)

if __name__ == "__main__":
    print("Please start Minecraft and focus the game window.")
    one_block_time = 0.2317
    one_turn_time = 0.105
    while True:
        cmd = input("Enter command (jump/sneak/place/walk_X/sprint_X/break_X/exit): ").strip().lower()
        print("please click the Minecraft window, enter the game, and wait for 3 seconds.")
        time.sleep(3)
        move(cmd)

    while True:
        command = input("Enter command (w/a/s/d/jump/sneak/turn/dig/exit): ").strip().lower()
        if command == "w":
            time.sleep(1)
            print("Moving forward for 1m...")
            move_forward(one_block_time)
        elif command == "a":
            time.sleep(1)
            print("Moving left for 1m...")
            move_left(one_block_time)
        elif command == "s":
            time.sleep(1)
            print("Moving backward for 1m...")
            move_backward(one_block_time)
        elif command == "d":
            time.sleep(1)
            print("Moving right for 1m...")
            move_right(one_block_time)
        elif command == "jump":
            time.sleep(1)
            print("Jumping...")
            jump()
        elif command == "sneak":
            time.sleep(1)
            print("Greeting...")
            sneak(0.2)
            time.sleep(0.2)
            sneak(0.2)
        elif command == "turn":
            time.sleep(1)
            print(f"Turning right...")
            turn_right(one_turn_time)
        elif command == "dig":
            time.sleep(1)
            print("Digging...")
            click_left(5)
        elif command == "exit":
            print("Exiting...")
            break