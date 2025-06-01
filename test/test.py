dir = ["W", "WA", "A", "AS", "S", "SD", "D", "DW"]
act = ["jump", "sneak", "offset", "place"]
for i in dir:
    act.append(f"walk_{i}")
    act.append(f"sprint_{i}")
for i in ["U", "UF", "F", "DF", "D"]:
    act.append(f"break_{i}")

print(act)