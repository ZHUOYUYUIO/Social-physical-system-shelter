import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def plot_attraction_heatmap(json_path, grid_size=(700, 700)):
    """
    读取吸引力矩阵 JSON 并生成热区图。
    修正了 X/Y 轴颠倒以及 Y 轴方向的问题。
    """
    if not os.path.exists(json_path):
        print(f"文件不存在: {json_path}")
        return

    # 1. 加载数据
    print(f"正在加载数据: {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    flat_map = data.get("macro_environment", {}).get("map", [])
    if not flat_map:
        print("JSON 格式不正确或 map 为空")
        return
    
    # 2. 将 1D 列表转换回 2D 矩阵 (700, 700)
    # 原始矩阵存储方式是 matrix[X, Y]
    matrix = np.array(flat_map).reshape(grid_size)
    
    # 3. 【核心修正】转置矩阵，使行对应 Y 坐标，列对应 X 坐标
    # 现在 matrix_plot[Y, X] = matrix[X, Y]
    matrix_plot = matrix.T
    
    # 4. 绘图
    plt.figure(figsize=(12, 10))
    
    # 使用 seaborn 绘制热区图
    # xticklabels/yticklabels 可以设置为较大间隔，防止刻度堆叠
    ax = sns.heatmap(
        matrix_plot, 
        cmap='viridis', 
        cbar_kws={'label': 'Attraction Value'},
        xticklabels=100, 
        yticklabels=100
    )
    
    plt.title("Familiarity Points Attraction Heatmap")
    plt.xlabel("X Coordinate ")
    plt.ylabel("Y Coordinate ")
    
    # 5. 【方向修正】反转 Y 轴，使 y=0 在下方，符合地理坐标系
    # 如果你的原始坐标系 y=0 确实在顶部（如屏幕坐标），则注释掉下面这一行
    ax.invert_yaxis()
    
    plt.tight_layout()
    plt.show()

# 调用示例
if __name__ == "__main__":
    # 目标文件路径
    target_file = "data/env_data/attraction_matrix_familiar_points.json"
    plot_attraction_heatmap(target_file)