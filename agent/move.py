import ctypes
import time

from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController

kb = KeyboardController()
mouse = MouseController()
tool_num = {
    "sword": 1,
    "axe": 2,
    "pickaxe": 3,
    "shovel": 4,
    "hoe": 5,
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

def switch_tool(tool: str, t: float = 0.1) -> None:
    if tool in tool_num:
        kb.press(str(tool_num[tool]))
        time.sleep(t)
        kb.release(str(tool_num[tool]))
    else:
        print(f"Tool '{tool}' not recognized. Available tools: {list(tool_num.keys())}")

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