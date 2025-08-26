from pyflamegpu import *
import pyflamegpu.codegen
import sys
import math

# Define an host function called write_env_hostfn
class write_env_hostfn(pyflamegpu.HostFunction):
  
  def __init__(self):
    super().__init__()  
  
  def run(self,FLAMEGPU):

    FLAMEGPU.environment.importMacroProperty("map_3d", "map_3d.json");

model = pyflamegpu.ModelDescription("F_MAP_tutorial")


env = model.Environment()
env.newMacroPropertyInt("map_3d", 3, 20,2)  



# Define an agent named point
agent = model.newAgent("point")
# Assign the agent some variables (ID is implicit to agents, so we don't define it ourselves)
agent.newVariableFloat("x")
agent.newVariableFloat("y")
agent.newVariableFloat("test_value")
agent.newVariableFloat("test_value1")
agent.newVariableFloat("drift", 0)
agent.newVariableInt("building_index",0)
agent.newVariableInt("in_building",0)
agent.newVariableInt("on_boundary",0) 
agent.newVariableInt("pushed_out",0)

def mult(a,b):
  return a*b

@pyflamegpu.device_function
def mult(a: float, b: float) -> float :
  return abs(a+b)

@pyflamegpu.device_function
def dist(x: float, y: float) -> float:
  return math.sqrtf(x*x+y*y)

@pyflamegpu.device_function
def min(a: float, b: float) -> float:
  return a if a < b else b

@pyflamegpu.device_function
def max(a: float, b: float) -> float:
  return a if a > b else b

'''
@pyflamegpu.agent_function
def map_get(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageNone):


    map_3d = pyflamegpu.environment.getMacroPropertyInt("map_3d", 3, 20,2)
    x = pyflamegpu.getVariableFloat("x")
    y = pyflamegpu.getVariableFloat("y")
    for i in range(3):
        map_3d[i][0][0] #这是第i个建筑物地第一个点的x坐标
        map_3d[i][0][1] #这是第i个建筑物地第一个点的y坐标
        
    
    




    pyflamegpu.setVariableFloat("test_value", inside)
    pyflamegpu.setVariableFloat("test_value1", a)
    return pyflamegpu.ALIVE
'''


@pyflamegpu.agent_function
def map_get(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageNone):
    map_3d = pyflamegpu.environment.getMacroPropertyInt("map_3d", 3, 20, 2)
    x = pyflamegpu.getVariableFloat("x")
    y = pyflamegpu.getVariableFloat("y")
    
    in_any_building = 0
    on_boundary = 0
    building_index = -1
    
    for building_idx in range(3):
        intersect_count = 0
        prev_x = map_3d[building_idx][19][0]
        prev_y = map_3d[building_idx][19][1]
        
        for point_idx in range(20):
            curr_x = map_3d[building_idx][point_idx][0]
            curr_y = map_3d[building_idx][point_idx][1]
            

            if curr_x == 0 and curr_y == 0:
                break
            

            if (min(prev_x, curr_x) <= x <= max(prev_x, curr_x) and 
                min(prev_y, curr_y) <= y <= max(prev_y, curr_y)):

                if abs((curr_y - prev_y) * x - (curr_x - prev_x) * y + curr_x * prev_y - curr_y * prev_x) < 1e-6:
                    on_boundary = 1
                    in_any_building = 1
                    building_index = building_idx
                    break
            
            # ray
            if ((prev_y > y) != (curr_y > y)) and (x < (curr_x - prev_x) * (y - prev_y) / (curr_y - prev_y + 1e-10) + prev_x):
                intersect_count += 1
            
            prev_x = curr_x
            prev_y = curr_y
        
        if on_boundary == 1:
            break
        
        if intersect_count % 2 == 1:
            in_any_building = 1
            building_index = building_idx
            break
    
    pyflamegpu.setVariableInt("in_building", in_any_building)
    pyflamegpu.setVariableInt("on_boundary", on_boundary)
    pyflamegpu.setVariableInt("building_index", building_index)
    
    return pyflamegpu.ALIVE

@pyflamegpu.agent_function
def push_start_out_of_obstacle(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageNone):
    start_x = pyflamegpu.getVariableFloat("x")
    start_y = pyflamegpu.getVariableFloat("y")
    building_idx = pyflamegpu.getVariableInt("building_index")
    
    if building_idx < 0:
        return pyflamegpu.ALIVE
    
    map_3d = pyflamegpu.environment.getMacroPropertyInt("map_3d", 3, 20, 2)
    
    # 找到多边形点数
    point_count = 0
    for j in range(20):
        if map_3d[building_idx][j][0] == 0 and map_3d[building_idx][j][1] == 0:
            break
        point_count += 1
    
    min_dist_sq = 1000000.0
    exit_x = start_x
    exit_y = start_y
    
    # 遍历所有边，找到最近的边
    for i in range(point_count):
        # 当前边的两个端点
        p1_x = float(map_3d[building_idx][i][0])
        p1_y = float(map_3d[building_idx][i][1])
        next_idx = (i + 1) % point_count
        p2_x = float(map_3d[building_idx][next_idx][0])
        p2_y = float(map_3d[building_idx][next_idx][1])
        
        # 计算边的向量
        edge_dx = p2_x - p1_x
        edge_dy = p2_y - p1_y
        edge_len_sq = edge_dx * edge_dx + edge_dy * edge_dy
        
        if edge_len_sq < 0.0001:
            # 边太短，当作点处理
            dx = start_x - p1_x
            dy = start_y - p1_y
            dist_sq = dx * dx + dy * dy
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                exit_x = p1_x
                exit_y = p1_y
        else:
            # 计算投影参数t
            t_val = ((start_x - p1_x) * edge_dx + (start_y - p1_y) * edge_dy) / edge_len_sq
            
            # 限制t在[0,1]范围内
            if t_val < 0:
                t_val = 0
            elif t_val > 1:
                t_val = 1
            
            # 计算投影点
            proj_x = p1_x + t_val * edge_dx
            proj_y = p1_y + t_val * edge_dy
            
            # 计算距离
            dx = start_x - proj_x
            dy = start_y - proj_y
            dist_sq = dx * dx + dy * dy
            
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                exit_x = proj_x
                exit_y = proj_y
    
    # 计算推出方向（从投影点指向起点）
    push_dx = start_x - exit_x
    push_dy = start_y - exit_y
    
    # 如果方向太小，使用默认方向
    if push_dx * push_dx + push_dy * push_dy < 0.0001:
        push_dx = 1.0
        push_dy = 0.0
    
    # 向外移动
    new_x = exit_x + push_dx
    new_y = exit_y + push_dy
    
    pyflamegpu.setVariableFloat("x", new_x)
    pyflamegpu.setVariableFloat("y", new_y)
    pyflamegpu.setVariableInt("pushed_out", 1)
    
    return pyflamegpu.ALIVE


map_get_translated = pyflamegpu.codegen.translate(map_get)
map_get_fn = agent.newRTCFunction("map_get",map_get_translated)

push_start_out_of_obstacle_translated = pyflamegpu.codegen.translate(push_start_out_of_obstacle)
push_start_out_of_obstacle_fn = agent.newRTCFunction("push_start_out_of_obstacle",push_start_out_of_obstacle_translated)

model.addInitFunction(write_env_hostfn())
model.addExecutionRoot(map_get_fn)
push_start_out_of_obstacle_fn.dependsOn(map_get_fn)
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

AGENT_COUNT=3
ENV_WIDTH=10
AgentPopulation = pyflamegpu.AgentVector(model.Agent("point"), AGENT_COUNT)
for i in range(AGENT_COUNT):
    agent = AgentPopulation[i]
    agent.setVariableFloat("x", random.uniform(0, ENV_WIDTH))
    agent.setVariableFloat("y", random.uniform(0, ENV_WIDTH))

cuda_model.setPopulationData(AgentPopulation)

cuda_model.initialise(sys.argv)

# Attach the logging config
cuda_model.setStepLog(step_log_cfg)

# Run the simulation
cuda_model.simulate()

out_pop = pyflamegpu.AgentVector(model.Agent("point"))
cuda_model.getPopulationData(out_pop)
for agent in out_pop:
    print("value: %f"%(agent.getVariableInt("in_building")))
    print("value: %f"%(agent.getVariableInt("on_boundary")))
    print("value: %f"%(agent.getVariableInt("building_index")))
    print("value: %f"%(agent.getVariableInt("pushed_out")))
