#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查散点楼层分布统计
"""

import json
import pandas as pd
from collections import Counter

def analyze_floor_distribution():
    """分析散点的楼层分布"""
    
    # 加载散点数据
    with open('data/output/population_points.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    agents = data['agents']['prey']['states']['default']['agents']
    
    # 提取楼层信息
    floors = [agent['variables']['floor'] for agent in agents]
    building_ids = [agent['variables']['building_id'] for agent in agents]
    
    print("=== 散点楼层分布统计 ===")
    print(f"总散点数: {len(agents)}")
    print()
    
    # 总体楼层分布
    floor_counts = Counter(floors)
    print("总体楼层分布:")
    for floor in sorted(floor_counts.keys()):
        count = floor_counts[floor]
        percentage = (count / len(agents)) * 100
        print(f"  楼层 {floor}: {count} 人 ({percentage:.1f}%)")
    
    print()
    
    # 按建筑物统计楼层分布
    print("按建筑物统计楼层分布:")
    df = pd.DataFrame({
        'building_id': building_ids,
        'floor': floors
    })
    
    for building_id in sorted(df['building_id'].unique()):
        building_data = df[df['building_id'] == building_id]
        building_floors = Counter(building_data['floor'])
        
        print(f"建筑物 {building_id}:")
        for floor in sorted(building_floors.keys()):
            count = building_floors[floor]
            percentage = (count / len(building_data)) * 100
            print(f"  楼层 {floor}: {count} 人 ({percentage:.1f}%)")
        print()
    
    # 验证楼层范围
    min_floor = min(floors)
    max_floor = max(floors)
    print(f"楼层范围: {min_floor} - {max_floor}")
    
    # 检查是否有超出建筑物楼层的情况
    print("\n=== 楼层验证 ===")
    
    # 加载建筑物数据（使用原始文件，因为转换后的文件丢失了属性）
    with open('buildings_with_floors.geojson', 'r', encoding='utf-8') as f:
        buildings_data = json.load(f)
    
    building_floors_info = {}
    for feature in buildings_data['features']:
        building_id = feature['properties']['building_id']
        floors = feature['properties']['floors']
        building_floors_info[building_id] = floors
    
    print("建筑物楼层信息:")
    for building_id, floors in building_floors_info.items():
        print(f"  建筑物 {building_id}: {floors} 层")
    
    print("\n楼层分配验证:")
    for building_id in sorted(df['building_id'].unique()):
        building_data = df[df['building_id'] == building_id]
        building_floors = building_data['floor']
        max_floor_in_data = max(building_floors)
        actual_max_floor = building_floors_info[building_id]
        
        if max_floor_in_data <= actual_max_floor:
            print(f"  建筑物 {building_id}: ✓ 楼层分配正确 (最高楼层: {max_floor_in_data}/{actual_max_floor})")
        else:
            print(f"  建筑物 {building_id}: ✗ 楼层分配错误 (最高楼层: {max_floor_in_data}/{actual_max_floor})")

if __name__ == "__main__":
    analyze_floor_distribution() 