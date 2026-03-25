import os
import json
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon
import random

def generate_standardized_points(boundary_gdf, step=10):
    """生成以step为间隔的标准化点集，覆盖边界"""
    minx, miny, maxx, maxy = boundary_gdf.total_bounds
    points = []
    for x in range(int(minx), int(maxx)+1, step):
        for y in range(int(miny), int(maxy)+1, step):
            pt = Point(x, y)
            if boundary_gdf.contains(pt).any():
                points.append({'x': x, 'y': y, 'geometry': pt})
    return pd.DataFrame(points)

def filter_points_in_shelters(points_df, shelter_gdf):
    """筛选出位于shelter可用框内的点"""
    # shelter_gdf每个geometry是Polygon
    mask = points_df['geometry'].apply(lambda pt: shelter_gdf.contains(pt).any())
    return points_df[mask].reset_index(drop=True)

def generate_flamegpu_init_code_for_shelter(
    population_file='data/output/shelter_points.csv',
    output_file='data/output/flamegpu_init_code_for_shelter.py',
    shelter_number=10
):
    """
    随机挑选 shelter_number 个 shelter agent，并生成FlameGPU初始化代码
    """
    import csv

    if not os.path.exists(population_file):
        print(f"❌ 找不到shelter_points.csv文件: {population_file}")
        return False

    try:
        # 读取 shelter_points.csv
        with open(population_file, 'r', encoding='utf-8') as f:
            shelter_points = [
                {'index': int(row['index']), 'x': float(row['x']), 'y': float(row['y'])}
                for row in csv.DictReader(f)
            ]

        if len(shelter_points) < shelter_number:
            print(f"❌ shelter点数量不足，只有{len(shelter_points)}个，无法随机选取{shelter_number}个")
            return False

        code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlameGPU shelter代理初始化代码
随机选取 {shelter_number} 个 shelter agent
"""

from pyflamegpu import *

def initialize_shelter_agent_population(model, cuda_model, index_vector, shelter_csv_path='data/output/shelter_points_withoutput_new.csv'):
    """
    初始化shelter代理种群
    index_vector: shelter点的索引列表（如 [3, 7, 12, ...]）
    shelter_csv_path: shelter点的csv文件路径
    """
    import csv
    import os

    if not os.path.exists(shelter_csv_path):
        raise FileNotFoundError(f"未找到shelter点csv文件: {{shelter_csv_path}}")

    # 读取csv文件，提取所有shelter点
    with open(shelter_csv_path, 'r', encoding='utf-8') as f:
        shelter_points = [
            {{'index': int(row['index']), 'x': float(row['x']), 'y': float(row['y'])}}
            for row in csv.DictReader(f)
        ]

    num_agents = len(index_vector)
    print(f"初始化 {{num_agents}} 个shelter代理个体")

    shelterAgentPopulation = pyflamegpu.AgentVector(model.Agent("shelter_agent"), num_agents)

    for i, idx in enumerate(index_vector):
        pt = next((p for p in shelter_points if p['index'] == idx), None)
        if pt is None:
            raise ValueError(f"未找到 index={{idx}} 的 shelter 点")
        shelter_agent = shelterAgentPopulation[i]
        shelter_agent.setVariableFloat("x", pt['x'])
        shelter_agent.setVariableFloat("y", pt['y'])
        shelter_agent.setVariableInt("shelter_id", pt['index'])
        shelter_agent.setVariableInt("graph_id", pt['graph_id'])
        shelter_agent.setVariableFloat("z", 0.0)

    cuda_model.setPopulationData(shelterAgentPopulation)
    print("shelter代理种群初始化完成")
'''

        # 这里判断output_file的父目录是否为空字符串，如果是则不创建目录
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                print(f"❌ 创建目录失败: {output_dir}，错误信息: {e}")
                return False

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(code)
        except Exception as e:
            print(f"❌ 无法写入文件 {output_file}，错误信息: {e}")
            return False

        print(f"✓ shelter代理FlameGPU初始化代码已保存: {output_file}")
        return True

    except Exception as e:
        print(f"❌ 生成shelter代理FlameGPU代码失败: {e}")
        return False
        


def main():
    # 路径
    boundary_path = os.path.join(os.path.dirname(__file__), '../data/output/transformed_boundary.geojson')
    shelter_path = os.path.join(os.path.dirname(__file__), '../data/output/transformed_shelter_available.geojson')
    output_path = os.path.join(os.path.dirname(__file__), '../data/output/shelter_points.csv')

    # 读取边界
    boundary_gdf = gpd.read_file(boundary_path)
    # 生成标准化点集
    points_df = generate_standardized_points(boundary_gdf, step=20)

    # 读取可用shelter框
    shelter_gdf = gpd.read_file(shelter_path)
    # 筛选在shelter框内的点
    filtered_points = filter_points_in_shelters(points_df, shelter_gdf)

    # 排序并重建索引
    filtered_points = filtered_points.sort_values(['x', 'y']).reset_index(drop=True)
    filtered_points['index'] = filtered_points.index

    # 只保留x, y, index列
    result_df = filtered_points[['index', 'x', 'y']]

    # 输出为csv
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result_df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"✅ 已生成 shelter_points.csv，点数: {len(result_df)}，保存于: {output_path}")


    shelter_flamegpu_code_path = os.path.join(os.path.dirname(__file__), '../data/output/shelter_flamegpu_init_code.py')
    
    generate_flamegpu_init_code_for_shelter(
        population_file=output_path,
        output_file=shelter_flamegpu_code_path,
        shelter_number=6
    )

if __name__ == "__main__":
    main()
