import numpy as np
import json
import os
from shapely.geometry import Point
from collections import deque

def load_familiar_points_from_geojson(geojson_path):
    """
    从 GeoJSON 文件中读取熟悉点坐标
    
    Parameters:
    - geojson_path: GeoJSON 文件路径
    
    Returns:
    - List of tuples (x, y) representing point coordinates
    """
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    points = []
    for feature in geojson_data['features']:
        if feature['geometry']['type'] == 'Point':
            coords = feature['geometry']['coordinates']
            # 转换为整数坐标
            x = int(round(coords[0]))
            y = int(round(coords[1]))
            points.append((x, y))
    
    return points

def generate_attraction_matrix(
    m, n,
    attraction_points,  # 手动输入的高吸引力点列表 [(x, y, radius, attraction), ...]
    normalize=False,     # 是否归一化到 [0, 1]
    output_json=False    # 是否返回 JSON 格式
):
    """
    Generate an attraction matrix based on specified attraction points with radial influence.
    
    Parameters:
    - m, n: Dimensions of the output matrix (rows, columns)
    - attraction_points: List of tuples (x, y, radius, attraction_value)
    - normalize: Whether to normalize the matrix to [0, 1]
    - output_json: Whether to return the result as JSON
    
    Returns:
    - Either a numpy array or JSON string representing the attraction matrix
    """
    
    # 1. 初始化总体边界矩阵
    attraction_matrix = np.zeros((m, n))
    
    # 2. 计算每个网格点的吸引力
    for x, y, radius, attraction in attraction_points:
        # 确保坐标在矩阵范围内
        x = max(0, min(m-1, x))
        y = max(0, min(n-1, y))
        
        # 创建网格坐标
        rows, cols = np.indices((m, n))
        
        # 计算每个点到吸引力中心的距离
        distances = np.sqrt((rows - x)**2 + (cols - y)**2)
        
        # 应用高斯衰减函数 (在半径范围内)
        decay = np.exp(-(distances**2) / (2 * (radius/3)**2))  # radius/3 makes it fall to ~0.1 at radius
        influence = attraction * np.where(distances <= radius, decay, 0)
        
        # 叠加到总体矩阵
        attraction_matrix += influence
    
    # 3. 归一化（可选）
    if normalize:
        max_val = np.max(attraction_matrix)
        if max_val > 0:
            attraction_matrix = attraction_matrix / max_val
    
    # 4. 返回 JSON 或矩阵
    if output_json:
        json_data = {
            "macro_environment": {
                "map": attraction_matrix.flatten().tolist()  # 展平为 1D 数组
            }
        }
        return json.dumps(json_data, indent=2)
    else:
        return attraction_matrix

def generate_attraction_matrix_direct(
    m, n,
    attraction_points,  # [(x, y, radius, base_attraction)]
    decay_rate=0.8,     # 每层衰减比例 (0~1)
    normalize=False,
    output_json=True
):
    """
    通过广度优先搜索 (BFS) 实现逐层衰减的吸引力矩阵
    """
    attraction_matrix = np.zeros((m, n))
    
    for x, y, radius, base_attraction in attraction_points:
        x, y = int(np.clip(x, 0, m-1)), int(np.clip(y, 0, n-1))
        visited = np.zeros((m, n), dtype=bool)
        queue = deque()
        
        # 初始化中心点
        queue.append((x, y, base_attraction))
        visited[x, y] = True
        attraction_matrix[x, y] += base_attraction
        
        # BFS 向外扩散
        while queue:
            cx, cy, current_attraction = queue.popleft()
            
            # 遍历四个邻居方向
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                
                # 检查边界和是否已访问
                if 0 <= nx < m and 0 <= ny < n and not visited[nx, ny]:
                    distance = abs(nx - x) + abs(ny - y)  # 曼哈顿距离
                    if distance <= radius:
                        decayed_attraction = base_attraction * (decay_rate ** distance)
                        attraction_matrix[nx, ny] += decayed_attraction
                        visited[nx, ny] = True
                        queue.append((nx, ny, decayed_attraction))
    
    if normalize:
        max_val = np.max(attraction_matrix)
        if max_val > 0:
            attraction_matrix /= max_val
    
    if output_json:
        return {"macro_environment": {"map": attraction_matrix.flatten().tolist()}}  
    else:
        return attraction_matrix

# 示例调用
if __name__ == "__main__":
    # 设置矩阵维度
    m, n = 700, 700  
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # 从 data/env_data 回到项目根目录
    
    # 读取 transformed_familiar_point.geojson 文件
    geojson_path = os.path.join(project_root, "output", "transformed_familiar_point.geojson")
    
    try:
        # 加载熟悉点坐标
        familiar_points = load_familiar_points_from_geojson(geojson_path)
        print(f"成功加载 {len(familiar_points)} 个熟悉点:")
        for i, (x, y) in enumerate(familiar_points):
            print(f"  点 {i+1}: ({x}, {y})")
        
        # 将坐标转换为吸引力点格式 (x, y, radius, attraction)
        # 默认设置：半径为5，吸引力为80
        default_radius = 10
        default_attraction = 80
        
        attraction_points = []
        for x, y in familiar_points:
            attraction_points.append((x, y, default_radius, default_attraction))
        
        print(f"\n转换后的吸引力点:")
        for i, (x, y, r, a) in enumerate(attraction_points):
            print(f"  点 {i+1}: 坐标({x}, {y}), 半径={r}, 吸引力={a}")
        
        # 生成 JSON 格式的吸引力矩阵
        json_output = generate_attraction_matrix_direct(m, n, attraction_points)
        
        # 保存为 JSON 文件
        output_path = os.path.join(project_root, "env_data", "attraction_matrix_familiar_points.json")
        
        with open(output_path, "w") as f:
            json.dump(json_output, f, indent=4)
        
        print(f"\n熟悉点吸引力矩阵 JSON 文件已生成: {output_path}")
        print("文件大小:", len(json_output["macro_environment"]["map"]), "个数据点")
        
    except FileNotFoundError:
        print(f"错误: 找不到文件 {geojson_path}")
        print("请确保 transformed_familiar_point.geojson 文件存在于 data/output/ 目录中")
    except Exception as e:
        print(f"处理文件时出错: {e}")

    # 运行命令: python data/env_data/familiarity_map_generation_from_geojson.py
