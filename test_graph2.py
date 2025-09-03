from pyflamegpu import *
import pyflamegpu.codegen
import sys
import math

model = pyflamegpu.ModelDescription("F_MAP_tutorial")


# Define an host function called directed_graph_hostfn
class directed_graph_hostfn(pyflamegpu.HostFunction):
  def run(self,FLAMEGPU):
    # Fetch a handle to the directed graph
    fgraph = FLAMEGPU.environment.getDirectedGraph("fgraph")
    # Import a different graph
    fgraph.importGraph("expanded_visibility_graph.json");

# Define an agent named point
agent = model.newAgent("point")
# Assign the agent some variables (ID is implicit to agents, so we don't define it ourselves)
agent.newVariableFloat("x")
agent.newVariableFloat("y")
agent.newVariableInt("vertex_id")
agent.newVariableInt("vertex_index")
agent.newVariableFloat("foo")
agent.newVariableInt("source_index")
agent.newVariableInt("destination_index")
agent.newVariableInt("edge_index")
agent.newVariableFloat("bar_0_0")
agent.newVariableInt("start_vertex_id")
agent.newVariableInt("end_vertex_id")
agent.newVariableInt("path_length")
agent.newVariableArrayInt("shortest_path", 20)  # 存储最短路径的顶点ID数组，16个顶点的图最长路径不超过20

agent.newVariableArrayFloat("shortest_value",16, [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0])

# Dijkstra算法需要的变量
agent.newVariableArrayFloat("distances", 16, [999999.0] * 16)  # 距离数组，初始化为无穷大
agent.newVariableArrayInt("visited", 16, [0] * 16)  # 访问标记数组
agent.newVariableArrayInt("previous", 16, [-1] * 16)  # 前驱节点数组
agent.newVariableInt("vertex_count")  # 顶点数量
agent.newVariableInt("edge_count")  # 边数量



# Fetch the model's environment
env = model.Environment()
# Declare a new directed graph named 'fgraph'
fgraph = env.newDirectedGraph("fgraph")
# Attach an float[2] property 'bar' to vertices
fgraph.newVertexPropertyArrayFloat("bar", 2)
# Attach an int property 'foo' to edges
fgraph.newEdgePropertyFloat("foo")


# 首先我要import一个graph

'''
@pyflamegpu.agent_function
def ExampleFn(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageNone):
    fgraph = pyflamegpu.environment.getDirectedGraph("fgraph")

    # Fetch the ID of the vertex at index 1
    vertex_id = fgraph.getVertexID(1) # index+1
    # Fetch the index of the vertex with ID 1
    vertex_index = fgraph.getVertexIndex(1) # id- 1

    # Access a property of vertex with ID 1
    bar_0_0 = fgraph.getVertexPropertyFloatArray2("bar", 1 , 0)


    # Fetch the source and destination indexes from the edge at index 0
    source_index = fgraph.getEdgeSource(1) # 第二条线的起点的索引
    destination_index = fgraph.getEdgeDestination(1) # 第二条线的终点的索引

    # Fetch the index of the edge from vertex ID 2 to vertex ID 5
    edge_index = fgraph.getEdgeIndex(2-1, 5-1)

    # Access a property of edge with source ID 2, destination ID 5
    foo = fgraph.getEdgePropertyFloat("foo", edge_index)

    pyflamegpu.setVariableInt("vertex_id", vertex_id)
    pyflamegpu.setVariableInt("vertex_index", vertex_index)
    pyflamegpu.setVariableFloat("foo", foo)
    pyflamegpu.setVariableFloat("bar_0_0", bar_0_0)
    pyflamegpu.setVariableInt("source_index", source_index)
    pyflamegpu.setVariableInt("destination_index", destination_index)
    pyflamegpu.setVariableInt("edge_index", edge_index)
    return pyflamegpu.ALIVE

'''


### 好消息，根据我的test_set_get_in_onefunc.py，我可以实现动态的数据存储啦！！！
@pyflamegpu.agent_function
def ShortestPathFn(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageNone):
    """
    使用Dijkstra算法实现最短路径规划
    """
    fgraph = pyflamegpu.environment.getDirectedGraph("fgraph")

    # 定义常量
    INF = 999999.0
    vertex_count = 16  # 假设图中有16个顶点

    # 获取起点和终点ID（可以从agent变量中获取，或者设置为固定值）
    start_vertex_id = pyflamegpu.getVariableInt("start_vertex_id")
    end_vertex_id = pyflamegpu.getVariableInt("end_vertex_id")

    ###
    # 起点是哪个，我们就把它的list对应的i，设置为0。
    ###
    pyflamegpu.setVariableFloatArray16("shortest_value", start_vertex_id, 0)

    #然后遍历所有顶点（1-16），除了我们的起点id外，如果它和起点id有连线，我们就把它的list对应的i，设置为起点到它的距离。

    #遍历起点的id，线的值就设置为shortest_value的起点对应的i的值+边的值。
    # 先初始化所有顶点的shortest_value为INF
    for i in range(1, 16):
        if i != start_vertex_id:
            pyflamegpu.setVariableFloatArray16("shortest_value", i, INF)

    # 遍历起点连接的边，设置对应的shortest_value
    for edge in fgraph.outEdges(start_vertex_id-1):
        # 获取边的目的顶点索引
        dest_vertex_index = edge.getEdgeDestination()
        # 获取边的foo属性
        foo = edge.getPropertyInt("foo")

        # 将foo值存储到对应顶点ID的位置
        pyflamegpu.setVariableFloatArray16("shortest_value", dest_vertex_index, foo)
            


    # 获取起点和终点的索引
    start_index = fgraph.getVertexIndex(start_vertex_id)
    end_index = fgraph.getVertexIndex(end_vertex_id)

    # 初始化起点距离为0
    pyflamegpu.setVariableFloatArray16("distances", start_index, 0.0)
    # 初始化起点前驱为-1
    pyflamegpu.setVariableIntArray16("previous", start_index, -1)
    # 初始化其他顶点的距离为无穷大，前驱为-1
    for i in range(vertex_count):
        if i != start_index:
            pyflamegpu.setVariableFloatArray16("distances", i, INF)
            pyflamegpu.setVariableIntArray16("previous", i, -1)
        pyflamegpu.setVariableIntArray16("visited", i, 0)

    # Dijkstra算法主循环
    for _ in range(vertex_count):
        # 找到当前未访问顶点中距离最小的顶点
        min_distance = INF
        current_index = -1

        for i in range(vertex_count):
            visited_i = pyflamegpu.getVariableIntArray16("visited", i)
            distance_i = pyflamegpu.getVariableFloatArray16("distances", i)
            if visited_i == 0 and distance_i < min_distance:
                min_distance = distance_i
                current_index = i

        if current_index == -1 or min_distance == INF:
            break

        # 标记当前顶点为已访问
        pyflamegpu.setVariableIntArray16("visited", current_index, 1)

        # 如果到达终点，可以提前结束
        if current_index == end_index:
            break

        # 获取当前顶点的ID
        current_vertex_id = fgraph.getVertexID(current_index)

        # 遍历当前顶点的所有出边
        for edge in fgraph.outEdges(current_index):
            source_index = fgraph.getEdgeSource()
            if source_index == current_index:
                dest_index = fgraph.getEdgeDestination()

                visited_dest = pyflamegpu.getVariableIntArray16("visited", dest_index)
                if visited_dest == 0:
                    # 获取边的权重
                    edge_weight = edge.getPropertyFloat("foo")
                    current_distance = pyflamegpu.getVariableFloatArray16("distances", current_index)
                    new_distance = current_distance + edge_weight

                    dest_distance = pyflamegpu.getVariableFloatArray16("distances", dest_index)
                    if new_distance < dest_distance:
                        pyflamegpu.setVariableFloatArray16("distances", dest_index, new_distance)
                        pyflamegpu.setVariableIntArray16("previous", dest_index, current_index)

    # 重建最短路径 - 使用pyflamegpu方法完全避免循环和索引操作

    # 初始化路径数组为-1（手动设置每个元素）
    pyflamegpu.setVariableIntArray20("shortest_path", 0, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 1, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 2, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 3, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 4, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 5, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 6, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 7, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 8, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 9, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 10, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 11, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 12, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 13, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 14, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 15, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 16, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 17, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 18, -1)
    pyflamegpu.setVariableIntArray20("shortest_path", 19, -1)
   
    # 从终点开始重建路径（展开循环，避免使用for循环）
    current_0 = end_index
    if current_0 != -1:
        vertex_id_0 = fgraph.getVertexID(current_0)
        pyflamegpu.setVariableIntArray100("shortest_path", 0, vertex_id_0)
        prev_0 = pyflamegpu.getVariableIntArray16("previous", current_0)

        if prev_0 != -1:
            vertex_id_1 = fgraph.getVertexID(prev_0)
            pyflamegpu.setVariableIntArray100("shortest_path", 1, vertex_id_1)
            # 路径长度为2
            pyflamegpu.setVariableInt("path_length", 2)
        else:
            # 路径长度为1
            pyflamegpu.setVariableInt("path_length", 1)
    else:
        # 没有路径
        pyflamegpu.setVariableInt("path_length", 0)

    # 检查路径是否以起点开始
    path_0 = pyflamegpu.getVariableIntArray20("shortest_path", 0)
    if path_0 != start_vertex_id:
        pyflamegpu.setVariableInt("path_length", 0)

    return pyflamegpu.ALIVE


#ExampleFn_translated = pyflamegpu.codegen.translate(ExampleFn)
ShortestPathFn_translated = pyflamegpu.codegen.translate(ShortestPathFn)
#ExampleFn_fn = agent.newRTCFunction("ExampleFn",ExampleFn_translated)
ShortestPathFn_fn = agent.newRTCFunction("ShortestPathFn",ShortestPathFn_translated)

model.addInitFunction(directed_graph_hostfn())
#model.addExecutionRoot(ExampleFn_fn)
model.addExecutionRoot(ShortestPathFn_fn)
model.generateLayers()

# Specify the desired StepLoggingConfig
step_log_cfg = pyflamegpu.StepLoggingConfig(model)
# Log every step
step_log_cfg.setFrequency(1)
# Include the mean of the "point" agent population's variable 'drift'
step_log_cfg.agent("point").logMeanFloat("foo")

# Create and init the simulation
cuda_model = pyflamegpu.CUDASimulation(model)

import random
AGENT_COUNT=3
ENV_WIDTH=2
AgentPopulation = pyflamegpu.AgentVector(model.Agent("point"), AGENT_COUNT)
for i in range(AGENT_COUNT):
    agent = AgentPopulation[i]
    agent.setVariableFloat("x", random.uniform(0, ENV_WIDTH))
    agent.setVariableFloat("y", random.uniform(0, ENV_WIDTH))

    # 设置起点和终点ID（示例中使用固定值，您可以根据需要修改）
    if i == 0:
        agent.setVariableInt("start_vertex_id", 1)  # 从顶点1开始
        agent.setVariableInt("end_vertex_id", 10)   # 到顶点10结束
    elif i == 1:
        agent.setVariableInt("start_vertex_id", 2)  # 从顶点2开始
        agent.setVariableInt("end_vertex_id", 15)   # 到顶点15结束
    else:
        agent.setVariableInt("start_vertex_id", 5)  # 从顶点5开始
        agent.setVariableInt("end_vertex_id", 11)   # 到顶点20结束

cuda_model.setPopulationData(AgentPopulation)

cuda_model.initialise(sys.argv)

# Attach the logging config
cuda_model.setStepLog(step_log_cfg)

# Run the simulation
cuda_model.simulate()

out_pop = pyflamegpu.AgentVector(model.Agent("point"))
cuda_model.getPopulationData(out_pop)
for agent in out_pop:
    print("Agent %d:" % out_pop.index(agent))
    print("  foo distance value: %f"%(agent.getVariableFloat("foo")))
    print("  x value: %f"%(agent.getVariableFloat("x")))
    print("  y value: %f"%(agent.getVariableFloat("y")))
    print("  vertex_id value: %d"%(agent.getVariableInt("vertex_id")))
    print("  vertex_index value: %d"%(agent.getVariableInt("vertex_index")))
    print("  source index value: %d"%(agent.getVariableInt("source_index")))
    print("  destination index value: %d"%(agent.getVariableInt("destination_index")))
    print("  edge index value: %d"%(agent.getVariableInt("edge_index")))
    print("  bar_0_0 value: %f"%(agent.getVariableFloat("bar_0_0")))

    # 显示最短路径信息
    start_id = agent.getVariableInt("start_vertex_id")
    end_id = agent.getVariableInt("end_vertex_id")
    path_length = agent.getVariableInt("path_length")

    print("  最短路径规划:")
    print("    起点ID: %d, 终点ID: %d" % (start_id, end_id))
    print("    路径长度: %d" % path_length)

    if path_length > 0:
        print("    最短路径: ", end="")
        shortest_path_array = agent.getVariableArrayInt("shortest_path")
        for i in range(path_length):
            if i > 0:
                print(" -> ", end="")
            print("%d" % shortest_path_array[i], end="")
        print("")
    else:
        print("    未找到路径（起点和终点可能不连通）")

    print("++++++++++++++++++++++++++++++++++++++")
