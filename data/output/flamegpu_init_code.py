#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlameGPU学生代理初始化代码
基于建筑物内散点数据生成
总散点数: 1542
"""

import json
import os

def initialize_student_agent_population(studentAgentPopulation, population_file='data/output/population_points.json'):
    """
    初始化学生代理种群
    使用从建筑物散点生成的数据
    
    Parameters:
    -----------
    studentAgentPopulation : list
        FlameGPU学生代理种群列表
    population_file : str
        人口数据JSON文件路径
    """
    # 从JSON文件加载散点数据
    if not os.path.exists(population_file):
        print(f"❌ 找不到人口数据文件: {population_file}")
        return
    
    try:
        with open(population_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取学生代理数据
        agents = data['agents']['student_agent']['states']['default']['agents']
        
        num_student_agents = len(agents)
        print(f"初始化 {num_student_agents} 个学生代理个体")
        
        studentAgentPopulation = pyflamegpu.AgentVector(model.Agent("student_agent"), num_student_agents)

        for i in range(num_student_agents):
            student_agent = studentAgentPopulation[i]
            agent_data = agents[i]['variables']
            
            # 设置位置坐标
            student_agent.setVariableFloat("x", agent_data['x'])
            student_agent.setVariableFloat("y", agent_data['y'])
            
            # 设置建筑物信息
            student_agent.setVariableInt("building_id", agent_data['building_id'])
            student_agent.setVariableInt("point_id", agent_data['point_id'])
            student_agent.setVariableInt("floor", agent_data['floor'])
        
        cudaSimulation.setPopulationData(studentAgentPopulation)
        print("学生代理种群初始化完成")
        
    except Exception as e:
        print(f"❌ 加载人口数据失败: {e}")

# 使用示例：
# from flamegpu import *
# 
# # 创建模型
# model = pyflamegpu.ModelDescription("Population Model")
# 
# # 添加代理类型
# student_agent = model.newAgent("student_agent")
# student_agent.newVariableFloat("x")
# student_agent.newVariableFloat("y")
# student_agent.newVariableInt("building_id")
# student_agent.newVariableInt("point_id")
# student_agent.newVariableInt("floor")
# 
# # 初始化种群
# init_population = model.newAgentFunction("init_population")
# init_population.setFunction(initialize_student_agent_population)
# 
# # 运行模型...
