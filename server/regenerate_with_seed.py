import os
import shutil
import nbtlib
import subprocess
import time
import argparse
import json

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from minecraft.authentication import AuthenticationToken
from minecraft.networking.connection import Connection
from minecraft.networking.packets import Packet, DisconnectPacket

from region_to_json import *

#python regenerate_with_seed.py --seed "your_seed_here"

# Parse command line arguments
parser = argparse.ArgumentParser(description='Regenerate Minecraft world with a specific seed')
parser.add_argument('--seed', type=int, default=0, help='Seed value for world generation')
args = parser.parse_args()

# Use the seed from arguments
SEED = args.seed

PATH=os.path.join("world", "level.dat")
if not os.path.exists(PATH):
    print("World not found. Generating a new world...")
    server_process = subprocess.Popen(["java", "-Xmx2G", "-Xms1G", "-jar", "server.jar", "nogui"],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)

    # Wait for world generation (looking for "Done" message would be better)
    line = ""
    while "Done" not in line:
        line = server_process.stdout.readline()
        print(line.strip())
        time.sleep(1)  # Adjust time based on your hardware
    
    # Send stop command and wait for termination
    server_process.communicate(input="stop\n")
    print("World generated successfully.")

level_dat = nbtlib.load(PATH)
level_dat["Data"]["WorldGenSettings"]["seed"] = nbtlib.tag.Long(SEED)
level_dat["Data"]["WorldGenSettings"]["dimensions"]["minecraft:overworld"]["generator"]["seed"] = nbtlib.tag.Long(SEED)
level_dat["Data"]["WorldGenSettings"]["dimensions"]["minecraft:the_end"]["generator"]["seed"] = nbtlib.tag.Long(SEED)
level_dat["Data"]["WorldGenSettings"]["dimensions"]["minecraft:the_end"]["generator"]["biome_source"]["seed"] = nbtlib.tag.Long(SEED)
level_dat["Data"]["WorldGenSettings"]["dimensions"]["minecraft:the_nether"]["generator"]["seed"] = nbtlib.tag.Long(SEED)
level_dat.save()
print("new seed set to", SEED)
for file in os.listdir("world"):
    if file != "level.dat":
        file_path = os.path.join("world", file)
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
            print(f"Deleted directory: {file_path}")
        else:
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
print("All files except level.dat have been deleted.")
print("Starting server to generate world with new seed...")
server_process = server_process = subprocess.Popen(["java", "-Xmx2G", "-Xms1G", "-jar", "server.jar", "nogui"],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)

line = ""
while "Done" not in line:
    line = server_process.stdout.readline()
    print(line.strip())
    time.sleep(1)
print("World generation complete.")

def handle_disconnect(pkt: Packet) -> None:
    print(f"Disconnected from server: {pkt.reason}")

def handle_exception(pkt: Packet) -> None:
    print(f"Exception occurred: {pkt.exception}")

now_dir = os.path.dirname(__file__)
with open(os.path.join(now_dir, "../agent/login/info.json"), "r", encoding="utf-8") as f:
    info = json.load(f)
token = AuthenticationToken(info["username"], info["access_token"], " ")
token.profile.name = info["username"]
token.profile.id_ = info["id"]
conn = Connection("localhost", 25565, username=info["username"], auth_token=token)
conn.connect()
conn.register_packet_listener(handle_disconnect, DisconnectPacket)
conn.exception_handler = handle_exception
print(f"Connecting to server localhost:25565 as {info['username']}...")

regional_path = os.path.join("world", "region") 
region_files = os.listdir(regional_path)

#all_blocks = {}
#processed_regions = []
start_time = time.time()

# Process each region file
for region_path in region_files:
    region_path = os.path.join(regional_path, region_path)  # Ensure full path
    if os.path.exists(region_path):
        process_region(region_path, info)
    else:
        print(f"Warning: Region file {region_path} not found, skipping")

#print(f"Saved {len(all_blocks)} blocks from {len(processed_regions)} regions")
print(f"Processing completed in {time.time() - start_time:.1f} seconds")

class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            event_path = os.path.join(regional_path, event.src_path)
            print(f"New file detected: {event_path}")
            process_region(event_path, info)

    def on_modified(self, event):
        if not event.is_directory:
            event_path = os.path.join(regional_path, event.src_path)
            print(f"File modified: {event_path}")
            process_region(event_path, info)

observer = Observer()
observer.schedule(NewFileHandler(), path=regional_path, recursive=False)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
    conn.disconnect()
    server_process.communicate(input="stop\n")
    print("ctrl+c")

# seed_region_path = "seed_region"
# if os.path.exists(seed_region_path):
#     if os.path.isdir(seed_region_path):
#         shutil.rmtree(seed_region_path)
#     else:
#         os.remove(seed_region_path)

# if os.path.exists(region_path):
#     shutil.move(region_path, seed_region_path)
#     print(f"Moved {region_path} to {seed_region_path}")
# else:
#     print(f"{region_path} does not exist, nothing to move")

# print("start to clean up")
# for directory in ["libraries", "logs", "versions", "world"]:
#     if os.path.exists(directory):
#         shutil.rmtree(directory)
#         print(f"Deleted directory: {directory}")
# for json_file in os.listdir("."):
#     if json_file.endswith(".json"):
#         os.remove(json_file)
#         print(f"Deleted file: {json_file}")
# print("Cleanup complete. All unnecessary files and directories have been removed.")
# print("the region folder is now in", seed_region_path)
