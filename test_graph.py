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



# Fetch the model's environment
env = model.Environment()
# Declare a new directed graph named 'fgraph'
fgraph = env.newDirectedGraph("fgraph")
# Attach an float[2] property 'bar' to vertices
fgraph.newVertexPropertyArrayFloat("bar", 2)
# Attach an int property 'foo' to edges
fgraph.newEdgePropertyFloat("foo")


# 首先我要import一个graph 


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


ExampleFn_translated = pyflamegpu.codegen.translate(ExampleFn)
ExampleFn_fn = agent.newRTCFunction("ExampleFn",ExampleFn_translated)

model.addInitFunction(directed_graph_hostfn())
model.addExecutionRoot(ExampleFn_fn)
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

cuda_model.setPopulationData(AgentPopulation)

cuda_model.initialise(sys.argv)

# Attach the logging config
cuda_model.setStepLog(step_log_cfg)

# Run the simulation
cuda_model.simulate()

out_pop = pyflamegpu.AgentVector(model.Agent("point"))
cuda_model.getPopulationData(out_pop)
for agent in out_pop:
    print("foo distance value: %f"%(agent.getVariableFloat("foo")))
    print("x value: %f"%(agent.getVariableFloat("x")))
    print("y value: %f"%(agent.getVariableFloat("y")))
    print("vertex_id value: %d"%(agent.getVariableInt("vertex_id")))
    print("vertex_index value: %d"%(agent.getVariableInt("vertex_index")))
    print("source index value: %d"%(agent.getVariableInt("source_index")))
    print("destination index value: %d"%(agent.getVariableInt("destination_index")))
    print("edge index value: %d"%(agent.getVariableInt("edge_index")))
    print("bar_0_0 value: %f"%(agent.getVariableFloat("bar_0_0")))
    print("++++++++++++++++++++++++++++++++++++++") 

'''
def find_shortest_path(fgraph, start_vertex_id, end_vertex_id):
    """
    使用Dijkstra算法查找两个顶点之间的最短路径
    """
    n = fgraph.getVertexCount()
    distances = [float('inf')] * n
    previous = [-1] * n
    unvisited = set(range(n))
    
    # 获取起点索引
    start_index = fgraph.getVertexIndex(start_vertex_id)
    end_index = fgraph.getVertexIndex(end_vertex_id)
    
    distances[start_index] = 0
    
    while unvisited:
        # 找到当前最小距离的顶点
        current_index = min(unvisited, key=lambda x: distances[x])
        unvisited.remove(current_index)
        
        if current_index == end_index:
            break
        
        # 获取当前顶点的所有出边
        current_id = fgraph.getVertexID(current_index)
        for edge_index in range(fgraph.getEdgeCount()):
            if fgraph.getEdgeSource(edge_index) == current_id:
                neighbor_id = fgraph.getEdgeDestination(edge_index)
                neighbor_index = fgraph.getVertexIndex(neighbor_id)
                
                if neighbor_index in unvisited:
                    # 计算边的权重（这里使用边的foo属性作为权重）
                    weight = fgraph.getEdgePropertyInt("foo", edge_index)
                    new_distance = distances[current_index] + weight
                    
                    if new_distance < distances[neighbor_index]:
                        distances[neighbor_index] = new_distance
                        previous[neighbor_index] = current_index
    
    # 重建路径
    path = []
    current = end_index
    while current != -1:
        vertex_id = fgraph.getVertexID(current)
        path.append(vertex_id)
        current = previous[current]
    
    path.reverse()
    return path
'''