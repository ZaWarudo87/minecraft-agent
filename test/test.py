import tkinter as tk
from pynput import keyboard, mouse

# 追蹤目前按下的鍵
pressed_keys = set()

# 追蹤 GUI 元件
key_widgets = {}

# 你想追蹤的鍵
keys_to_track = {
    'w', 'a', 's', 'd',
    '1','2','3','4','5','6','7','8','9',
    'space', 'shift', 'ctrl',
    'mouse_left', 'mouse_right'
}

layout = [
    [    '1', '2', '3', '4', '5', '6',          '7',           '8', '9'],
    ['shift',  '',  '', 'w',  '',  '', 'mouse_left', 'mouse_right'],
    [ 'ctrl',  '', 'a', 's', 'd',  '',      'space']
]

# GUI 初始化
root = tk.Tk()
root.title("鍵盤顯示器")
root.geometry("800x200")
root.resizable(True, True)

frame = tk.Frame(root)
frame.pack(expand=True)

# 建立按鍵 label（初始顯示為放開）
def create_key_label(key, row, col):
    if key:
        lbl = tk.Label(frame, text=key.upper(), width=6, height=2, font=('Arial', 14), bg='lightgray')
        lbl.grid(row=row, column=col, padx=5, pady=5)
        key_widgets[key] = lbl
    else:
        tk.Label(frame, text='', width=6, height=2).grid(row=row, column=col, padx=5, pady=5)

for row_idx, row_keys in enumerate(layout):
    for col_idx, key in enumerate(row_keys):
        create_key_label(key, row_idx, col_idx)

# 更新 GUI 顏色
def update_key_color(key, pressed):
    if key in key_widgets:
        key_widgets[key]['bg'] = 'green' if pressed else 'lightgray'

# 處理鍵盤按下事件
def on_press(key):
    try:
        k = key.char.lower()
    except AttributeError:
        k = str(key).replace('Key.', '')
    if k == 'ctrl_l' or k == 'ctrl_r':
        k = 'ctrl'
    elif k == 'shift':
        k = 'shift'
    elif k == 'space':
        k = 'space'

    if k in keys_to_track and k not in pressed_keys:
        pressed_keys.add(k)
        update_key_color(k, True)

# 處理鍵盤放開事件
def on_release(key):
    try:
        k = key.char.lower()
    except AttributeError:
        k = str(key).replace('Key.', '')
    if k == 'ctrl_l' or k == 'ctrl_r':
        k = 'ctrl'
    elif k == 'shift':
        k = 'shift'
    elif k == 'space':
        k = 'space'

    if k in pressed_keys:
        pressed_keys.remove(k)
        update_key_color(k, False)

# 滑鼠事件
def on_click(x, y, button, pressed):
    k = ''
    if button == mouse.Button.left:
        k = 'mouse_left'
    elif button == mouse.Button.right:
        k = 'mouse_right'
    
    if k in keys_to_track:
        if pressed:
            pressed_keys.add(k)
        else:
            pressed_keys.discard(k)
        update_key_color(k, pressed)

# 啟動鍵盤與滑鼠監聽
keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
mouse_listener = mouse.Listener(on_click=on_click)
keyboard_listener.start()
mouse_listener.start()

# 啟動 GUI 主迴圈
root.mainloop()