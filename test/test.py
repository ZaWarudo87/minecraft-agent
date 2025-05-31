from rich.live import Live
from rich.table import Table
from rich.console import Console
import time

console = Console()

# 假設你的 f3 結構如下：
f3 = {
    "entity1": {"x": 0, "y": 0, "z": 0, "vx": 1, "vy": 0.5, "vz": -0.2, "yaw": 30, "pitch": 10},
    "entity2": {"x": 3, "y": 5, "z": 2, "vx": 0.3, "vy": -0.1, "vz": 0.4, "yaw": 60, "pitch": -15},
}

def generate_table():
    table = Table(title="Entity Coordinates")
    table.add_column("Entity", style="cyan")
    table.add_column("X")
    table.add_column("Y")
    table.add_column("Z")
    table.add_column("Yaw")
    table.add_column("Pitch")

    for k, v in f3.items():
        v["x"] += v["vx"]
        v["y"] += v["vy"]
        v["z"] += v["vz"]
        table.add_row(
            k,
            f"{v['x']:.2f}",
            f"{v['y']:.2f}",
            f"{v['z']:.2f}",
            f"{v['yaw']:.2f}",
            f"{v['pitch']:.2f}"
        )
    return table

with Live(generate_table(), refresh_per_second=10, screen=False) as live:
    while True:
        time.sleep(0.1)
        live.update(generate_table())
