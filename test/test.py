from minecraft_data.v1_20 import blocks, entities

# 所有方塊 ID 與名稱
block_ids = blocks.blocks_by_id
block_names = blocks.blocks_by_name

# 所有實體 ID 與名稱
entity_ids = entities.entities_by_id
entity_names = entities.entities_by_name

print(block_names.keys())   # 印出所有可識別的方塊名稱
print(entity_names.keys())  # 印出所有可識別的生物名稱
