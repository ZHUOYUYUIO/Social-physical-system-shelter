#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目功能测试脚本
验证所有主要功能是否正常工作
"""

import os
import json
import pandas as pd
from pathlib import Path

def test_file_existence():
    """测试必要文件是否存在"""
    print("🔍 测试文件存在性...")
    
    required_files = [
        'boundary.geojson',
        'buildings.geojson',
        'requirements.txt',
        'complete_workflow.py',
        'generate_population_points.py',
        'community_building_transformer.py'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠ 缺少文件: {missing_files}")
        return False
    else:
        print("✅ 所有必要文件都存在")
        return True

def test_output_files():
    """测试输出文件是否生成"""
    print("\n📁 测试输出文件...")
    
    output_files = [
            'data/output/population_points.json',
    'data/output/population_points.csv',
    'data/output/population_points.geojson',
    'data/output/population_visualization.png',
    'data/output/building_population_3d.png',
    'data/output/building_population_interactive.html',
    'data/output/flamegpu_init_code.py',
    'data/output/transformed_buildings.geojson',
    'data/output/transformed_boundary.geojson'
    ]
    
    existing_files = []
    missing_files = []
    
    for file in output_files:
        if os.path.exists(file):
            size = os.path.getsize(file) / 1024  # KB
            print(f"  ✅ {file} ({size:.1f} KB)")
            existing_files.append(file)
        else:
            print(f"  ❌ {file}")
            missing_files.append(file)
    
    print(f"\n📊 输出文件统计:")
    print(f"  生成文件: {len(existing_files)}")
    print(f"  缺失文件: {len(missing_files)}")
    
    return len(missing_files) == 0

def test_data_integrity():
    """测试数据完整性"""
    print("\n📊 测试数据完整性...")
    
    try:
        # 测试JSON数据
        with open('data/output/population_points.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        agents = data['agents']['prey']['states']['default']['agents']
        print(f"  ✅ JSON数据: {len(agents)} 个散点")
        
        # 检查必要字段
        required_fields = ['x', 'y', 'building_id', 'point_id', 'floor']
        sample_agent = agents[0]['variables']
        
        for field in required_fields:
            if field in sample_agent:
                print(f"    ✅ 字段 {field}: {sample_agent[field]}")
            else:
                print(f"    ❌ 缺少字段 {field}")
                return False
        
        # 测试CSV数据
        df = pd.read_csv('data/output/population_points.csv')
        print(f"  ✅ CSV数据: {len(df)} 行, {len(df.columns)} 列")
        
        # 测试GeoJSON数据
        with open('data/output/population_points.geojson', 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        print(f"  ✅ GeoJSON数据: {len(geojson_data['features'])} 个特征")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 数据完整性测试失败: {e}")
        return False

def test_floor_distribution():
    """测试楼层分布"""
    print("\n🏢 测试楼层分布...")
    
    try:
        with open('data/output/population_points.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        agents = data['agents']['prey']['states']['default']['agents']
        floors = [agent['variables']['floor'] for agent in agents]
        
        print(f"  总人口: {len(agents)}")
        print(f"  楼层范围: {min(floors)} - {max(floors)}")
        
        # 检查楼层分布
        floor_counts = {}
        for floor in floors:
            floor_counts[floor] = floor_counts.get(floor, 0) + 1
        
        print(f"  楼层数量: {len(floor_counts)}")
        
        # 检查是否有合理的楼层分布
        if len(floor_counts) > 0 and max(floors) <= 20:
            print("  ✅ 楼层分布合理")
            return True
        else:
            print("  ❌ 楼层分布异常")
            return False
            
    except Exception as e:
        print(f"  ❌ 楼层分布测试失败: {e}")
        return False

def test_flamegpu_code():
    """测试FlameGPU代码生成"""
    print("\n🔧 测试FlameGPU代码...")
    
    try:
        with open('data/output/flamegpu_init_code.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 检查必要的代码元素
        required_elements = [
            'def initialize_prey_population',
            'prey.setVariableFloat("x"',
            'prey.setVariableFloat("y"',
            'prey.setVariableInt("building_id"',
            'prey.setVariableInt("point_id"',
            'prey.setVariableInt("floor"',
            'population_data = ['
        ]
        
        for element in required_elements:
            if element in code:
                print(f"  ✅ 包含 {element}")
            else:
                print(f"  ❌ 缺少 {element}")
                return False
        
        print("  ✅ FlameGPU代码生成正常")
        return True
        
    except Exception as e:
        print(f"  ❌ FlameGPU代码测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 SHELTER_FLAMEGPU2 项目功能测试")
    print("=" * 50)
    
    tests = [
        ("文件存在性", test_file_existence),
        ("输出文件", test_output_files),
        ("数据完整性", test_data_integrity),
        ("楼层分布", test_floor_distribution),
        ("FlameGPU代码", test_flamegpu_code)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 测试: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ 测试异常: {e}")
            results.append((test_name, False))
    
    # 总结测试结果
    print("\n" + "=" * 50)
    print("📋 测试结果总结")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！项目功能正常。")
        return True
    else:
        print("⚠ 部分测试失败，请检查相关功能。")
        return False

if __name__ == "__main__":
    main() 