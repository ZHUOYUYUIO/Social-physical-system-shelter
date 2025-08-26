import json
import numpy as np

def matrix_to_column(matrix, output_file=True):
    """
    将NumPy矩阵展成一列并生成指定格式的JSON
    
    Args:
        matrix: NumPy二维矩阵
        output_file: 输出文件名 (可选)
    
    Returns:
        JSON格式的字符串
    """
    # 将NumPy矩阵展平为一维列表
    flattened = matrix.flatten().tolist()
    
    # 构建JSON结构
    data = {
        "macro_environment": {
            "obstacle3": flattened
        }
    }
    
    # 转换为JSON字符串
    json_str = json.dumps(data, indent=4)
    
    # 如果指定了输出文件，则写入文件
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_str)
    
    return json_str

# 你的矩阵
example_matrix = np.array([
        [3, 6],
        [5, 6],
        [6, 7],
        [5, 8],
        [3, 8],
        [2, 7]
    ])

if __name__ == "__main__":
    # 生成JSON并打印

    
    # 保存到文件（可选）
    matrix_to_column(example_matrix, "obstacle3.json")