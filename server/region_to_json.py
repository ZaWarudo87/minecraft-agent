import anvil
import json
import os
import time

now_dir = os.path.dirname(__file__)
with open(os.path.join(now_dir, "../train/MCdata/blocks.json"), "r", encoding="utf-8") as f:
    fin = json.load(f)
    block_info = {i["name"]: i["minStateId"] for i in fin}

def process_region(region_path, blocks, info, skip_air=False):
    """Process a Minecraft region file and return all blocks"""
    print(f"Loading region file: {region_path}")
    
    try:
        region = anvil.Region.from_file(region_path)
    except Exception as e:
        print(f"Error loading region {region_path}: {e}")
        return
    
    # Extract region X and Z from filename (r.X.Z.mca)
    filename = os.path.basename(region_path)
    parts = filename.split('.')
    region_x = int(parts[1])
    region_z = int(parts[2])
    fout_name = os.path.join(now_dir, f"../world_cache/{info["server"]}_{info["port"]}_block_{region_x}_{region_z}.json")
    blocks = {}

    if os.path.exists(fout_name):
        print(f"Region {filename} already processed.")
        return
    
    # Calculate region offset in blocks
    region_x_offset = region_x * 512
    region_z_offset = region_z * 512
    
    # Iterate through all possible chunk positions within a region (32x32)
    for chunk_x in range(32):
        for chunk_z in range(32):
            try:
                # Try to load this chunk
                chunk = anvil.Chunk.from_region(region, chunk_x, chunk_z)
                print(f"Processing chunk ({chunk_x}, {chunk_z}) in region {filename}")
                
                # Calculate world coordinates
                world_x_base = region_x_offset + (chunk_x * 16)
                world_z_base = region_z_offset + (chunk_z * 16)
                
                # Scan all blocks in this chunk
                for local_x in range(16):
                    for local_z in range(16):
                        # Modern Minecraft height range
                        for y in range(-64, 320):
                            try:
                                block = chunk.get_block(local_x, y, local_z)
                                
                                # Skip air blocks if specified
                                if skip_air and (block.id == "minecraft:air" or block.id == "air"):
                                    continue
                                
                                # Calculate world coordinates
                                world_x = world_x_base + local_x
                                world_z = world_z_base + local_z
                                
                                if str(world_x) not in blocks:
                                    blocks[str(world_x)] = {}
                                if str(y) not in blocks[str(world_x)]:
                                    blocks[str(world_x)][str(y)] = {}
                                blocks[str(world_x)][str(y)][str(world_z)] = block_info[block.id]
                            except Exception as e:
                                # Skip blocks that can't be accessed
                                pass
            except Exception as e:
                # This chunk probably doesn't exist, skip it
                pass
    with open(fout_name, "w", encoding='utf-8') as f:
        json.dump(blocks, f)
    print(f"Found {len(blocks)} blocks in {region_path}")

if __name__ == "__main__":
    # Define the regions to process
    region_files = [
        'seed_region/r.0.0.mca',
        'seed_region/r.0.-1.mca', 
        'seed_region/r.-1.0.mca',
        'seed_region/r.-1.-1.mca'
    ]
    
    output_path = 'combined_regions.json'
    all_blocks = []
    processed_regions = []
    start_time = time.time()
    
    # Process each region file
    for region_path in region_files:
        if os.path.exists(region_path):
            blocks = process_region(region_path, skip_air=True)
            all_blocks.extend(blocks)
            processed_regions.append(os.path.basename(region_path))
            
            # Save intermediate results to avoid losing all data if there's an error
            intermediate_data = {
                "regions": processed_regions,
                "block_count": len(all_blocks),
                "blocks": all_blocks
            }
            
            intermediate_path = f"intermediate_{len(processed_regions)}_regions.json"
            with open(intermediate_path, 'w') as f:
                json.dump(intermediate_data, f)
            print(f"Saved intermediate result to {intermediate_path}")
        else:
            print(f"Warning: Region file {region_path} not found, skipping")
    
    # Create final output with metadata
    output_data = {
        "regions": processed_regions,
        "block_count": len(all_blocks),
        "processing_time_seconds": time.time() - start_time,
        "blocks": all_blocks
    }
    
    # Save to JSON file
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Saved {len(all_blocks)} blocks from {len(processed_regions)} regions to {output_path}")
    print(f"Processing completed in {time.time() - start_time:.1f} seconds")
    
    # Optional: Print a sample of blocks
    if all_blocks:
        print("\nSample blocks:")
        for block in all_blocks[:5]:  # Show first 5 blocks
            print(f"{block['id']} at ({block['x']}, {block['y']}, {block['z']})")