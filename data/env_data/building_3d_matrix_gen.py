import numpy as np
import json
import os

def load_buildings_from_geojson(filepath):
    """
    从GeoJSON文件中加载建筑物数据
    返回建筑物列表，每个建筑物包含其坐标点
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    buildings = []

    for feature in data['features']:
        # 获取建筑物坐标
        coordinates = feature['geometry']['coordinates'][0]  # 多边形的外环
        # 转换为整数坐标
        building_points = []
        for coord in coordinates:
            # 取整坐标
            x, y = int(round(coord[0])), int(round(coord[1]))
            building_points.append([x, y])

        # 移除最后一个重复的点（GeoJSON中多边形首尾相连）
        if building_points and building_points[0] == building_points[-1]:
            building_points.pop()

        buildings.append(np.array(building_points))

    return buildings

def create_building_3d_matrix(buildings, max_points_per_building=None):
    """
    从建筑物列表创建3D矩阵
    buildings: 建筑物列表，每个元素是numpy数组
    max_points_per_building: 每个建筑物的最大点数，如果为None则使用最大建筑物点数
    """
    n = len(buildings)  # 建筑物数量

    if max_points_per_building is None:
        m = max(len(building) for building in buildings)  # 最大点数
    else:
        m = max_points_per_building

    # 创建3D数组：n个建筑物，m个点位，每个点有2个坐标(x,y)
    map_3d = np.zeros((n, m, 2), dtype=int)

    # 将建筑物数据填充到3D数组中
    for building_idx, building in enumerate(buildings):
        for point_idx, point in enumerate(building):
            if point_idx < m:
                map_3d[building_idx][point_idx] = point

    return map_3d

# 主程序
if __name__ == "__main__":
    # 从GeoJSON文件加载建筑物数据
    geojson_path = os.path.join("..", "output", "transformed_buildings.geojson")
    buildings = load_buildings_from_geojson(geojson_path)

    print(f"加载了 {len(buildings)} 个建筑物")
    for i, building in enumerate(buildings):
        print(f"建筑物 {i}: {len(building)} 个点")

    # 创建3D矩阵（固定最大点位为20）
    map_3d = create_building_3d_matrix(buildings, max_points_per_building=20)

    # 按行优先顺序展平3D数组
    flattened_map = map_3d.flatten(order='C')  # 'C'表示行优先（C风格）

    # 创建JSON结构
    result = {
        "macro_environment": {
            "map_3d": flattened_map.tolist()
        }
    }

    # 输出JSON
    print("\n生成的JSON结构:")
    print(json.dumps(result, indent=2))

    with open('map_3d.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("\n验证信息:")
    print(f"原始3D数组形状: {map_3d.shape}")
    print(f"展平后数组长度: {len(flattened_map)}")
    print(f"前几个值: {flattened_map[:20]}")
    print(f"建筑物信息已保存到 map_3d.json")