"""
预处理脚本：将 familiarity map 归一化到 [0, 1] 范围
使用 log 归一化：f = log(raw + 1) / log(MAX_MAP + 1)
"""
import json
import math
from pathlib import Path

# 配置
INPUT_PATH = Path("data/env_data/attraction_matrix_familiar_points.json")
OUTPUT_PATH = Path("data/env_data/attraction_matrix_familiar_points_normalized.json")

print(f"读取原始 map 文件: {INPUT_PATH}")
with open(INPUT_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取 map 数组（在 macro_environment.map 下）
if "macro_environment" in data and "map" in data["macro_environment"]:
    raw_map = data["macro_environment"]["map"]
else:
    # 如果直接是数组
    raw_map = data if isinstance(data, list) else data.get("map", [])

print(f"原始 map 长度: {len(raw_map)}")
print(f"原始值范围: min={min(raw_map):.2f}, max={max(raw_map):.2f}")

# 自动获取最大值作为 MAX_MAP
MAX_MAP = max(raw_map)
print(f"自动检测到的 MAX_MAP = {MAX_MAP:.2f}")

# 应用 log 归一化
normalized_map = []
for val in raw_map:
    normalized_val = math.log(val + 1.0) / math.log(MAX_MAP + 1.0)
    normalized_map.append(normalized_val)

print(f"归一化后值范围: min={min(normalized_map):.6f}, max={max(normalized_map):.6f}")

# 保存归一化后的 map（保持原始 JSON 结构）
output_data = {
    "macro_environment": {
        "map": normalized_map
    }
}

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output_data, f)

print(f"归一化完成！已保存到: {OUTPUT_PATH}")
print(f"   原始值范围 [0, {MAX_MAP}] -> 归一化后范围 [0, 1]")

