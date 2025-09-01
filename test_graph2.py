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
agent.newVariableArrayInt("shortest_path", 100)  # 存储最短路径的顶点ID数组



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

    # 获取起点和终点ID（可以从agent变量中获取，或者设置为固定值）
    start_vertex_id = pyflamegpu.getVariableInt("start_vertex_id")
    end_vertex_id = pyflamegpu.getVariableInt("end_vertex_id")

    # 获取图的顶点数量
    vertex_count = fgraph.getVertexCount()
    edge_count = fgraph.getEdgeCount()

    # 初始化距离数组（使用一个大的常数表示无穷大）
    INF = 999999.0
    distances = [INF] * vertex_count
    previous = [-1] * vertex_count
    visited = [False] * vertex_count

    # 获取起点和终点的索引
    start_index = fgraph.getVertexIndex(start_vertex_id)
    end_index = fgraph.getVertexIndex(end_vertex_id)

    # 初始化起点
    distances[start_index] = 0.0

    # Dijkstra算法主循环
    for _ in range(vertex_count):
        # 找到当前未访问顶点中距离最小的顶点
        min_distance = INF
        current_index = -1

        for i in range(vertex_count):
            if not visited[i] and distances[i] < min_distance:
                min_distance = distances[i]
                current_index = i

        if current_index == -1 or distances[current_index] == INF:
            break

        visited[current_index] = True

        # 如果到达终点，可以提前结束
        if current_index == end_index:
            break

        # 获取当前顶点的ID
        current_vertex_id = fgraph.getVertexID(current_index)

        # 遍历当前顶点的所有出边
        for edge_index in range(edge_count):
            source_id = fgraph.getEdgeSource(edge_index)
            if source_id == current_vertex_id:
                dest_id = fgraph.getEdgeDestination(edge_index)
                dest_index = fgraph.getVertexIndex(dest_id)

                if not visited[dest_index]:
                    # 获取边的权重
                    edge_weight = fgraph.getEdgePropertyFloat("foo", edge_index)
                    new_distance = distances[current_index] + edge_weight

                    if new_distance < distances[dest_index]:
                        distances[dest_index] = new_distance
                        previous[dest_index] = current_index

    # 重建最短路径
    path = []
    current = end_index

    while current != -1:
        vertex_id = fgraph.getVertexID(current)
        path.append(vertex_id)
        current = previous[current]

    path.reverse()

    # 如果路径存在（起点和终点连通），则存储路径信息
    if len(path) > 1 and path[0] == start_vertex_id:
        # 存储路径长度
        pyflamegpu.setVariableInt("path_length", len(path))

        # 存储路径中的顶点ID
        shortest_path_array = pyflamegpu.getVariableArrayInt("shortest_path")
        for i in range(min(len(path), 100)):  # 限制路径长度不超过数组大小
            shortest_path_array[i] = path[i]
    else:
        # 没有找到路径
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
