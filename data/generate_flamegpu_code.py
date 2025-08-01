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
        agents = data['agents']['prey']['states']['default']['agents']
        
        if not agents:
            print("❌ 人口数据为空")
            return False
        
        print(f"✓ 加载了 {len(agents)} 个散点数据")
        
        # 生成FlameGPU代码
        code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlameGPU猎物种群初始化代码
基于建筑物内散点数据生成
总散点数: {len(agents)}
"""

import random

def initialize_prey_population(preyPopulation):
    """
    初始化猎物种群
    使用从建筑物散点生成的数据
    """
    # 散点数据（从JSON文件加载）
    population_data = [
'''
        
        # 添加所有散点数据
        for i, agent in enumerate(agents):
            variables = agent['variables']
            code += f'''        {{'x': {variables['x']}, 'y': {variables['y']}, 'building_id': {variables['building_id']}, 'point_id': {variables['point_id']}, 'floor': {variables['floor']}}}{',' if i < len(agents) - 1 else ''}
'''
        
        code += f'''    ]
    
    num_prey = len(population_data)
    print(f"初始化 {{num_prey}} 个猎物个体")
    
    for i in range(num_prey):
        prey = preyPopulation[i]
        point_data = population_data[i]
        
        # 设置位置坐标
        prey.setVariableFloat("x", point_data['x'])
        prey.setVariableFloat("y", point_data['y'])
        
        # 设置建筑物信息
        prey.setVariableInt("building_id", point_data['building_id'])
        prey.setVariableInt("point_id", point_data['point_id'])
        prey.setVariableInt("floor", point_data['floor'])
    
    print("猎物种群初始化完成")

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
FlameGPU猎物种群初始化代码（随机分布版本）
散点数: {num_points}
"""

import random

def initialize_prey_population(preyPopulation):
    """
    初始化猎物种群（随机分布）
    """
    num_prey = {num_points}
    print(f"初始化 {{num_prey}} 个猎物个体（随机分布）")
    
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