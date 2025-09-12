#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlameGPU shelter代理初始化代码
随机选取 6 个 shelter agent
"""

from pyflamegpu import *

def initialize_shelter_agent_population(model, cuda_model, index_vector, shelter_csv_path='data/output/shelter_points.csv'):
    """
    初始化shelter代理种群
    index_vector: shelter点的索引列表（如 [3, 7, 12, ...]）
    shelter_csv_path: shelter点的csv文件路径
    """
    import csv
    import os

    if not os.path.exists(shelter_csv_path):
        raise FileNotFoundError(f"未找到shelter点csv文件: {shelter_csv_path}")

    # 读取csv文件，提取所有shelter点
    with open(shelter_csv_path, 'r', encoding='utf-8') as f:
        shelter_points = [
            {'index': int(row['index']), 'x': float(row['x']), 'y': float(row['y'])}
            for row in csv.DictReader(f)
        ]

    num_agents = len(index_vector)
    print(f"初始化 {num_agents} 个shelter代理个体")

    shelterAgentPopulation = pyflamegpu.AgentVector(model.Agent("shelter_agent"), num_agents)

    for i, idx in enumerate(index_vector):
        pt = next((p for p in shelter_points if p['index'] == idx), None)
        if pt is None:
            raise ValueError(f"未找到 index={idx} 的 shelter 点")
        shelter_agent = shelterAgentPopulation[i]
        shelter_agent.setVariableFloat("x", pt['x'])
        shelter_agent.setVariableFloat("y", pt['y'])
        shelter_agent.setVariableInt("shelter_id", pt['index'])
        shelter_agent.setVariableFloat("z", 0.0)

    cuda_model.setPopulationData(shelterAgentPopulation)
    print("shelter代理种群初始化完成")
