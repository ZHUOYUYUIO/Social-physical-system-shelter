#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
import math

def analyze_geojson_boundaries_simple(geojson_file):
    """
    简化版GeoJSON边界分析
    
    Args:
        geojson_file (str): GeoJSON文件路径
    
    Returns:
        dict: 包含边界信息和中心点的字典
    """
    
    # 读取GeoJSON文件
    with open(geojson_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 存储所有坐标点
    all_coords = []
    building_info = []
    
    # 遍历所有建筑物
    for feature in data['features']:
        building_id = feature['properties']['building_id']
        floors = feature['properties']['floors']
        geometry = feature['geometry']
        
        if geometry['type'] == 'Polygon':
            coords = geometry['coordinates'][0]  # 第一个环是外边界
            all_coords.extend(coords)
            
            # 计算单个建筑物的边界和中心点
            x_coords = [coord[0] for coord in coords]
            y_coords = [coord[1] for coord in coords]
            
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            
            # 计算建筑物中心点（简单平均）
            center_x = sum(x_coords) / len(x_coords)
            center_y = sum(y_coords) / len(y_coords)
            
            # 计算面积（使用多边形面积公式）
            area = calculate_polygon_area(coords)
            
            building_info.append({
                'building_id': building_id,
                'floors': floors,
                'centroid': (center_x, center_y),
                'area': area,
                'bounds': (min_x, min_y, max_x, max_y)
            })
    
    # 计算整体边界
    all_x = [coord[0] for coord in all_coords]
    all_y = [coord[1] for coord in all_coords]
    
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    
    # 计算整体中心点
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    # 计算所有建筑物的中心点
    all_centroids_x = [info['centroid'][0] for info in building_info]
    all_centroids_y = [info['centroid'][1] for info in building_info]
    overall_centroid_x = sum(all_centroids_x) / len(all_centroids_x)
    overall_centroid_y = sum(all_centroids_y) / len(all_centroids_y)
    
    # 构建结果字典
    result = {
        'boundaries': {
            'min_x': min_x,
            'min_y': min_y,
            'max_x': max_x,
            'max_y': max_y,
            'width': max_x - min_x,
            'height': max_y - min_y
        },
        'center_points': {
            'boundary_center': (center_x, center_y),
            'buildings_centroid': (overall_centroid_x, overall_centroid_y)
        },
        'buildings': building_info,
        'total_buildings': len(building_info)
    }
    
    return result

def calculate_polygon_area(coords):
    """
    使用鞋带公式计算多边形面积
    
    Args:
        coords (list): 多边形坐标点列表 [(x1,y1), (x2,y2), ...]
    
    Returns:
        float: 多边形面积
    """
    n = len(coords)
    area = 0.0
    
    for i in range(n):
        j = (i + 1) % n
        area += coords[i][0] * coords[j][1]
        area -= coords[j][0] * coords[i][1]
    
    return abs(area) / 2.0

def print_analysis_results(results):
    """
    打印分析结果
    """
    print("=" * 60)
    print("建筑物边界分析结果")
    print("=" * 60)
    
    boundaries = results['boundaries']
    centers = results['center_points']
    
    print(f"\n📏 边界信息:")
    print(f"   左边界 (min_x): {boundaries['min_x']:.6f}")
    print(f"   右边界 (max_x): {boundaries['max_x']:.6f}")
    print(f"   下边界 (min_y): {boundaries['min_y']:.6f}")
    print(f"   上边界 (max_y): {boundaries['max_y']:.6f}")
    print(f"   宽度: {boundaries['width']:.6f}")
    print(f"   高度: {boundaries['height']:.6f}")
    
    print(f"\n🎯 中心点信息:")
    print(f"   边界中心点: ({centers['boundary_center'][0]:.6f}, {centers['boundary_center'][1]:.6f})")
    print(f"   建筑物质心: ({centers['buildings_centroid'][0]:.6f}, {centers['buildings_centroid'][1]:.6f})")
    
    print(f"\n🏢 建筑物详细信息:")
    print(f"   总建筑物数量: {results['total_buildings']}")
    for building in results['buildings']:
        print(f"   建筑物 {building['building_id']}: 楼层={building['floors']}, "
              f"中心=({building['centroid'][0]:.6f}, {building['centroid'][1]:.6f}), "
              f"面积={building['area']:.6f}")

def save_results_to_file(results, output_file):
    """
    将结果保存到JSON文件
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 结果已保存到: {output_file}")

def main():
    """
    主函数
    """
    # 文件路径
    geojson_file = "data/output/transformed_buildings.geojson"
    results_file = "data/output/boundary_analysis_results.json"
    
    try:
        # 分析GeoJSON文件
        print("🔍 正在分析建筑物边界...")
        results = analyze_geojson_boundaries_simple(geojson_file)
        
        # 打印结果
        print_analysis_results(results)
        
        # 保存结果到文件
        save_results_to_file(results, results_file)
        
        print("\n✅ 分析完成！")
        
    except FileNotFoundError:
        print(f"❌ 错误: 找不到文件 {geojson_file}")
        print("请确保脚本在包含transformed_buildings.geojson的目录中运行")
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

if __name__ == "__main__":
    main() 