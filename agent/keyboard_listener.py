import time
import tkinter as tk
from pynput import keyboard, mouse

pressed_key = set()
gui = {}
key_set = {
    "w", "a", "s", "d",
    "1", "2", "3", "4", "5", "6",
    "space", "shift", "ctrl",
    "mouse_left", "mouse_right"
}
layout = [
    [     "", "1", "2", "3", "4", "5",    "6"],
    ["shift",  "",  "", "w",  "",  "",   "ml",   "mr"],
    [ "ctrl",  "", "a", "s", "d",  "", "[__]", "(0, 0)"]
]
bef_mouse = {"x": 0, "y": 0}

def get_key(key) -> str:
    try:
        k = key.char.lower()
    except AttributeError:
        k = str(key).replace('Key.', '')
        if k == 'ctrl_l' or k == 'ctrl_r':
            k = 'ctrl'
        elif k == 'shift_l' or k == 'shift_r':
            k = 'shift'
    return k

def on_press(key: keyboard.Key) -> None:
    k = get_key(key)
    if k in key_set:
        pressed_key.add(k)
        gui[k].config(bg="green")

def on_release(key: keyboard.Key) -> None:
    k = get_key(key)
    if k in pressed_key:
        pressed_key.remove(k)
        gui[k].config(bg="lightgray")

def on_click(x, y, button, pressed) -> None:
    k = [["", "mouse_right"][button == mouse.Button.right], "mouse_left"][button == mouse.Button.left]
    if k in key_set:
        if pressed:
            pressed_key.add(k)
            gui[k].config(bg="green")
        else:
            pressed_key.discard(k)
            gui[k].config(bg="lightgray")

def on_move(x, y) -> None:
    gui["mouse_move"].config(text=f"({x - bef_mouse["x"]}, {y - bef_mouse['y']})")
    bef_mouse["x"] = x
    bef_mouse["y"] = y

def game_test() -> bool:
    time.sleep(0.5)
    test_mouse = mouse.Controller()
    befx, befy = test_mouse.position
    test_mouse.move(100, 100)
    return abs(test_mouse.position[0] - befx) < 10 and abs(test_mouse.position[1] - befy) < 10

def kb_listen() -> None:
    screen = tk.Tk()
    screen.title("Keyboard Listener")
    screen.geometry("700x200")
    screen.resizable(True, True)
    frame = tk.Frame(screen)
    frame.pack(expand=True)

    for row, row_keys in enumerate(layout):
        for col, key in enumerate(row_keys):
            if key:
                lbl = tk.Label(frame, text=key.upper(), width=6, height=2, font=("Arial", 14), bg="lightgray")
                lbl.grid(row=row, column=col, padx=5, pady=5)
                gui[[[[[key, "mouse_move"][key == "(0, 0)"], "space"][key == "[__]"], "mouse_right"][key == "mr"], "mouse_left"][key == "ml"]] = lbl
            else:
                tk.Label(frame, text="", width=6, height=2).grid(row=row, column=col, padx=5, pady=5)

    keyboard.Listener(on_press=on_press, on_release=on_release).start()
    mouse.Listener(on_click=on_click, on_move=on_move).start()
    screen.mainloop()

if __name__ == "__main__":
    kb_listen()