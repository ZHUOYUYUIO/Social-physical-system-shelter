import numpy as np
import math
import json

def expand_obstacle_simple(obstacle, margin=0.5):
    """
    等比例扩张障碍物：将每个顶点沿中心方向向外移动
    """
    polygon = []
    for i in range(obstacle.shape[0]):
        polygon.append((obstacle[i, 0], obstacle[i, 1]))
    
    # 计算多边形的中心点
    center_x = sum(p[0] for p in polygon) / len(polygon)
    center_y = sum(p[1] for p in polygon) / len(polygon)
    center = (center_x, center_y)
    
    expanded_vertices = []
    for point in polygon:
        # 计算从中心到顶点的方向向量
        dx = point[0] - center_x
        dy = point[1] - center_y
        
        # 计算距离
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 1e-10:
            # 归一化方向向量
            norm_dx = dx / distance
            norm_dy = dy / distance
            
            # 沿方向向外移动
            new_x = point[0] + norm_dx * margin
            new_y = point[1] + norm_dy * margin
            expanded_vertices.append((new_x, new_y))
        else:
            # 如果距离为0（理论上不会发生），直接使用原顶点
            expanded_vertices.append(point)
    
    return expanded_vertices

def expand_obstacle_uniform(obstacle, margin=0.5):
    """
    均匀扩张障碍物：每个顶点向外移动固定距离
    """
    polygon = []
    for i in range(obstacle.shape[0]):
        polygon.append((obstacle[i, 0], obstacle[i, 1]))
    
    expanded_vertices = []
    n = len(polygon)
    
    for i in range(n):
        # 当前顶点
        curr = polygon[i]
        prev = polygon[(i - 1) % n]
        next = polygon[(i + 1) % n]
        
        # 计算两条边的向量
        v1 = (prev[0] - curr[0], prev[1] - curr[1])
        v2 = (next[0] - curr[0], next[1] - curr[1])
        
        # 计算法向量（平均值）
        norm1 = (-v1[1], v1[0])  # 左转90度
        norm2 = (-v2[1], v2[0])
        
        # 归一化
        len1 = math.sqrt(norm1[0]**2 + norm1[1]**2)
        len2 = math.sqrt(norm2[0]**2 + norm2[1]**2)
        
        if len1 > 1e-10:
            norm1 = (norm1[0]/len1, norm1[1]/len1)
        if len2 > 1e-10:
            norm2 = (norm2[0]/len2, norm2[1]/len2)
        
        # 平均法向量
        avg_norm = ((norm1[0] + norm2[0])/2, (norm1[1] + norm2[1])/2)
        avg_len = math.sqrt(avg_norm[0]**2 + avg_norm[1]**2)
        
        if avg_len > 1e-10:
            avg_norm = (avg_norm[0]/avg_len, avg_norm[1]/avg_len)
        
        # 向外移动
        new_x = curr[0] + avg_norm[0] * margin
        new_y = curr[1] + avg_norm[1] * margin
        expanded_vertices.append((new_x, new_y))
    
    return expanded_vertices

def ccw(A, B, C):
    """计算三点(A, B, C)的叉积"""
    return (B[0]-A[0])*(C[1]-A[1]) - (B[1]-A[1])*(C[0]-A[0])

def is_intersect(p1, p2, p3, p4, epsilon=1e-10):
    """判断线段是否相交"""
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    
    # 快速排斥实验
    if max(p1[0], p2[0]) < min(p3[0], p4[0]) or max(p3[0], p4[0]) < min(p1[0], p2[0]) or \
       max(p1[1], p2[1]) < min(p3[1], p4[1]) or max(p3[1], p4[1]) < min(p1[1], p2[1]):
        return False
    
    # 跨立实验
    if cross(p1, p2, p3) * cross(p1, p2, p4) > epsilon or \
       cross(p3, p4, p1) * cross(p3, p4, p2) > epsilon:
        return False
    
    return True

def is_point_in_polygon(point, polygon):
    """判断点是否在多边形内部"""
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside

def is_edge_visible(original_obstacles, point1, point2, epsilon=1e-10):
    """判断边是否可见"""
    if math.dist(point1, point2) < epsilon:
        return False
    
    # 检查是否与任何障碍物边相交
    for obstacle in original_obstacles:
        n = len(obstacle)
        for i in range(n):
            p3 = obstacle[i]
            p4 = obstacle[(i + 1) % n]
            
            if is_intersect(point1, point2, p3, p4):
                return False
    
    # 检查中点是否在任何障碍物内部
    mid_point = ((point1[0] + point2[0])/2, (point1[1] + point2[1])/2)
    for obstacle in original_obstacles:
        if is_point_in_polygon(mid_point, obstacle):
            return False
    
    return True

def generate_visibility_graph(original_obstacles, expanded_obstacles):
    """生成可视图"""
    all_vertices = []
    vertex_to_id = {}
    
    # 添加所有扩展后的顶点
    vertex_id = 1
    for i, obstacle in enumerate(expanded_obstacles):
        for point in obstacle:
            all_vertices.append(point)
            vertex_to_id[point] = str(vertex_id)
            vertex_id += 1
    
    # 生成可见边
    edges = []
    n = len(all_vertices)
    
    print(f"共有 {n} 个扩展顶点")
    
    for i in range(n):
        for j in range(i + 1, n):
            if is_edge_visible(original_obstacles, all_vertices[i], all_vertices[j]):
                edges.append((all_vertices[i], all_vertices[j]))
    
    print(f"生成 {len(edges)} 条可见边")
    return all_vertices, edges, vertex_to_id

def main():
    # 定义障碍物
    obstacle1 = np.array([[2, 2], [4, 2], [4, 4], [2, 4]])
    obstacle2 = np.array([[6, 1], [8, 1], [9, 2], [8, 3], [6, 3], [5, 2]])
    obstacle3 = np.array([[3, 6], [5, 6], [6, 7], [5, 8], [3, 8], [2, 7]])
    
    original_obstacles = [obstacle1, obstacle2, obstacle3]
    
    # 扩展障碍物 - 使用等比例扩张方法
    expanded_obstacles = []
    for i, obstacle in enumerate(original_obstacles):
        expanded = expand_obstacle_simple(obstacle, margin=0.1)
        expanded_obstacles.append(expanded)
        print(f"障碍物 {i+1} 扩展完成")
        print(f"原始: {obstacle.tolist()}")
        print(f"扩展后: {expanded}")
        print()
    
    # 生成可视图
    vertices, edges, vertex_to_id = generate_visibility_graph(original_obstacles, expanded_obstacles)
    
    # 构建输出
    nodes = [{"id": vertex_to_id[v], "bar": [float(v[0]), float(v[1])]} for v in vertices]
    links = []
    
    for edge in edges:
        source_id = vertex_to_id[edge[0]]
        target_id = vertex_to_id[edge[1]]
        length = math.dist(edge[0], edge[1])
        # 添加双向链接
        links.append({"source": source_id, "target": target_id, "foo": float(length)})
        links.append({"source": target_id, "target": source_id, "foo": float(length)})
    
    output = {"nodes": nodes, "links": links}
    
    with open("expanded_visibility_graph.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print("JSON文件已生成: expanded_visibility_graph.json")

if __name__ == "__main__":
    main()