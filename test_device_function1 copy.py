import math
import numpy as np
from pyflamegpu import *
import pyflamegpu.codegen


class write_env_hostfn(pyflamegpu.HostFunction):
  
  def __init__(self):
    super().__init__()  
  
  def run(self,FLAMEGPU):

      # Retrieve the environment macro property bar of type int array[5][5]

      # Update some of the values
      # foo = 12.0; is not allowed
      FLAMEGPU.environment.importMacroProperty("obstacle1", "obstacle1.json");
      FLAMEGPU.environment.importMacroProperty("obstacle2", "obstacle2.json");
      FLAMEGPU.environment.importMacroProperty("obstacle3", "obstacle3.json");

model = pyflamegpu.ModelDescription("F_MAP_tutorial1")

env = model.Environment()
env.newMacroPropertyFloat("obstacle1", 2, 4)  
env.newMacroPropertyInt("obstacle2", 2, 6)
env.newMacroPropertyInt("obstacle3", 2, 6) 

@pyflamegpu.device_function
def min(a: float, b: float) -> float:
  return a if a < b else b
@pyflamegpu.device_function
def max(a: float, b: float) -> float:
  return a if a > b else b

@pyflamegpu.agent_function
def find_path_ultra_consolidated(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageNone):
    x = pyflamegpu.getVariableFloat("x")
    y = pyflamegpu.getVariableFloat("y")

    obstacle1 = pyflamegpu.environment.getMacroPropertyFloat("obstacle1", 2, 4)
    n = 4
    inside = 0

    # 初始化第一个顶点
    p1x = obstacle1[0][0]
    p1y = obstacle1[0][1]

    for i in range(1, n + 1):
        # 获取当前顶点（循环处理最后一个顶点与第一个顶点的连接）
        p2x = obstacle1[i % n][0]
        p2y = obstacle1[i % n][1]

        # 射线法判断点是否在多边形内
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    xinters = 0.0  # 初始化 xinters
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        if inside == 0:
                            inside = 1
                        else:
                            inside = 0

        # 为下一次迭代准备
        p1x = p2x
        p1y = p2y

    pyflamegpu.setVariableFloat("test_value", inside)
    pyflamegpu.setVariableFloat("test_value1", obstacle1[1][1])
    return pyflamegpu.ALIVE




# Define an agent named point
agent = model.newAgent("point")
# Assign the agent some variables (ID is implicit to agents, so we don't define it ourselves)
agent.newVariableFloat("x")
agent.newVariableFloat("y")

agent.newVariableArrayFloat("location", 10)  # 路径点数组，最大100个点

agent.newVariableFloat("drift", 0)





find_path_ultra_consolidated_translated = pyflamegpu.codegen.translate(find_path_ultra_consolidated)
find_path_ultra_consolidated_fn = agent.newRTCFunction("find_path_ultra_consolidated",find_path_ultra_consolidated_translated)

model.addInitFunction(write_env_hostfn())
model.addExecutionRoot(find_path_ultra_consolidated_fn)
model.generateLayers()


# Specify the desired StepLoggingConfig
step_log_cfg = pyflamegpu.StepLoggingConfig(model)
# Log every step
step_log_cfg.setFrequency(1) 
# Include the mean of the "point" agent population's variable 'drift'
step_log_cfg.agent("point").logMeanFloat("drift")

# Create and init the simulation
cuda_model = pyflamegpu.CUDASimulation(model)

import random
import sys

AGENT_COUNT=3
ENV_WIDTH=10
AgentPopulation = pyflamegpu.AgentVector(model.Agent("point"), AGENT_COUNT)
for i in range(AGENT_COUNT):
    agent = AgentPopulation[i]
    agent.setVariableFloat("x", random.uniform(0, ENV_WIDTH))
    agent.setVariableFloat("y", random.uniform(0, ENV_WIDTH))


cuda_model.initialise(sys.argv)

# Attach the logging config
cuda_model.setStepLog(step_log_cfg)

# Run the simulation
cuda_model.simulate()

out_pop = pyflamegpu.AgentVector(model.Agent("point"))
cuda_model.getPopulationData(out_pop)
for agent in out_pop:
    print("value: %f"%(agent.getVariableFloat("test_value1")))