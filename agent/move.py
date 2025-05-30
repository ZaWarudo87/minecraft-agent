import time
import threading

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

def jump(t: float) -> None:
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

def turn_left(t: float, p: int = 5, s: float = 0.005) -> None:
    for _ in range(int(t / s)):
        mouse.move(-p, 0)
        time.sleep(s)

def turn_right(t: float, p: int = 5, s: float = 0.005) -> None:
    for _ in range(int(t / s)):
        mouse.move(p, 0)
        time.sleep(s)

def turn_up(t: float, p: int = 5, s: float = 0.005) -> None:
    for _ in range(int(t / s)):
        mouse.move(0, -p)
        time.sleep(s)

def turn_down(t: float, p: int = 5, s: float = 0.005) -> None:
    for _ in range(int(t / s)):
        mouse.move(0, p)
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