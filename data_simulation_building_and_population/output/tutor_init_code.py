#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlameGPU tutor 代理初始化代码
基于 tutor_points.json（每栋楼每层一个 tutor）生成
"""

import json
import os
from pyflamegpu import *  # noqa: F401,F403
import pyflamegpu.codegen  # noqa: F401
import sys  # noqa: F401


def initialize_tutor_agent_population(
    model,
    cuda_model,
    tutor_file="data/output/tutor_points.json",
    z_per_floor=3.0,
):
    """
    初始化 tutor 代理种群（每栋楼每层 1 个 tutor）

    期望模型中 tutor_agent 至少定义以下变量（与 notebook `src/ver1 copy 3.ipynb` 对齐）：
    - x (float)
    - y (float)
    - building_id (int)
    - point_id (int)   # 这里用 tutor_points.json 的 source_point_id 作为 point_id
    - z (float)        # 用 tutor_points.json 的 floor 计算 z = floor * z_per_floor
    """
    if not os.path.exists(tutor_file):
        print(f"❌ 找不到 tutor 数据文件: {tutor_file}")
        print("请先运行：python data/generate_tutor_agents.py")
        return

    try:
        with open(tutor_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        tutors = data.get("tutor_agents", [])
        if not tutors:
            print("❌ tutor 数据为空（tutor_agents 为空）")
            return

        num_tutor_agents = len(tutors)
        print(f"初始化 {num_tutor_agents} 个 tutor 代理个体")

        tutorAgentPopulation = pyflamegpu.AgentVector(model.Agent("tutor_agent"), num_tutor_agents)

        for i in range(num_tutor_agents):
            tutor_agent = tutorAgentPopulation[i]
            t = tutors[i]

            # 位置
            tutor_agent.setVariableFloat("x", float(t["x"]))
            tutor_agent.setVariableFloat("y", float(t["y"]))

            # 建筑信息
            tutor_agent.setVariableInt("building_id", int(t["building_id"]))

            # 与现有模型变量对齐：point_id
            tutor_agent.setVariableInt("point_id", int(t.get("source_point_id", t.get("tutor_id", i))))

            # 3D 高度（如果模型未定义 z 变量，这行会报错；请在模型里加上 z 变量或注释掉）
            tutor_agent.setVariableFloat("z", float(t.get("floor", 0)) * float(z_per_floor))

        cuda_model.setPopulationData(tutorAgentPopulation)
        print("tutor 代理种群初始化完成")

    except Exception as e:
        print(f"❌ 加载 tutor 数据失败: {e}")


# 使用示例（模型侧）：
# model = pyflamegpu.ModelDescription("My Model")
# tutor = model.newAgent("tutor_agent")
# tutor.newVariableFloat("x")
# tutor.newVariableFloat("y")
# tutor.newVariableInt("building_id")
# tutor.newVariableInt("point_id")
# tutor.newVariableFloat("z")
# ...
# init_tutor = model.newAgentFunction("init_tutor_population")
# init_tutor.setFunction(initialize_tutor_agent_population)


