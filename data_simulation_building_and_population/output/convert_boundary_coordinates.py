#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
边界坐标转换脚本
将 transformed_boundary.geojson 中的坐标点转换成 pen.addVertex() 格式
"""

import json
import os

def convert_boundary_coordinates():
    """
    将边界坐标转换成 pen.addVertex() 格式
    """ 
    # 读取边界文件
    boundary_file = "transformed_boundary.geojson"
    
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    boundary_file = os.path.join(script_dir, boundary_file)
    
    if not os.path.exists(boundary_file):
        print(f"错误：找不到文件 {boundary_file}")
        return
    
    try:
        with open(boundary_file, 'r', encoding='utf-8') as f:
            boundary_data = json.load(f)
        
        # 提取坐标点
        features = boundary_data.get('features', [])
        if not features:
            print("错误：文件中没有找到features")
            return
        
        # 获取第一个多边形的坐标
        geometry = features[0].get('geometry', {})
        if geometry.get('type') != 'Polygon':
            print("错误：几何类型不是Polygon")
            return
        
        coordinates = geometry.get('coordinates', [])
        if not coordinates:
            print("错误：没有找到坐标数据")
            return
        
        # 获取外环坐标（第一个坐标数组）
        outer_ring = coordinates[0]
        
        print("转换后的坐标点（pen.addVertex格式）：")
        print("# 边界坐标点")
        
        # 为每个坐标点生成 pen.addVertex() 调用
        for i, coord in enumerate(outer_ring):
            x, y = coord
            # 将坐标转换为整数（如果需要的话）
            x_int = int(round(x))
            y_int = int(round(y))
            
            # 添加中文注释说明位置
            position_comment = ""
            if i == 0:
                position_comment = " # 起始点"
            elif i == len(outer_ring) - 1:
                position_comment = " # 闭合点"
            
            print(f"    pen.addVertex({x_int}, {y_int}, 0){position_comment}")
        
        print(f"\n# 总共 {len(outer_ring)} 个坐标点")
        
        # 同时生成浮点数版本
        print("\n# 浮点数版本（精确坐标）：")
        for i, coord in enumerate(outer_ring):
            x, y = coord
            position_comment = ""
            if i == 0:
                position_comment = " # 起始点"
            elif i == len(outer_ring) - 1:
                position_comment = " # 闭合点"
            
            print(f"    pen.addVertex({x}, {y}, 0){position_comment}")
        
        # 保存到文件
        output_file = "data/output/boundary_coordinates_converted.py"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 自动生成的边界坐标转换结果\n")
            f.write("# 从 transformed_boundary.geojson 转换而来\n\n")
            
            f.write("# 整数版本\n")
            for i, coord in enumerate(outer_ring):
                x, y = coord
                x_int = int(round(x))
                y_int = int(round(y))
                position_comment = ""
                if i == 0:
                    position_comment = " # 起始点"
                elif i == len(outer_ring) - 1:
                    position_comment = " # 闭合点"
                
                f.write(f"pen.addVertex({x_int}, {y_int}, 0){position_comment}\n")
            
            f.write("\n# 浮点数版本（精确坐标）\n")
            for i, coord in enumerate(outer_ring):
                x, y = coord
                position_comment = ""
                if i == 0:
                    position_comment = " # 起始点"
                elif i == len(outer_ring) - 1:
                    position_comment = " # 闭合点"
                
                f.write(f"pen.addVertex({x}, {y}, 0){position_comment}\n")
        
        print(f"\n转换结果已保存到 {output_file}")
        
    except Exception as e:
        print(f"处理文件时出错：{e}")

def main():
    """
    主函数
    """
    print("边界坐标转换工具")
    print("=" * 30)
    convert_boundary_coordinates()

if __name__ == "__main__":
    main() 