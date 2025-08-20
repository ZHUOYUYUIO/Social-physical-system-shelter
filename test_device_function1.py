import math
import numpy as np


def find_path_ultra_consolidated(start, end, obstacles):
    """

    将大部分逻辑都整合在一个函数中，希望这对我们的单一agent函数有用。看看是放在agent里还是device function里。
    
    输入: start - 起点坐标, end - 终点坐标, obstacles - 障碍物矩阵列表 n times 2的矩阵存储障碍物的点位
    输出: float数组 - 路径坐标数组 [x1, y1, x2, y2, ...]
    """
    
    # =================================================================
    # 1. 处理起点在障碍物内部的情况
    # =================================================================
    actual_start = start
    inside_obstacle = None
    
    # 检查起点是否在任何障碍物内部
    for obstacle in obstacles:
        # 将矩阵转换为点列表
        polygon = []
        for i in range(obstacle.shape[0]):
            polygon.append((obstacle[i, 0], obstacle[i, 1]))
        
        # 使用射线法判断点是否在多边形内部
        x, y = start
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        if inside:
            inside_obstacle = obstacle
            break
    
    # 如果起点在障碍物内部，找到最近的出口点
    if inside_obstacle is not None:
        polygon = []
        for i in range(inside_obstacle.shape[0]):
            polygon.append((inside_obstacle[i, 0], inside_obstacle[i, 1]))
        
        min_distance = float('inf')
        best_exit = start
        
        n = len(polygon)
        for i in range(n):
            p1 = polygon[i]
            p2 = polygon[(i + 1) % n]
            
            # 计算点到线段的最短距离和投影点
            x, y = start
            x1, y1 = p1
            x2, y2 = p2
            
            line_len_sq = (x2 - x1)**2 + (y2 - y1)**2
            
            if line_len_sq == 0:
                exit_point = p1
            else:
                t = max(0, min(1, ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / line_len_sq))
                proj_x = x1 + t * (x2 - x1)
                proj_y = y1 + t * (y2 - y1)
                exit_point = (proj_x, proj_y)
            
            dist = math.sqrt((start[0] - exit_point[0])**2 + (start[1] - exit_point[1])**2)
            
            if dist < min_distance:
                min_distance = dist
                
                # 计算边的法向量（向外）
                edge_vector = (p2[0] - p1[0], p2[1] - p1[1])
                # 逆时针旋转90度得到外法向量
                normal = (-edge_vector[1], edge_vector[0])
                normal_len = math.sqrt(normal[0]**2 + normal[1]**2)
                
                if normal_len > 0:
                    normal = (normal[0]/normal_len, normal[1]/normal_len)
                    # 检查法向量方向是否正确（应该指向多边形外部）
                    test_point = (exit_point[0] + normal[0] * 0.1, exit_point[1] + normal[1] * 0.1)
                    
                    # 检查测试点是否在多边形内
                    x, y = test_point
                    inside_test = False
                    p1x, p1y = polygon[0]
                    for j in range(1, n + 1):
                        p2x, p2y = polygon[j % n]
                        if y > min(p1y, p2y):
                            if y <= max(p1y, p2y):
                                if x <= max(p1x, p2x):
                                    if p1y != p2y:
                                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                                    if p1x == p2x or x <= xinters:
                                        inside_test = not inside_test
                        p1x, p1y = p2x, p2y
                    
                    if inside_test:
                        # 如果测试点还在多边形内，说明法向量方向错误，需要反向
                        normal = (-normal[0], -normal[1])
                    
                    # 沿法向量向外移动
                    best_exit = (
                        exit_point[0] + normal[0] * 0.5,
                        exit_point[1] + normal[1] * 0.5
                    )
                else:
                    # 如果无法计算法向量，使用原来的方法
                    direction = (exit_point[0] - start[0], exit_point[1] - start[1])
                    if math.sqrt(direction[0]**2 + direction[1]**2) > 0:
                        norm = math.sqrt(direction[0]**2 + direction[1]**2)
                        direction = (direction[0]/norm, direction[1]/norm)
                        best_exit = (
                            exit_point[0] + direction[0] * 0.5,
                            exit_point[1] + direction[1] * 0.5
                        )
                    else:
                        best_exit = exit_point
        
        actual_start = best_exit
    
    # =================================================================
    # 2. 检查是否可以直接到达终点
    # =================================================================
    can_go_direct = True
    for obstacle in obstacles:
        # 将矩阵转换为点列表
        polygon = []
        for i in range(obstacle.shape[0]):
            polygon.append((obstacle[i, 0], obstacle[i, 1]))
        
        n = len(polygon)
        
        # 检查端点是否在多边形内
        x, y = actual_start
        inside_start = False
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside_start = not inside_start
            p1x, p1y = p2x, p2y
        
        x, y = end
        inside_end = False
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside_end = not inside_end
            p1x, p1y = p2x, p2y
        
        if inside_start or inside_end:
            can_go_direct = False
            break
        
        # 检查线段是否与多边形的任何边相交
        for i in range(n):
            p1 = polygon[i]
            p2 = polygon[(i + 1) % n]
            
            x1, y1 = actual_start
            x2, y2 = end
            x3, y3 = p1
            x4, y4 = p2
            
            denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            
            if abs(denom) < 1e-10:
                continue
            
            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
            u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
            
            if 0 <= t <= 1 and 0 <= u <= 1:
                can_go_direct = False
                break
        
        if not can_go_direct:
            break
    
    # 如果可以直接到达，返回直线路径
    if can_go_direct:
        if actual_start == start:
            path = [start, end]
        else:
            path = [start, actual_start, end]
        
        # 转换为float数组格式
        float_array = []
        for point in path:
            float_array.extend([point[0], point[1]])
        return float_array
    
    # =================================================================
    # 3. 收集所有关键点（起点、终点、障碍物扩展顶点）
    # =================================================================
    waypoints = [actual_start, end]
    
    for obstacle in obstacles:
        # 将矩阵转换为点列表
        polygon = []
        for i in range(obstacle.shape[0]):
            polygon.append((obstacle[i, 0], obstacle[i, 1]))
        
        # 对于矩形障碍物，使用简单的向外扩展
        if len(polygon) == 4:
            # 计算边界框
            min_x = min(p[0] for p in polygon)
            max_x = max(p[0] for p in polygon)
            min_y = min(p[1] for p in polygon)
            max_y = max(p[1] for p in polygon)
            
            # 向外扩展
            extended_vertices = [
                (min_x - 1.0, min_y - 1.0),  # 左下
                (max_x + 1.0, min_y - 1.0),  # 右下
                (max_x + 1.0, max_y + 1.0),  # 右上
                (min_x - 1.0, max_y + 1.0),  # 左上
            ]
            waypoints.extend(extended_vertices)
        else:
            # 对于其他多边形，使用角平分线方法
            n = len(polygon)
            margin = 1.0
            
            for i in range(n):
                prev_vertex = polygon[(i - 1) % n]
                curr_vertex = polygon[i]
                next_vertex = polygon[(i + 1) % n]
                
                v1 = (prev_vertex[0] - curr_vertex[0], prev_vertex[1] - curr_vertex[1])
                v2 = (next_vertex[0] - curr_vertex[0], next_vertex[1] - curr_vertex[1])
                
                len1 = math.sqrt(v1[0]**2 + v1[1]**2)
                len2 = math.sqrt(v2[0]**2 + v2[1]**2)
                
                if len1 > 0:
                    v1 = (v1[0]/len1, v1[1]/len1)
                if len2 > 0:
                    v2 = (v2[0]/len2, v2[1]/len2)
                
                bisector = (v1[0] + v2[0], v1[1] + v2[1])
                bisector_len = math.sqrt(bisector[0]**2 + bisector[1]**2)
                
                if bisector_len > 0:
                    bisector = (bisector[0]/bisector_len, bisector[1]/bisector_len)
                    extended_vertex = (
                        curr_vertex[0] + bisector[0] * margin,
                        curr_vertex[1] + bisector[1] * margin
                    )
                    waypoints.append(extended_vertex)
                else:
                    perp = (-v1[1], v1[0])
                    extended_vertex = (
                        curr_vertex[0] + perp[0] * margin,
                        curr_vertex[1] + perp[1] * margin
                    )
                    waypoints.append(extended_vertex)
    
    # =================================================================
    # 4. 建立连接图
    # =================================================================
    connections = {}
    n = len(waypoints)
    
    for i in range(n):
        connections[i] = []
        for j in range(n):
            if i != j:
                # 检查两点之间是否可以直接连接
                can_connect = True
                for obstacle in obstacles:
                    # 将矩阵转换为点列表
                    polygon = []
                    for k in range(obstacle.shape[0]):
                        polygon.append((obstacle[k, 0], obstacle[k, 1]))
                    
                    n_poly = len(polygon)
                    
                    # 检查端点是否在多边形内
                    x, y = waypoints[i]
                    inside_i = False
                    p1x, p1y = polygon[0]
                    for k in range(1, n_poly + 1):
                        p2x, p2y = polygon[k % n_poly]
                        if y > min(p1y, p2y):
                            if y <= max(p1y, p2y):
                                if x <= max(p1x, p2x):
                                    if p1y != p2y:
                                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                                    if p1x == p2x or x <= xinters:
                                        inside_i = not inside_i
                        p1x, p1y = p2x, p2y
                    
                    x, y = waypoints[j]
                    inside_j = False
                    p1x, p1y = polygon[0]
                    for k in range(1, n_poly + 1):
                        p2x, p2y = polygon[k % n_poly]
                        if y > min(p1y, p2y):
                            if y <= max(p1y, p2y):
                                if x <= max(p1x, p2x):
                                    if p1y != p2y:
                                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                                    if p1x == p2x or x <= xinters:
                                        inside_j = not inside_j
                        p1x, p1y = p2x, p2y
                    
                    if inside_i or inside_j:
                        can_connect = False
                        break
                    
                    # 检查线段是否与多边形的任何边相交
                    for k in range(n_poly):
                        p1 = polygon[k]
                        p2 = polygon[(k + 1) % n_poly]
                        
                        x1, y1 = waypoints[i]
                        x2, y2 = waypoints[j]
                        x3, y3 = p1
                        x4, y4 = p2
                        
                        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
                        
                        if abs(denom) < 1e-10:
                            continue
                        
                        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
                        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
                        
                        if 0 <= t <= 1 and 0 <= u <= 1:
                            can_connect = False
                            break
                    
                    if not can_connect:
                        break
                
                if can_connect:
                    connections[i].append(j)
    
    # =================================================================
    # 5. 使用Dijkstra算法找最短路径并重建路径
    # =================================================================
    distances = [float('inf')] * n
    distances[0] = 0
    previous = [-1] * n
    unvisited = set(range(n))
    
    while unvisited:
        current = min(unvisited, key=lambda x: distances[x])
        unvisited.remove(current)
        
        if current == 1:  # 到达终点
            break
        
        for neighbor in connections[current]:
            if neighbor in unvisited:
                # 计算距离
                p1 = waypoints[current]
                p2 = waypoints[neighbor]
                dist = math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
                
                new_distance = distances[current] + dist
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous[neighbor] = current
    
    # 重建路径
    if previous[1] == -1:
        return []  # 无法到达
    
    path = []
    current = 1
    while current != -1:
        path.append(waypoints[current])
        current = previous[current]
    
    path.reverse()
    
    # =================================================================
    # 6. 路径后处理
    # =================================================================
    # 如果实际起点不是原始起点，在路径前面加上原始起点
    if actual_start != start:
        path.insert(0, start)
    
    # 转换为float数组格式
    float_array = []
    for point in path:
        float_array.extend([point[0], point[1]])
    
    return float_array


# 测试示例
if __name__ == "__main__":
    print("=== 超整合版路径规划算法测试 ===")
    
    # 定义起点和终点
    start_point = (0, 0)
    end_point = (10, 10)
    
    # 定义障碍物（矩阵形式）
    # 第一个障碍物：矩形（4个点）
    obstacle1 = np.array([
        [2, 2],
        [4, 2],
        [4, 4],
        [2, 4]
    ])
    
    # 第二个障碍物：不规则六边形（6个点）
    obstacle2 = np.array([
        [6, 1],
        [8, 1],
        [9, 2],
        [8, 3],
        [6, 3],
        [5, 2]
    ])
    
    # 第三个障碍物：另一个不规则六边形（6个点）
    obstacle3 = np.array([
        [3, 6],
        [5, 6],
        [6, 7],
        [5, 8],
        [3, 8],
        [2, 7]
    ])
    
    obstacles = [obstacle1, obstacle2, obstacle3]
    
    # 测试1: 正常情况
    print("测试1: 正常路径规划")
    path1 = find_path_ultra_consolidated(start_point, end_point, obstacles)
    print(f"路径float数组: {path1}")
    
    # 测试2: 起点在障碍物内部
    print("\n测试2: 起点在障碍物内部")
    start2 = (3, 3)  # 在第一个障碍物内部
    path2 = find_path_ultra_consolidated(start2, end_point, obstacles)
    print(f"路径float数组: {path2}")
    
    # 测试3: 起点在多边形障碍物内部
    print("\n测试3: 起点在多边形障碍物内部")
    start3 = (7, 2)  # 在第二个障碍物内部
    end3 = (1, 9)
    path3 = find_path_ultra_consolidated(start3, end3, obstacles)
    print(f"路径float数组: {path3}")
    
    # 验证输出格式
    print("\n=== 输出格式验证 ===")
    for i, path in enumerate([path1, path2, path3]):
        print(f"路径{i+1}:")
        for j in range(0, len(path), 2):
            if j + 1 < len(path):
                print(f"  点{j//2 + 1}: ({path[j]}, {path[j+1]})")
