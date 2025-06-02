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
