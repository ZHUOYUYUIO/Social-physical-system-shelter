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
agent.newVariableInt("pushed_out",0)
agent.newVariableFloat("exit_x",0)
agent.newVariableFloat("exit_y",0)
agent.newVariableInt("can_go_direct",0)

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
    building_index = -1
    
    for building_idx in range(3):
        intersect_count = 0
        
        # 找到当前建筑物的最后一个有效点索引
        last_valid_idx = 0
        for i in range(20):
            if map_3d[building_idx][i][0] == 0 and map_3d[building_idx][i][1] == 0:
                last_valid_idx = i - 1
                break
            last_valid_idx = i  # 如果所有点都有效
        
        # 如果没有有效点，跳过这个建筑物
        if last_valid_idx < 0:
            continue
        
        # 设置第一个点为最后一个有效点（形成闭合多边形）
        prev_x = map_3d[building_idx][last_valid_idx][0]
        prev_y = map_3d[building_idx][last_valid_idx][1]
        
        for point_idx in range(last_valid_idx + 1):  # 只遍历有效点
            curr_x = map_3d[building_idx][point_idx][0]
            curr_y = map_3d[building_idx][point_idx][1]
            
            # 检查点是否在边界上
            
            # 射线法判断交点
            if ((prev_y > y) != (curr_y > y)) and \
               (x < (curr_x - prev_x) * (y - prev_y) / (curr_y - prev_y + 1e-10) + prev_x):
                intersect_count += 1
            
            prev_x = curr_x
            prev_y = curr_y
        
        if intersect_count % 2 == 1:
            in_any_building = 1
            building_index = building_idx
            break
    
    pyflamegpu.setVariableInt("in_building", in_any_building)
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
    push_dx = exit_x - start_x
    push_dy = exit_y - start_y
    
    # 如果方向太小，使用默认方向
    if push_dx * push_dx + push_dy * push_dy < 0.0001:
        push_dx = 1.0
        push_dy = 0.0
    
    m= math.sqrtf(push_dx*push_dx+push_dy*push_dy)
    ddx=push_dx/m*0.1
    ddy=push_dy/m*0.1


    # 向外移动
    new_x = exit_x + ddx
    new_y = exit_y + ddy
    
    drift = new_x - start_x
    pyflamegpu.setVariableFloat("exit_x", new_x)
    pyflamegpu.setVariableFloat("exit_y", new_y)
    pyflamegpu.setVariableInt("pushed_out", 1)
    pyflamegpu.setVariableFloat("drift", drift)
    
    return pyflamegpu.ALIVE

###
#这里需要注意后面线段与几何体的边是否相交，来判断。
##
@pyflamegpu.agent_function
def can_go_direct(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageNone):
    x = pyflamegpu.getVariableFloat("x")
    y = pyflamegpu.getVariableFloat("y")
    map_3d = pyflamegpu.environment.getMacroPropertyInt("map_3d", 3, 20, 2)
    shelter_x = 1.0
    shelter_y = 9.0
    
    # 初始化结果为可以直接到达
    can_go = 1
    
    # 遍历所有建筑物
    for building_idx in range(3):
        # 找到当前建筑物的最后一个有效点索引
        last_valid_idx = -1
        for i in range(20):
            if map_3d[building_idx][i][0] == 0 and map_3d[building_idx][i][1] == 0:
                last_valid_idx = i - 1
                break
            last_valid_idx = i  # 如果所有点都有效
        
        # 如果没有有效点，跳过这个建筑物
        if last_valid_idx < 1:  # 至少需要2个点才能形成边
            continue
        
        # 遍历建筑物的所有边
        for i in range(last_valid_idx + 1):
            # 获取当前边的两个端点
            x1 = float(map_3d[building_idx][i][0])
            y1 = float(map_3d[building_idx][i][1])
            # 获取下一个端点（如果是最后一个点，则连接到第一个点形成闭合多边形）
            next_idx = (i + 1) % (last_valid_idx + 1)
            x2 = float(map_3d[building_idx][next_idx][0])
            y2 = float(map_3d[building_idx][next_idx][1])
            
            # 使用线段相交算法判断路径是否被阻挡
            # 线段1: (x,y) -> (shelter_x, shelter_y)
            # 线段2: (x1,y1) -> (x2,y2)
            
            # 第一步：MBR快速排斥实验
            if max(x, shelter_x) >= min(x1, x2) and \
               max(x1, x2) >= min(x, shelter_x) and \
               max(y, shelter_y) >= min(y1, y2) and \
               max(y1, y2) >= min(y, shelter_y):
                
                # 第二步：跨立实验
                # 计算向量叉积
                cross1 = (shelter_x - x) * (y1 - y) - (x1 - x) * (shelter_y - y)
                cross2 = (shelter_x - x) * (y2 - y) - (x2 - x) * (shelter_y - y)
                cross3 = (x2 - x1) * (y - y1) - (x - x1) * (y2 - y1)
                cross4 = (x2 - x1) * (shelter_y - y1) - (shelter_x - x1) * (y2 - y1)
                
                # 如果两条线段相交，则不能直接到达
                if cross1 * cross2 <= 0 and cross3 * cross4 <= 0:
                    can_go = 0
                    break  # 只要有一个阻挡就退出内层循环
        
        if can_go == 0:
            break  # 退出外层循环
    
    pyflamegpu.setVariableInt("can_go_direct", can_go)
    return pyflamegpu.ALIVE


map_get_translated = pyflamegpu.codegen.translate(map_get)
map_get_fn = agent.newRTCFunction("map_get",map_get_translated)

push_start_out_of_obstacle_translated = pyflamegpu.codegen.translate(push_start_out_of_obstacle)
push_start_out_of_obstacle_fn = agent.newRTCFunction("push_start_out_of_obstacle",push_start_out_of_obstacle_translated)

can_go_direct_translated = pyflamegpu.codegen.translate(can_go_direct)
can_go_direct_fn = agent.newRTCFunction("can_go_direct",can_go_direct_translated)

model.addInitFunction(write_env_hostfn())
model.addExecutionRoot(map_get_fn)
push_start_out_of_obstacle_fn.dependsOn(map_get_fn)
can_go_direct_fn.dependsOn(push_start_out_of_obstacle_fn)
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
    agent.setVariableFloat("x", 1.0)
    agent.setVariableFloat("y", 7.1)

cuda_model.setPopulationData(AgentPopulation)

cuda_model.initialise(sys.argv)

# Attach the logging config
cuda_model.setStepLog(step_log_cfg)


# Only run this block if pyflamegpu was built with visualisation support
if pyflamegpu.VISUALISATION:
    # Create visualisation
    m_vis = cuda_model.getVisualisation()
    # Set the initial camera location and speed
    INIT_CAM = ENV_WIDTH * 1.25

    m_vis.setInitialCameraLocation(INIT_CAM, INIT_CAM, INIT_CAM)
    m_vis.setCameraSpeed(0.01)
    m_vis.setSimulationSpeed(25)
    # Add "point" agents to the visualisation
    point_agt = m_vis.addAgent("point")
    # Location variables have names "x" and "y" so will be used by default
    point_agt.setModel(pyflamegpu.ICOSPHERE);
    point_agt.setModelScale(1/10.0);
    # Mark the environment bounds
    pen = m_vis.newPolylineSketch(1, 1, 1, 0.2)
    # 第一个障碍物：正方形（4个点）
    pen.addVertex(2, 2, 0)
    pen.addVertex(4, 2, 0)
    pen.addVertex(4, 4, 0)
    pen.addVertex(2, 4, 0)
    pen.addVertex(2, 2, 0)  # 回到起点形成闭合

    # 第二个障碍物：不规则六边形（6个点）
    pen.addVertex(6, 1, 0)
    pen.addVertex(8, 1, 0)
    pen.addVertex(9, 2, 0)
    pen.addVertex(8, 3, 0)
    pen.addVertex(6, 3, 0)
    pen.addVertex(5, 2, 0)
    pen.addVertex(6, 1, 0)  # 回到起点形成闭合

    # 第三个障碍物：另一个不规则六边形（6个点） 
    pen.addVertex(3, 6, 0)
    pen.addVertex(5, 6, 0)
    pen.addVertex(6, 7, 0)
    pen.addVertex(5, 8, 0)
    pen.addVertex(3, 8, 0)
    pen.addVertex(2, 7, 0)
    pen.addVertex(3, 6, 0)  # 回到起点形成闭合


    # Open the visualiser window
    m_vis.activate()

# Run the simulation
cuda_model.simulate()

out_pop = pyflamegpu.AgentVector(model.Agent("point"))
cuda_model.getPopulationData(out_pop)
for agent in out_pop:
    print("value: %f"%(agent.getVariableInt("in_building")))
    #print("value: %f"%(agent.getVariableInt("on_boundary")))
    print("value: %f"%(agent.getVariableInt("building_index")))
    print("value: %f"%(agent.getVariableInt("pushed_out")))
    print("value: %f"%(agent.getVariableFloat("drift")))
    print("value: %f"%(agent.getVariableFloat("x")))
    print("value: %f"%(agent.getVariableFloat("y")))
    print("value: %f"%(agent.getVariableFloat("exit_x")))
    print("value: %f"%(agent.getVariableFloat("exit_y")))
    print("value: %f"%(agent.getVariableInt("can_go_direct")))

    print("=======")

if pyflamegpu.VISUALISATION:
    # Keep the visualisation window active after the simulation has completed
    m_vis.join()