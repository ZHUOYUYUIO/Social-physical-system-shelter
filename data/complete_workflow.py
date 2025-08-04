#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

This is a script for complete workflow used to generate data of ABM
This script combine the functions including "coordinate system transformation" and "population generation"
完整工作流程脚本
整合坐标转换和散点生成功能
"""

import os
import sys
from community_building_transformer import CommunityBuildingTransformer
from generate_population_points import PopulationPointGenerator
from generate_flamegpu_code import generate_flamegpu_init_code
import geopandas as gpd


#DEfine what are needed for our function
def run_complete_workflow(boundary_file='data/boundary.geojson', 
                         buildings_file='data/buildings.geojson',
                         stairwells_file='data/stairwell.geojson',
                         base_population=50, 
                         variance=0.3):
    """
    运行完整的工作流程
    
    Parameters:
    -----------
    boundary_file : str
        社区边界文件路径
    buildings_file : str
        建筑物文件路径（包含楼层信息）
    base_population : int
        每层基础人口数
    variance : float
        人口变化幅度
    """
    
    print("=== complete workflow. ch:完整工作流程：坐标转换 + 散点生成 ===")
    print("=" * 60)
    
    # 检查输入文件
    if not os.path.exists(boundary_file):
        print(f"❌ can not find the boundary_file; 找不到社区边界文件: {boundary_file}")
        return False
    
    if not os.path.exists(buildings_file):
        print(f"❌ can not find the builindings_file; 找不到建筑物文件: {buildings_file}")
        return False
    
    if not os.path.exists(stairwells_file):
        print(f"❌ can not find the builindings_file; 找不到建筑物文件: {stairwells_file}")
        return False    
    
    try:
        # 步骤1：坐标转换
        print("\n📋 步骤1：坐标转换")
        print("-" * 30)
        
        transformer = CommunityBuildingTransformer(target_crs='EPSG:3415')
        transform_result = transformer.process_community_data(boundary_file, buildings_file, stairwells_file)
        
        if not transform_result:
            print("❌ 坐标转换失败")
            return False
        
        # 保存转换结果
        transformer.save_transformed_data(transform_result, 'data/output')
        
        # 步骤2：散点生成
        print("\n📋 步骤2：散点生成")
        print("-" * 30)
        
        generator = PopulationPointGenerator('data/output/transformed_buildings.geojson')
        population_result = generator.process_data(base_population, variance)
        
        if not population_result:
            print("❌ 散点生成失败")
            return False
        
        # 步骤3：生成FlameGPU代码
        print("\n📋 步骤3：生成FlameGPU代码")
        print("-" * 30)
        
        code_success = generate_flamegpu_init_code()
        
        if not code_success:
            print("❌ FlameGPU代码生成失败")
            return False
        
        # 显示最终结果
        print("\n🎉 工作流程完成！")
        print("=" * 60)
        print("生成的文件：")
        print("\n📁 坐标转换结果：")
        print("  - data/output/transformed_boundary.shp")
        print("  - data/output/transformed_boundary.geojson")
        print("  - data/output/transformed_buildings.shp")
        print("  - data/output/transformed_buildings.geojson")
        print("  - data/output/transformation_info.txt")
        
        print("\n📁 散点生成结果：")
        print("  - data/output/population_points.json (FlameGPU格式)")
        print("  - data/output/population_points.csv")
        print("  - data/output/population_points.geojson")
        print("  - data/output/population_visualization.png")
        
        print("\n📁 FlameGPU代码：")
        print("  - data/output/flamegpu_init_code.py (基于散点数据)")
        print("  - data/output/flamegpu_init_code_random.py (随机分布)")
        
        print(f"\n📊 统计信息：")
        print(f"  - 建筑物数量: {len(population_result['buildings'])}")
        print(f"  - 散点总数: {len(population_result['points'])}")
        print(f"  - 平均每建筑物散点数: {len(population_result['points'])/len(population_result['buildings']):.1f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 工作流程执行失败: {e}")
        return False

def main():
    """主函数"""
    print("完整工作流程脚本")
    print("功能：坐标转换 + 散点生成 + FlameGPU代码生成")
    print("=" * 60)
    
    # 设置参数
    boundary_file = "data/boundary.geojson"
    buildings_file = "data/buildings.geojson"  # 包含楼层信息的建筑物文件
    base_population = 50  # 每层基础人口数
    variance = 0.3        # 人口变化幅度
    
    print(f"输入文件：")
    print(f"  - 社区边界: {boundary_file}")
    print(f"  - 建筑物: {buildings_file} (包含楼层信息)")
    print(f"参数设置：")
    print(f"  - 每层基础人口数: {base_population}")
    print(f"  - 人口变化幅度: {variance}")
    
    # 运行完整工作流程
    success = run_complete_workflow(
        boundary_file=boundary_file,
        buildings_file=buildings_file,
        base_population=base_population,
        variance=variance
    )
    
    if success:
        print("\n✅ 所有步骤执行成功！")
        print("\n💡 使用说明：")
        print("1. 查看 data/output/ 目录下的所有生成文件")
        print("2. 使用 data/output/flamegpu_init_code.py 中的代码初始化FlameGPU模型")
        print("3. 根据需要调整 base_population 和 variance 参数")
    else:
        print("\n❌ 工作流程执行失败")

if __name__ == "__main__":
    main() 