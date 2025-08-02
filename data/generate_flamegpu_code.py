#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlameGPU代码生成器
根据生成的散点数据，生成符合FlameGPU格式的初始化代码
"""

import json
import os
import random

def generate_flamegpu_init_code(population_file='data/output/population_points.json',
                                output_file='data/output/flamegpu_init_code.py'):
    """
    生成FlameGPU初始化代码
    
    Parameters:
    -----------
    population_file : str
        人口散点数据文件路径
    output_file : str
        输出的FlameGPU代码文件路径
    """
    
    # 检查输入文件是否存在
    if not os.path.exists(population_file):
        print(f"❌ 找不到人口数据文件: {population_file}")
        print("请先运行 generate_population_points.py 生成散点数据")
        return False
    
    try:
        # 加载人口数据
        with open(population_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取散点数据
        agents = data['agents']['student_agent']['states']['default']['agents']
        
        if not agents:
            print("❌ 人口数据为空")
            return False
        
        print(f"✓ 加载了 {len(agents)} 个散点数据")
        
        # 生成FlameGPU代码
        code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlameGPU学生代理初始化代码
基于建筑物内散点数据生成
总散点数: {len(agents)}
"""

import json
import os
from pyflamegpu import *
import pyflamegpu.codegen
import sys

def initialize_student_agent_population(model, cuda_model, population_file='data/output/population_points.json'):
    """
    初始化学生代理种群
    使用从建筑物散点生成的数据
    
    Parameters:
    -----------
    model : pyflamegpu.ModelDescription
        FlameGPU模型描述对象
    cuda_model : pyflamegpu.CUDASimulation
        CUDA模拟对象
    population_file : str
        人口数据JSON文件路径
    """
    # 从JSON文件加载散点数据
    if not os.path.exists(population_file):
        print(f"❌ 找不到人口数据文件: {{population_file}}")
        return
    
    try:
        with open(population_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取学生代理数据
        agents = data['agents']['student_agent']['states']['default']['agents']
        
        num_student_agents = len(agents)
        print(f"初始化 {{num_student_agents}} 个学生代理个体")
        
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
        
        cuda_model.setPopulationData(studentAgentPopulation)
        print("学生代理种群初始化完成")
        
    except Exception as e:
        print(f"❌ 加载人口数据失败: {{e}}")

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
'''
        
        # 保存代码文件
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        print(f"✓ FlameGPU初始化代码已保存: {output_file}")
        
        # 生成简化的随机版本（如果用户想要随机分布）
        random_code_file = output_file.replace('.py', '_random.py')
        generate_random_version(random_code_file, len(agents))
        
        return True
        
    except Exception as e:
        print(f"❌ 生成FlameGPU代码失败: {e}")
        return False

def generate_random_version(output_file, num_points):
    """
    生成随机分布的版本（作为对比）
    
    Parameters:
    -----------
    output_file : str
        输出文件路径
    num_points : int
        散点数量
    """
    
    code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlameGPU学生代理初始化代码（随机分布版本）
散点数: {num_points}
"""

import random

def initialize_student_agent_population(studentAgentPopulation):
    """
    初始化学生代理种群（随机分布）
    """
    num_student_agents = {num_points}
    print(f"初始化 {{num_student_agents}} 个学生代理个体（随机分布）")
    
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
'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(code)
    
    print(f"✓ 随机分布版本已保存: {output_file}")

def main():
    """主函数"""
    print("FlameGPU代码生成器")
    print("=" * 40)
    
    # 生成基于散点数据的代码
    success = generate_flamegpu_init_code()
    
    if success:
        print("\n✅ 代码生成成功！")
        print("生成的文件：")
        print("- data/output/flamegpu_init_code.py (基于散点数据)")
        print("- data/output/flamegpu_init_code_random.py (随机分布版本)")
        print("\n使用说明：")
        print("1. 将生成的代码集成到您的FlameGPU模型中")
        print("2. 确保模型中有对应的变量定义")
        print("3. 调用 initialize_prey_population 函数初始化种群")
    else:
        print("\n❌ 代码生成失败")

if __name__ == "__main__":
    main() 