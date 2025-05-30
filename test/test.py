import pygetwindow as gw

# 檢查 Minecraft 是否在焦點視窗
active = gw.getWindowsWithTitle('Minecraft 1.18')
print(active[0].title)
print(active[0].isActive)

active[0].restore()  # 如果視窗被最小化，則恢復視窗
active[0].activate()  # 將 Minecraft 視窗設為焦點