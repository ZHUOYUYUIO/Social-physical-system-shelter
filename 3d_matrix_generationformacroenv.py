import numpy as np
import json

# 定义建筑物数据
obstacle1 = np.array([
    [2, 2],
    [4, 2],
    [4, 4],
    [2, 4]
])

obstacle2 = np.array([
    [6, 1],
    [8, 1],
    [9, 2],
    [8, 3],
    [6, 3],
    [5, 2]
])

obstacle3 = np.array([
    [3, 6],
    [5, 6],
    [6, 7],
    [5, 8],
    [3, 8],
    [2, 7]
])

# 设置数组维度：n=3个建筑物，m=20个点位，每个点有2个坐标(x,y)
n = 3
m = 20
map_3d = np.zeros((n, m, 2), dtype=int)

# 将建筑物数据填充到3D数组中
# 第一个建筑物 (4个点)
for i, point in enumerate(obstacle1):
    if i < m:
        map_3d[0][i] = point

# 第二个建筑物 (6个点)
for i, point in enumerate(obstacle2):
    if i < m:
        map_3d[1][i] = point

# 第三个建筑物 (6个点)
for i, point in enumerate(obstacle3):
    if i < m:
        map_3d[2][i] = point

# 按行优先顺序展平3D数组
flattened_map = map_3d.flatten(order='C')  # 'C'表示行优先（C风格）

# 创建JSON结构
result = {
    "macro_environment": {
        "map_3d": flattened_map.tolist()
    }
}

# 输出JSON
print(json.dumps(result, indent=2))

with open('map_3d.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

# 验证展平顺序（可选）
print("\n验证展平顺序:")
print("原始3D数组形状:", map_3d.shape)
print("展平后数组长度:", len(flattened_map))
print("前几个值:", flattened_map[:10])