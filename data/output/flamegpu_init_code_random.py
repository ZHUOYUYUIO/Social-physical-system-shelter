#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlameGPU猎物种群初始化代码（随机分布版本）
散点数: 1638
"""

import random

def initialize_prey_population(preyPopulation):
    """
    初始化猎物种群（随机分布）
    """
    num_prey = 1638
    print(f"初始化 {num_prey} 个猎物个体（随机分布）")
    
    for i in range(num_prey):
        prey = preyPopulation[i]
        
        # 随机设置位置坐标（在-1.0到1.0范围内）
        prey.setVariableFloat("x", random.uniform(-1.0, 1.0))
        prey.setVariableFloat("y", random.uniform(-1.0, 1.0))
        
        # 设置建筑物信息（随机分配）
        prey.setVariableInt("building_id", random.randint(0, 5))  # 假设有6个建筑物
        prey.setVariableInt("point_id", i)
        prey.setVariableInt("floor", random.randint(1, 6))  # 随机楼层1-6层
    
    print("猎物种群初始化完成（随机分布）")

# 使用示例：
# from flamegpu import *
# 
# # 创建模型
# model = pyflamegpu.ModelDescription("Population Model")
# 
# # 添加代理类型
# prey = model.newAgent("prey")
# prey.newVariableFloat("x")
# prey.newVariableFloat("y")
# prey.newVariableInt("building_id")
# prey.newVariableInt("point_id")
# prey.newVariableInt("floor")
# 
# # 初始化种群
# init_population = model.newAgentFunction("init_population")
# init_population.setFunction(initialize_prey_population)
# 
# # 运行模型...
