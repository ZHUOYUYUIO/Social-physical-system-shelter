import sys
import os
from pyflamegpu import *
import pyflamegpu.codegen
import sys
# 切换到你的项目根目录
project_root = r"D:\programming\python_script\socio-physical system for shelter"
os.chdir(project_root)

# 添加 data/output 目录到 Python 路径
sys.path.append('data/output')


from deap import algorithms
from deap import base
from deap import creator
from deap import tools

from pyflamegpu import *
import pyflamegpu.codegen
import sys
import math
import random

model = pyflamegpu.ModelDescription("F_MAP_tutorial")


# Define an host function called directed_graph_hostfn
class directed_graph_hostfn(pyflamegpu.HostFunction):
  def run(self,FLAMEGPU):
    # Fetch a handle to the directed graph
    fgraph = FLAMEGPU.environment.getDirectedGraph("fgraph")
    # Import a different graph
    fgraph.importGraph("data/env_data/expanded_visibility_graph_renumbered.json");



# Define an host function called write_env_hostfn
class write_env_hostfn(pyflamegpu.HostFunction):
  
  def __init__(self):
    super().__init__()  
  
  def run(self,FLAMEGPU):

      # Retrieve the environment macro property bar of type int array[5][5]

      # Update some of the values
      # foo = 12.0; is not allowed
      FLAMEGPU.environment.importMacroProperty("map", "data/env_data/attraction_matrix_familiar_points.json");



# Define a message of type MessageSpatial2D named location
# MessageSpatial2D: Each agent outputs a message at a specific location in 2D space
# agents only read messages located close to a particular search origin（搜素的中心点）.
# 可以获取一定距离内的消息
message = model.newMessageSpatial3D("location")
# Configure the message list

message.setMin(0, 0,0)
message.setMax(500, 500,100)
message.setRadius(200)
# Add extra variables to the message
# X Y (Z) are implicit for spatial messages
message.newVariableID("id")

stairwell_message = model.newMessageSpatial3D("stairwell_location")
# Configure the message list

stairwell_message.setMin(0, 0,0)
stairwell_message.setMax(500, 500,100)
stairwell_message.setRadius(200)
# Add extra variables to the message
# X Y (Z) are implicit for spatial messages
stairwell_message.newVariableID("id")
stairwell_message.newVariableInt("building_id")
stairwell_message.newVariableFloat("outstop_x")
stairwell_message.newVariableFloat("outstop_y")
stairwell_message.newVariableInt("graph_id")

shelter_message = model.newMessageSpatial3D("shelter_location")
shelter_message.setMin(0, 0,0)
shelter_message.setMax(1000, 1000,200)
shelter_message.setRadius(1000)
shelter_message.newVariableID("id")
shelter_message.newVariableInt("shelter_id")
shelter_message.newVariableInt("graph_id")

# Assign the agent some variables (ID is implicit to agents, so we don't define it ourselves)
student_agent = model.newAgent("student_agent")
student_agent.newVariableFloat("x")
student_agent.newVariableFloat("y")
student_agent.newVariableInt("building_id")
student_agent.newVariableInt("point_id")
student_agent.newVariableFloat("z")
student_agent.newVariableFloat("drift", 0)
student_agent.newVariableInt("target_stairwell_id", -1)
student_agent.newVariableFloat("target_stairwell_x")
student_agent.newVariableFloat("target_stairwell_y")
student_agent.newVariableInt("target_shelter_id", -1)
student_agent.newVariableInt("is_set_shelter", -1)
student_agent.newVariableInt("evacuate_status", 1)
student_agent.newVariableInt("zigzag_dir", 1)
student_agent.newVariableFloat("target_shelter_x")
student_agent.newVariableFloat("target_shelter_y")
# stairwell-connected out stop point:
student_agent.newVariableFloat("outstop_x")
student_agent.newVariableFloat("outstop_y")

student_agent.newVariableInt("start_id")
student_agent.newVariableInt("end_id")
# for road planning





student_agent.newVariableFloat("bar_0_0")
student_agent.newVariableInt("start_vertex_id",131)
student_agent.newVariableInt("end_vertex_id",175)
student_agent.newVariableInt("path_length")
student_agent.newVariableArrayInt("shortest_path", 20)  # 存储最短路径的顶点ID数组，16个顶点的图最长路径不超过20





student_agent.newVariableArrayFloat("shortest_value",176, [-1.0] * 176)

# Dijkstra算法需要的变量
student_agent.newVariableArrayFloat("distances", 176, [999999.0] * 176)  # 距离数组，初始化为无穷大
student_agent.newVariableArrayInt("visited", 176, [0] * 176)  # 访问标记数组
student_agent.newVariableArrayInt("previous", 176, [-1] * 176)  # 前驱节点数组
student_agent.newVariableInt("vertex_count")  # 顶点数量
student_agent.newVariableInt("edge_count")  # 边数量
student_agent.newVariableInt("is_set_shortest_path", 0)

#for move
student_agent.newVariableInt("path_point", 1)

student_agent.newVariableInt("in_shelter",0)


stairwell_agent = model.newAgent("stairwell_agent")
stairwell_agent.newVariableFloat("x")
stairwell_agent.newVariableFloat("y")
stairwell_agent.newVariableInt("stairwell_id")
stairwell_agent.newVariableInt("building_id")
stairwell_agent.newVariableFloat("outstop_x")
stairwell_agent.newVariableFloat("outstop_y")
stairwell_agent.newVariableInt("graph_id")
stairwell_agent.newVariableFloat("z")

shelter_agent = model.newAgent("shelter_agent")
shelter_agent.newVariableFloat("x")
shelter_agent.newVariableFloat("y")
shelter_agent.newVariableInt("shelter_id")
shelter_agent.newVariableFloat("z")
shelter_agent.newVariableInt("graph_id")



# Fetch the model's environment
env = model.Environment()
# Declare a new directed graph named 'fgraph'
fgraph = env.newDirectedGraph("fgraph")
# Attach an float[2] property 'bar' to vertices
fgraph.newVertexPropertyArrayFloat("bar", 2)
# Attach an int property 'foo' to edges
fgraph.newEdgePropertyFloat("foo")
env.newMacroPropertyFloat("map", 700, 700)

# 首先我要import一个graph


@pyflamegpu.agent_function
def output_message(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageSpatial3D):
    message_out.setVariableUInt("id", pyflamegpu.getID())
    message_out.setLocation(
        pyflamegpu.getVariableFloat("x"),
        pyflamegpu.getVariableFloat("y"),
        pyflamegpu.getVariableFloat("z")
        )
    return pyflamegpu.ALIVE

@pyflamegpu.agent_function
def stairwell_output_message(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageSpatial3D):
    message_out.setVariableUInt("id", pyflamegpu.getID())
    message_out.setVariableInt("building_id", pyflamegpu.getVariableInt("building_id"))
    message_out.setVariableFloat("outstop_x", pyflamegpu.getVariableFloat("outstop_x"))
    message_out.setVariableFloat("outstop_y", pyflamegpu.getVariableFloat("outstop_y"))
    message_out.setVariableInt("graph_id", pyflamegpu.getVariableInt("graph_id"))
    message_out.setLocation(
        pyflamegpu.getVariableFloat("x"),
        pyflamegpu.getVariableFloat("y"),
        pyflamegpu.getVariableFloat("z")
        )
    return pyflamegpu.ALIVE

@pyflamegpu.agent_function
def shelter_output_message(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageSpatial3D):
    message_out.setVariableUInt("id", pyflamegpu.getID())
    message_out.setVariableInt("shelter_id", pyflamegpu.getVariableInt("shelter_id"))
    message_out.setLocation(
        pyflamegpu.getVariableFloat("x"),
        pyflamegpu.getVariableFloat("y"),
        pyflamegpu.getVariableFloat("z")
        )
    message_out.setVariableInt("graph_id", pyflamegpu.getVariableInt("graph_id"))
    return pyflamegpu.ALIVE

@pyflamegpu.agent_function
def set_target_stairwell(message_in: pyflamegpu.MessageSpatial3D, message_out: pyflamegpu.MessageNone):
    # Get this agent's x, y, z variables
    x = pyflamegpu.getVariableFloat("x")
    y = pyflamegpu.getVariableFloat("y")
    z = pyflamegpu.getVariableFloat("z")
    target_stairwell_id = pyflamegpu.getVariableInt("target_stairwell_id")

    min_dist = 100000
    if target_stairwell_id == -1:
        for message in message_in(x,y,z):
            # Process the message's variables e.g.
            if message.getVariableInt("building_id") == pyflamegpu.getVariableInt("building_id"):
                #找到距离最近的楼梯
                # 找到距离最近的楼梯

                stairwell_x = message.getVariableFloat("x")
                stairwell_y = message.getVariableFloat("y")

                # 计算欧氏距离
                dx = stairwell_x - x
                dy = stairwell_y - y

                dist = math.sqrtf(dx*dx + dy*dy)
                if dist < min_dist:
                    min_dist = dist
                    nearest_stairwell_id = message.getVariableInt("id")
                    # 记录最近楼梯的坐标
                    pyflamegpu.setVariableInt("target_stairwell_id", nearest_stairwell_id)
                    pyflamegpu.setVariableFloat("target_stairwell_x", stairwell_x)
                    pyflamegpu.setVariableFloat("target_stairwell_y", stairwell_y)
                    pyflamegpu.setVariableInt("start_id", message.getVariableInt("graph_id"))
                    pyflamegpu.setVariableFloat("outstop_x", message.getVariableFloat("outstop_x"))
                    pyflamegpu.setVariableFloat("outstop_y", message.getVariableFloat("outstop_y")) 

            #设置目标楼梯
    return pyflamegpu.ALIVE


@pyflamegpu.agent_function
def set_target_shelter_first(message_in: pyflamegpu.MessageSpatial3D, message_out: pyflamegpu.MessageNone):
    """按权重概率选择 shelter（含容量过滤）。

    权重 w = familiarity(m,n) / dist
    P(选择 i) = w_i / sum(w)
    """
    x = pyflamegpu.getVariableFloat("x")
    y = pyflamegpu.getVariableFloat("y")
    z = pyflamegpu.getVariableFloat("z")

    if pyflamegpu.getVariableInt("is_set_shelter") != -1:
        return pyflamegpu.ALIVE

    fmap = pyflamegpu.environment.getMacroPropertyFloat("map", 700, 700)

    total_w = 0.0
    for message in message_in(x, y, z):
        # 容量机制：跳过满员 shelter（如果你的 shelter_message 没有该字段，可删除此判断）
        if message.getVariableInt("available") == 0:
            continue

        shelter_x = message.getVariableFloat("x")
        shelter_y = message.getVariableFloat("y")

        dx = shelter_x - x
        dy = shelter_y - y
        dist = math.sqrtf(dx * dx + dy * dy)
        if dist <= 1e-6:
            continue

        m = int(shelter_x)
        n = int(shelter_y)
        if m < 0:
            m = 0
        elif m > 699:
            m = 699
        if n < 0:
            n = 0
        elif n > 699:
            n = 699

        familiarity = math.sqrtf(fmap[m][n]) + 200.0
        w = familiarity / dist
        if w > 0.0:
            total_w += w

    if total_w <= 0.0:
        return pyflamegpu.ALIVE

    r = pyflamegpu.random.uniformFloat() * total_w
    cum_w = 0.0

    for message in message_in(x, y, z):
        if message.getVariableInt("available") == 0:
            continue

        shelter_x = message.getVariableFloat("x")
        shelter_y = message.getVariableFloat("y")

        dx = shelter_x - x
        dy = shelter_y - y
        dist = math.sqrtf(dx * dx + dy * dy)
        if dist <= 1e-6:
            continue

        m = int(shelter_x)
        n = int(shelter_y)
        if m < 0:
            m = 0
        elif m > 699:
            m = 699
        if n < 0:
            n = 0
        elif n > 699:
            n = 699

        familiarity = math.sqrtf(fmap[m][n]) + 200.0
        w = familiarity / dist
        if w <= 0.0:
            continue

        cum_w += w
        if cum_w >= r:
            pyflamegpu.setVariableInt("target_shelter_id", message.getVariableInt("shelter_id"))
            pyflamegpu.setVariableFloat("target_shelter_x", shelter_x)
            pyflamegpu.setVariableFloat("target_shelter_y", shelter_y)
            pyflamegpu.setVariableInt("is_set_shelter", 1)
            pyflamegpu.setVariableInt("end_id", message.getVariableInt("graph_id"))
            break

    return pyflamegpu.ALIVE

                

### 好消息，根据我的test_set_get_in_onefunc.py，我可以实现动态的数据存储啦！！！
@pyflamegpu.agent_function
def ShortestPathFn(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageNone):
    """
    使用Dijkstra算法实现最短路径规划
    """
    fgraph = pyflamegpu.environment.getDirectedGraph("fgraph")

    # 定义常量
    INF = 999999.0
    vertex_count = 176  # 假设图中有16个顶点

    # 获取起点和终点ID（可以从agent变量中获取，或者设置为固定值）
    start_vertex_id = pyflamegpu.getVariableInt("end_id")
    end_vertex_id = pyflamegpu.getVariableInt("start_id")

    ###
    # 起点是哪个，我们就把它的list对应的i，设置为0。
    ###
    pyflamegpu.setVariableFloatArray176("shortest_value", start_vertex_id, 0)

    #然后遍历所有顶点（1-16），除了我们的起点id外，如果它和起点id有连线，我们就把它的list对应的i，设置为起点到它的距离。

    #遍历起点的id，线的值就设置为shortest_value的起点对应的i的值+边的值。
    # 先初始化所有顶点的shortest_value为INF
    for i in range(176):
        if i != start_vertex_id:
            pyflamegpu.setVariableFloatArray176("shortest_value", i, INF)

    # 遍历起点连接的边，设置对应的shortest_value
    for edge in fgraph.outEdges(start_vertex_id):
        # 获取边的目的顶点索引
        dest_vertex_index = edge.getEdgeDestination()
        # 获取边的foo属性
        foo = edge.getPropertyInt("foo")

        # 将foo值存储到对应顶点ID的位置
        pyflamegpu.setVariableFloatArray176("shortest_value", dest_vertex_index, foo)
            


    # 获取起点和终点的索引
    start_index = fgraph.getVertexIndex(start_vertex_id)
    end_index = fgraph.getVertexIndex(end_vertex_id)

    # 初始化起点距离为0
    pyflamegpu.setVariableFloatArray176("distances", start_index, 0.0)
    # 初始化起点前驱为-1
    pyflamegpu.setVariableIntArray176("previous", start_index, -1)
    # 初始化其他顶点的距离为无穷大，前驱为-1
    for i in range(vertex_count):
        if i != start_index:
            pyflamegpu.setVariableFloatArray176("distances", i, INF)
            pyflamegpu.setVariableIntArray176("previous", i, -1)
        pyflamegpu.setVariableIntArray176("visited", i, 0)

    # Dijkstra算法主循环
    for _ in range(vertex_count):
        # 找到当前未访问顶点中距离最小的顶点
        min_distance = INF      
        current_index = -1

        for i in range(vertex_count):
            visited_i = pyflamegpu.getVariableIntArray176("visited", i)
            distance_i = pyflamegpu.getVariableFloatArray176("distances", i) 
            if visited_i == 0 and distance_i < min_distance:
                min_distance = distance_i
                current_index = i

        if current_index == -1 or min_distance == INF:
            break

        # 标记当前顶点为已访问
        pyflamegpu.setVariableIntArray176("visited", current_index, 1)   

        # 如果到达终点，可以提前结束
        if current_index == end_index:
            break


        # 遍历当前顶点的所有出边
        for edge in fgraph.outEdges(current_index):

            dest_index = edge.getEdgeDestination()

            visited_dest = pyflamegpu.getVariableIntArray176("visited", dest_index)
            if visited_dest == 0:
                # 获取边的权重
                edge_weight = edge.getPropertyFloat("foo")
                current_distance = pyflamegpu.getVariableFloatArray176("distances", current_index)
                new_distance = current_distance + edge_weight

                dest_distance = pyflamegpu.getVariableFloatArray176("distances", dest_index)
                if new_distance < dest_distance:
                    pyflamegpu.setVariableFloatArray176("distances", dest_index, new_distance)
                    pyflamegpu.setVariableIntArray176("previous", dest_index, current_index)

    # 重建最短路径 - 使用pyflamegpu方法完全避免循环和索引操作

    # 初始化路径数组为-1
    for i in range(20):
        pyflamegpu.setVariableIntArray20("shortest_path", i, -1)

    # 从终点开始重建路径
    current = end_index
    path_index = 0
    path_length = 0

    # 逆向追溯直到起点或前驱为-1
    while current != -1 and path_index < 20:
        vertex_id = fgraph.getVertexID(current)
        pyflamegpu.setVariableIntArray20("shortest_path", path_index, vertex_id)
        path_index += 1
        path_length += 1
        
        # 如果到达起点，停止追溯
        if current == start_index:  # 假设start_index是起点的索引
            break
        
        # 获取前驱节点
        current = pyflamegpu.getVariableIntArray176("previous", current)

    # 设置路径长度
    pyflamegpu.setVariableInt("path_length", path_length)

    # 验证路径是否确实从终点连接到起点
    first_vertex = pyflamegpu.getVariableIntArray20("shortest_path", 0)
    last_vertex = pyflamegpu.getVariableIntArray20("shortest_path", path_length - 1)

    if first_vertex != end_vertex_id or last_vertex != start_vertex_id:
        # 路径不完整，可能需要特殊处理
        pyflamegpu.setVariableInt("path_length", 0)  # 或者标记为无效路径

    pyflamegpu.setVariableInt("is_set_shortest_path", 1)
    return pyflamegpu.ALIVE 

@pyflamegpu.agent_function_condition
def is_set_shortest_path_is_1() -> bool:
    return pyflamegpu.getVariableInt("is_set_shortest_path") == 0

import math

@pyflamegpu.agent_function
def move_to_stairwell(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageSpatial3D):
    target_stairwell_x = pyflamegpu.getVariableFloat("target_stairwell_x")
    target_stairwell_y = pyflamegpu.getVariableFloat("target_stairwell_y")
    x = pyflamegpu.getVariableFloat("x")
    y = pyflamegpu.getVariableFloat("y")
    
    delta_x = target_stairwell_x - x
    delta_y = target_stairwell_y - y

    distance = math.sqrtf(delta_x * delta_x + delta_y * delta_y)

    next_x=0.0
    next_y=0.0
    if distance > 5.0:
        step_x = delta_x / distance 
        step_y = delta_y / distance
        next_x = x + 5*step_x
        next_y = y + 5*step_y
    else:
        next_x =  target_stairwell_x
        next_y =  target_stairwell_y
        pyflamegpu.setVariableInt("evacuate_status", 2)

    pyflamegpu.setVariableFloat("x", next_x)
    pyflamegpu.setVariableFloat("y", next_y)

    
    message_out.setLocation(next_x, next_y, pyflamegpu.getVariableFloat("z"))


    return pyflamegpu.ALIVE

#conditional function set
@pyflamegpu.agent_function_condition
def eva_state_is_1() -> bool :
    return pyflamegpu.getVariableInt("evacuate_status") == 1

# z字形下楼的算法
# 假设每层楼高3，行人和stairwell的x、y初始一致
# 通过y,z索引，z字形移动，每次移动一小步，遇到转折点y反向

@pyflamegpu.agent_function
def down_stairwell(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageSpatial3D):
    """
    行人在stairwell点z字形下降，每层楼高3
    通过y,z索引，z字形移动
    """
    # 获取当前位置
    x = pyflamegpu.getVariableFloat("x")
    y = pyflamegpu.getVariableFloat("y")
    z = pyflamegpu.getVariableFloat("z")
    # 获取目标stairwell的x,y
    stairwell_x = pyflamegpu.getVariableFloat("target_stairwell_x")
    stairwell_y = pyflamegpu.getVariableFloat("target_stairwell_y")
    # 获取当前z字形方向（1为y正向，-1为y负向）
    if not pyflamegpu.getVariableInt("zigzag_dir"):
        pyflamegpu.setVariableInt("zigzag_dir", 1)

    dire = pyflamegpu.getVariableInt("zigzag_dir")
    # 每步y方向移动距离
    step_y = 0.5
    # 每步z方向下降距离
    step_z = 0.2
    # z字形的y范围（比如以stairwell_y为中心，上下各1.5）
    y_min = stairwell_y - 1.5
    y_max = stairwell_y + 1.5
    # 计算下一步y
    next_y = y + dire * step_y
    # 判断是否到达边界，若到达则反向
    if next_y > y_max:
        next_y = y_max
        dire = -1
    elif next_y < y_min:
        next_y = y_min
        dire = 1
    # 计算下一步z
    next_z = z - step_z
    # 判断是否到达下一层（z是否小于目标z）
    # 假设目标z为0
    if next_z < 0:
        next_z = 0
        pyflamegpu.setVariableInt("evacuate_status", 3)
    # 更新变量
    pyflamegpu.setVariableFloat("y", next_y)
    pyflamegpu.setVariableFloat("z", next_z)
    pyflamegpu.setVariableInt("zigzag_dir", dire)
    # x保持不变
    pyflamegpu.setVariableFloat("x", stairwell_x)
    # 输出当前位置
    message_out.setLocation(stairwell_x, next_y, next_z)
    return pyflamegpu.ALIVE

    
#conditional function set
@pyflamegpu.agent_function_condition
def eva_state_is_2() -> bool :
    return pyflamegpu.getVariableInt("evacuate_status") == 2

@pyflamegpu.agent_function
def move_to_stop(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageNone):
    outstop_x = pyflamegpu.getVariableFloat("outstop_x")
    outstop_y = pyflamegpu.getVariableFloat("outstop_y")
    x = pyflamegpu.getVariableFloat("x")
    y = pyflamegpu.getVariableFloat("y")
    
    delta_x = outstop_x - x
    delta_y = outstop_y - y

    distance = math.sqrtf(delta_x * delta_x + delta_y * delta_y)

    next_x=0.0
    next_y=0.0
    if distance > 5.0:
        step_x = delta_x / distance 
        step_y = delta_y / distance
        next_x = x + 5*step_x
        next_y = y + 5*step_y
    else:
        next_x =  outstop_x
        next_y =  outstop_y
        pyflamegpu.setVariableInt("evacuate_status", 4)

    pyflamegpu.setVariableFloat("x", next_x)
    pyflamegpu.setVariableFloat("y", next_y)

    return pyflamegpu.ALIVE

#conditional function set
@pyflamegpu.agent_function_condition
def eva_state_is_3() -> bool :
    return pyflamegpu.getVariableInt("evacuate_status") == 3


@pyflamegpu.agent_function
def move_to_shelter(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageNone):
    
    fgraph = pyflamegpu.environment.getDirectedGraph("fgraph")
    i = pyflamegpu.getVariableInt("path_point")
    m = pyflamegpu.getVariableIntArray20("shortest_path", i)
    #n = pyflamegpu.getVariableIntArray20("shortest_path", i+1)
    target_shelter_x = fgraph.getVertexPropertyFloatArray2("bar", m,0)
    target_shelter_y = fgraph.getVertexPropertyFloatArray2("bar", m,1)

    pyflamegpu.setVariableFloat("target_shelter_x", target_shelter_x)
    pyflamegpu.setVariableFloat("target_shelter_y", target_shelter_y)

    return pyflamegpu.ALIVE

@pyflamegpu.agent_function
def move_to_shelter(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageSpatial3D):
    
    fgraph = pyflamegpu.environment.getDirectedGraph("fgraph")
    i = pyflamegpu.getVariableInt("path_point")
    m = pyflamegpu.getVariableIntArray20("shortest_path", i)
    n = pyflamegpu.getVariableIntArray20("shortest_path", i+1)

    target_shelter_x = fgraph.getVertexPropertyFloatArray2("bar", m-1, 0)
    target_shelter_y = fgraph.getVertexPropertyFloatArray2("bar", m-1, 1)
    x = pyflamegpu.getVariableFloat("x")
    y = pyflamegpu.getVariableFloat("y")


    delta_x = target_shelter_x - x
    delta_y = target_shelter_y - y

    distance = math.sqrtf(delta_x * delta_x + delta_y * delta_y)

    next_x=0.0
    next_y=0.0
    if distance > 5.0:
        step_x = delta_x / distance 
        step_y = delta_y / distance
        next_x = x + 5*step_x
        next_y = y + 5*step_y
    else:
        next_x =  target_shelter_x
        next_y =  target_shelter_y
        if n == -1:
            pyflamegpu.setVariableInt("evacuate_status", 5)
            pyflamegpu.setVariableInt("in_shelter", 1)
        else:
            pyflamegpu.setVariableInt("path_point", i+1)

    pyflamegpu.setVariableFloat("x", next_x)
    pyflamegpu.setVariableFloat("y", next_y)

    message_out.setLocation(next_x, next_y, pyflamegpu.getVariableFloat("z"))




    return pyflamegpu.ALIVE

#conditional function set
@pyflamegpu.agent_function_condition
def eva_state_is_4() -> bool :
    return pyflamegpu.getVariableInt("evacuate_status") == 4


output_func_translated = pyflamegpu.codegen.translate(output_message)
stairwell_output_func_translated = pyflamegpu.codegen.translate(stairwell_output_message)
shelter_output_func_translated = pyflamegpu.codegen.translate(shelter_output_message)
set_target_stairwell_func_translated = pyflamegpu.codegen.translate(set_target_stairwell)
set_target_shelter_func_translated = pyflamegpu.codegen.translate(set_target_shelter_first)
#ExampleFn_translated = pyflamegpu.codegen.translate(ExampleFn)
move_to_stairwell_func_translated = pyflamegpu.codegen.translate(move_to_stairwell)


ShortestPathFn_translated = pyflamegpu.codegen.translate(ShortestPathFn)
down_stairwell_func_translated = pyflamegpu.codegen.translate(down_stairwell)
move_to_stop_func_translated = pyflamegpu.codegen.translate(move_to_stop)

eva_state_is_1_func_translated = pyflamegpu.codegen.translate(eva_state_is_1)
eva_state_is_2_func_translated = pyflamegpu.codegen.translate(eva_state_is_2)
eva_state_is_3_func_translated = pyflamegpu.codegen.translate(eva_state_is_3)
eva_state_is_4_func_translated = pyflamegpu.codegen.translate(eva_state_is_4)
is_set_shortest_path_is_1_func_translated = pyflamegpu.codegen.translate(is_set_shortest_path_is_1)




# Setup the two agent functions
output_fn = student_agent.newRTCFunction("output_message", output_func_translated)
output_fn.setMessageOutput("location")

stairwell_output_fn = stairwell_agent.newRTCFunction("stairwell_output_message", stairwell_output_func_translated)
stairwell_output_fn.setMessageOutput("stairwell_location")

shelter_output_fn = shelter_agent.newRTCFunction("shelter_output_message", shelter_output_func_translated)
shelter_output_fn.setMessageOutput("shelter_location")

set_target_stairwell_fn = student_agent.newRTCFunction("set_target_stairwell", set_target_stairwell_func_translated)
set_target_stairwell_fn.setMessageInput("stairwell_location")

set_target_shelter_fn = student_agent.newRTCFunction("set_target_shelter", set_target_shelter_func_translated)
set_target_shelter_fn.setMessageInput("shelter_location")

#ExampleFn_fn = agent.newRTCFunction("ExampleFn",ExampleFn_translated)
ShortestPathFn_fn = student_agent.newRTCFunction("ShortestPathFn",ShortestPathFn_translated)
ShortestPathFn_fn.setRTCFunctionCondition(is_set_shortest_path_is_1_func_translated)

move_to_stairwell_fn = student_agent.newRTCFunction("move_to_stairwell", move_to_stairwell_func_translated)
move_to_stairwell_fn.setMessageOutput("location")
move_to_stairwell_fn.setRTCFunctionCondition(eva_state_is_1_func_translated)

down_stairwell_fn = student_agent.newRTCFunction("down_stairwell", down_stairwell_func_translated)
down_stairwell_fn.setMessageOutput("location")
down_stairwell_fn.setRTCFunctionCondition(eva_state_is_2_func_translated)

move_to_stop_fn = student_agent.newRTCFunction("move_to_stop", move_to_stop_func_translated)
move_to_stop_fn.setRTCFunctionCondition(eva_state_is_3_func_translated)


move_to_shelter_translated = pyflamegpu.codegen.translate(move_to_shelter)
move_to_shelter_fn = student_agent.newRTCFunction("move_to_shelter", move_to_shelter_translated)
move_to_shelter_fn.setMessageOutput("location")
move_to_shelter_fn.setRTCFunctionCondition(eva_state_is_4_func_translated)


model.addInitFunction(directed_graph_hostfn())
#model.addExecutionRoot(ExampleFn_fn)
model.addExecutionRoot(output_fn)
stairwell_output_fn.dependsOn(output_fn)
shelter_output_fn.dependsOn(output_fn)
set_target_shelter_fn.dependsOn(shelter_output_fn)
set_target_stairwell_fn.dependsOn(stairwell_output_fn)
ShortestPathFn_fn.dependsOn(set_target_shelter_fn)
ShortestPathFn_fn.dependsOn(set_target_stairwell_fn)
move_to_stairwell_fn.dependsOn(ShortestPathFn_fn)

down_stairwell_fn.dependsOn(move_to_stairwell_fn)
move_to_stop_fn.dependsOn(down_stairwell_fn)
move_to_shelter_fn.dependsOn(move_to_stop_fn)


model.generateLayers() 




# Specify the desired StepLoggingConfig
step_log_cfg = pyflamegpu.StepLoggingConfig(model)
# Log every step
step_log_cfg.setFrequency(1)
# Include the mean of the "point" agent population's variable 'drift'
step_log_cfg.agent("student_agent").logMeanInt("in_shelter")
step_log_cfg.agent("student_agent", "default").logCount()

# Create and init the simulation
cuda_model = pyflamegpu.CUDASimulation(model)

import numpy as np
import array

def EvaluateShleter(shelter_list):
    from flamegpu_init_code import initialize_student_agent_population
    from shelter_flamegpu_init_code import initialize_shelter_agent_population


    # initialize agent population
    initialize_student_agent_population(model, cuda_model)
    initialize_shelter_agent_population(model, cuda_model, shelter_list)    

    cuda_model.setStepLog(step_log_cfg)
    cuda_model.SimulationConfig().steps = 200
    cuda_model.CUDAConfig().device_id = 0
    cuda_model.applyConfig()
    # Run the simulation

    # Attach the logging config/s

    cuda_model.simulate()
    run_log = cuda_model.getRunLog()
    step_log = run_log.getStepLog()
    # 获取所有step的 "student_agent" 的 "in_shelter" 平均值组成的列表
    agent_speed_mean_list = [log.getAgent("student_agent").getMean("in_shelter") for log in step_log]
    # 找到大于0.95的最小索引，如果没有则赋值为600（Python索引从0开始，如果想要第几个step，加1）
    found_index = next((i for i, x in enumerate(agent_speed_mean_list) if x > 0.95), None)
    if found_index is not None:
        min_index = found_index + 1
    else:
        min_index = 200
    list0 = [int(min_index)]
    return list0


creator.create("FitnessMin", base.Fitness, weights=(-1.0,))

creator.create("Individual", array.array, typecode='i', fitness=creator.FitnessMin)

toolbox = base.Toolbox()
# Attribute generator
#range(num_al_shelter)中随机选出6个数作为染色体
num_select_shelter=6
toolbox.register("indices", random.sample, range(70), num_select_shelter)
 

toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.indices)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutUniformInt, low=0, up=70,indpb=0.3)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("evaluate", EvaluateShleter)
 
#add in 1.15
def deletere(individual):
    # Convert the list to a set to remove duplicates
    unique_elements = set(individual)

    # Convert the set back to a list
    unique_list = list(unique_elements)

    # If the length of the list has decreased, fill in with random numbers
    original_length = len(individual)
    new_length = len(unique_list)

    if new_length < original_length:
        # Generate a set of numbers from 0 to 93 excluding the elements in the unique set
        all_numbers = set(range(70))
        available_numbers = all_numbers - unique_elements

        # Fill in the list with random numbers from the available numbers
        while len(unique_list) < original_length:
            random_number = random.choice(list(available_numbers))
            unique_list.append(random_number)
            available_numbers.remove(random_number)
    random.shuffle(unique_list)
    for i in range(len(unique_list)):
        individual[i]=unique_list[i]
    return individual,





def opt_shelter(population, toolbox, mate_probability, mutate_probability, ngen, stats=None, halloffame=None):
    logbook = tools.Logbook()
    logbook.header = ['gen', 'nevals'] + (stats.fields if stats else [])

    # 记录每一代的前三最优个体 [(gen, [list...], (fitness,...)), ...]
    top_individuals_all_gens = []

    # 记录到目前为止的全局前三个个体，保存为三元组 (chromosome, fitness, generation_found)
    overall_top3 = []

    invalid_shelter_lists = [shelter_list for shelter_list in population if not shelter_list.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_shelter_lists)
    for ind, fit in zip(invalid_shelter_lists, fitnesses):
        ind.fitness.values = fit  

    if halloffame is not None:
        halloffame.update(population)

    # 初始化第一代前三最优个体
    current_top3 = tools.selBest(population, 3)
    top_individuals_all_gens.append(
        (0, [list(ind[:]) for ind in current_top3], [ind.fitness.values for ind in current_top3])
    )

    # 更新整体 top3，引入新的个体时确保仅保留前三个最优
    for ind in current_top3:
        chrom = list(ind[:])
        fit = ind.fitness.values
        overall_top3.append((chrom, fit, 0))
    overall_top3.sort(key=lambda x: x[1])
    overall_top3 = overall_top3[:3]

    record = stats.compile(population) if stats else {}
    logbook.record(generation=0, nevals=len(invalid_shelter_lists), **record)    
    print(logbook.stream)
    print(f"第0代 当前最优的三个染色体：")
    for idx, (chrom, fit) in enumerate(zip([list(ind[:]) for ind in current_top3], [ind.fitness.values for ind in current_top3])):
        print(f"   Top{idx+1}: 染色体: {chrom} 适应度: {fit}")

    print("至目前为止整体最优的三个染色体：")
    for idx, (chrom, fit, gen_found) in enumerate(overall_top3):
        print(f"   Overall Top{idx+1}: 染色体: {chrom} 适应度: {fit} 发现于第{gen_found}代")

    done = False

    for gen in range(1, ngen + 1):
        if done:
            break
        offspring = toolbox.select(population, len(population))
        offspring = [toolbox.clone(ind) for ind in offspring]
 
        # 交叉
        for i in range(1, len(offspring), 2):
            if random.random() < mate_probability:
                offspring[i - 1], offspring[i] = toolbox.mate(offspring[i - 1], offspring[i])
                del offspring[i - 1].fitness.values, offspring[i].fitness.values

        # 变异
        for i in range(len(offspring)):
            if random.random() < mutate_probability:
                offspring[i], = toolbox.mutate(offspring[i])
                del offspring[i].fitness.values

        # 确保没有重复
        for i in range(len(offspring)):
            if len(set(offspring[i]))<6:
                offspring[i], = deletere(offspring[i])
                del offspring[i].fitness.values

        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit  

        if halloffame is not None:
            halloffame.update(offspring)

        # 当前代的前三最优个体
        current_top3 = tools.selBest(offspring, 3)
        top_individuals_all_gens.append(
            (gen, [list(ind[:]) for ind in current_top3], [ind.fitness.values for ind in current_top3])
        )

        # 更新整体 top 3
        for ind in current_top3:
            chrom = list(ind[:])
            fit = ind.fitness.values
            if not any(chrom == ex_chrom for (ex_chrom, _, _) in overall_top3):
                overall_top3.append((chrom, fit, gen))
        overall_top3.sort(key=lambda x: x[1])
        overall_top3 = overall_top3[:3]

        print(f"第{gen}代 当前最优的三个染色体：")
        for idx, (chrom, fit) in enumerate(zip([list(ind[:]) for ind in current_top3], [ind.fitness.values for ind in current_top3])):
            print(f"   Top{idx+1}: 染色体: {chrom} 适应度: {fit}")

        print("至目前为止整体最优的三个染色体：")
        for idx, (chrom, fit, gen_found) in enumerate(overall_top3):
            print(f"   Overall Top{idx+1}: 染色体: {chrom} 适应度: {fit} 发现于第{gen_found}代")

        population[:] = offspring

        record = stats.compile(population) if stats else {}
        logbook.record(gen=gen, nevals=len(invalid_ind), **record)
        print(logbook.stream)

    return {"per_gen_top3": top_individuals_all_gens,
            "overall_top3": overall_top3}

#实例化一个hof，储存一个最优解
hof = tools.HallOfFame(3)
population = toolbox.population(n=9)

#输入的是避难所的索引，得到的是适应度的值的统计量
stats = tools.Statistics(lambda ind: ind.fitness.values)
stats.register("avg", np.mean)
stats.register("std", np.std)
stats.register("min", np.min)
stats.register("max", np.max)

if __name__ == "__main__":
    results = opt_shelter(population, toolbox, 0.7, 0.3, 200, stats=stats, halloffame=hof)

#terminal: D:\编程的文档\python\mesa-geo库的学习\新建文件夹> python -m scoop ver1.1.py