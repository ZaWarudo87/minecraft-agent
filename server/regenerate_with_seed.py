import os
import shutil
import nbtlib
import subprocess
import time
import argparse

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
    time.sleep(60)  # Adjust time based on your hardware
    
    # Send stop command and wait for termination
    server_process.communicate(input="stop\n")
    print("World generated successfully.")

level_dat = nbtlib.load(PATH)
level_dat["Data"]["WorldGenSettings"]["seed"] = nbtlib.tag.Long(SEED)
level_dat.save()
print("new seed set to", SEED)
dim1_path = os.path.join("world", "DIM1")
if os.path.exists(dim1_path):
    shutil.rmtree(dim1_path)
    print(f"Deleted {dim1_path}")
dim_1_path = os.path.join("world", "DIM-1")
if os.path.exists(dim_1_path):
    shutil.rmtree(dim_1_path)
    print(f"Deleted {dim_1_path}")
region_path = os.path.join("world", "region")
if os.path.exists(region_path):
    shutil.rmtree(region_path)
    print(f"Deleted {region_path}")
level_dat_old_path = os.path.join("world", "level.dat_old")
if os.path.exists(level_dat_old_path):
    os.remove(level_dat_old_path)
    print(f"Deleted {level_dat_old_path}")
print("generating new world with seed", SEED)
server_process = subprocess.Popen(["java", "-Xmx2G", "-Xms1G", "-jar", "server.jar", "nogui"],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)
time.sleep(60)
server_process.communicate(input="stop\n")
print("World generation complete.")

region_path = os.path.join("world", "region") 
seed_region_path = "seed_region"
if os.path.exists(seed_region_path):
    if os.path.isdir(seed_region_path):
        shutil.rmtree(seed_region_path)
    else:
        os.remove(seed_region_path)

if os.path.exists(region_path):
    shutil.move(region_path, seed_region_path)
    print(f"Moved {region_path} to {seed_region_path}")
else:
    print(f"{region_path} does not exist, nothing to move")

print("start to clean up")
for directory in ["libraries", "logs", "versions", "world"]:
    if os.path.exists(directory):
        shutil.rmtree(directory)
        print(f"Deleted directory: {directory}")
for json_file in os.listdir("."):
    if json_file.endswith(".json"):
        os.remove(json_file)
        print(f"Deleted file: {json_file}")
print("Cleanup complete. All unnecessary files and directories have been removed.")
print("the region folder is now in", seed_region_path)