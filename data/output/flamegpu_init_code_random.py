#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlameGPU学生代理初始化代码（随机分布版本）
散点数: 1800
"""

import random

def initialize_student_agent_population(studentAgentPopulation):
    """
    初始化学生代理种群（随机分布）
    """
    num_student_agents = 1800
    print(f"初始化 {num_student_agents} 个学生代理个体（随机分布）")
    
    for i in range(num_student_agents):
        student_agent = studentAgentPopulation[i]
        
        # 随机设置位置坐标（在-1.0到1.0范围内）
        student_agent.setVariableFloat("x", random.uniform(-1.0, 1.0))
        student_agent.setVariableFloat("y", random.uniform(-1.0, 1.0))
        
        # 设置建筑物信息（随机分配）
        student_agent.setVariableInt("building_id", random.randint(0, 5))  # 假设有6个建筑物
        student_agent.setVariableInt("point_id", i)
        student_agent.setVariableInt("floor", random.randint(1, 6))  # 随机楼层1-6层
    
    print("学生代理种群初始化完成（随机分布）")

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
