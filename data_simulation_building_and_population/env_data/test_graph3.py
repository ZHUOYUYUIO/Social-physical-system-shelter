from pyflamegpu import *
import pyflamegpu.codegen
import sys
import random

"""
test_graph3.py

目标：
- 修复 test_graph2.py 中 Vertex ID / Vertex Index 混用导致的越界与运行时错误。
- 统一约定：
  - 图相关 API 一律使用 Vertex ID（合法范围：1..VERTEX_COUNT）
  - 所有 agent 数组一律使用 Vertex Index（合法范围：0..VERTEX_COUNT-1）

图文件（已重编号，ID 从 1 开始）：
  data/env_data/expanded_visibility_graph_renumbered.json
"""

MODEL_NAME = "F_MAP_tutorial_graph3"
GRAPH_NAME = "fgraph"
GRAPH_PATH = "data/env_data/expanded_visibility_graph_renumbered.json"

# 注意：该值应与 renumbered 图一致（ID: 1..176）
VERTEX_COUNT = 176
# 最短路数组最大长度（防止路径>20 被截断）
MAX_PATH_LEN = 256

model = pyflamegpu.ModelDescription(MODEL_NAME)


class import_graph_hostfn(pyflamegpu.HostFunction):
    def run(self, FLAMEGPU):
        fgraph = FLAMEGPU.environment.getDirectedGraph(GRAPH_NAME)
        fgraph.importGraph(GRAPH_PATH)


# Agent
agent = model.newAgent("point")
agent.newVariableInt("start_vertex_id")
agent.newVariableInt("end_vertex_id")
agent.newVariableInt("path_length")
agent.newVariableArrayInt("shortest_path", MAX_PATH_LEN)  # 存储顶点ID序列（从终点回溯，逆序）
agent.newVariableInt("error_code")  # 0 OK; 1 invalid id; 2 no path

# Dijkstra arrays (index-based)
agent.newVariableArrayFloat("distances", VERTEX_COUNT, [999999.0] * VERTEX_COUNT)
agent.newVariableArrayInt("visited", VERTEX_COUNT, [0] * VERTEX_COUNT)
agent.newVariableArrayInt("previous", VERTEX_COUNT, [-1] * VERTEX_COUNT)  # previous vertex INDEX


# Environment + Graph
env = model.Environment()
fgraph = env.newDirectedGraph(GRAPH_NAME)
fgraph.newVertexPropertyArrayFloat("bar", 2)
fgraph.newEdgePropertyFloat("foo")


@pyflamegpu.agent_function
def ShortestPathFn(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageNone):
    fgraph = pyflamegpu.environment.getDirectedGraph(GRAPH_NAME)

    # 读入起终点 Vertex ID（必须是 1..VERTEX_COUNT）
    start_id = pyflamegpu.getVariableInt("start_vertex_id")
    end_id = pyflamegpu.getVariableInt("end_vertex_id")

    # 初始化输出
    pyflamegpu.setVariableInt("path_length", 0)
    pyflamegpu.setVariableInt("error_code", 0)
    for i in range(MAX_PATH_LEN):
        pyflamegpu.setVariableIntArray256("shortest_path", i, -1)

    # 防御：ID 合法性检查（避免 Vertex ID=0 触发 runtime error）
    if start_id < 1 or start_id > VERTEX_COUNT or end_id < 1 or end_id > VERTEX_COUNT:
        pyflamegpu.setVariableInt("error_code", 1)
        return pyflamegpu.ALIVE

    # ID -> INDEX（index: 0..VERTEX_COUNT-1）
    start_index = fgraph.getVertexIndex(start_id)
    end_index = fgraph.getVertexIndex(end_id)

    INF = 999999.0

    # 初始化 arrays
    for i in range(VERTEX_COUNT):
        pyflamegpu.setVariableFloatArray176("distances", i, INF)
        pyflamegpu.setVariableIntArray176("visited", i, 0)
        pyflamegpu.setVariableIntArray176("previous", i, -1)
    pyflamegpu.setVariableFloatArray176("distances", start_index, 0.0)

    # Dijkstra
    for _ in range(VERTEX_COUNT):
        # 找未访问的最小 dist
        min_dist = INF
        current_index = -1
        for i in range(VERTEX_COUNT):
            if pyflamegpu.getVariableIntArray176("visited", i) == 0:
                d = pyflamegpu.getVariableFloatArray176("distances", i)
                if d < min_dist:
                    min_dist = d
                    current_index = i

        if current_index == -1 or min_dist == INF:
            break

        pyflamegpu.setVariableIntArray176("visited", current_index, 1)
        if current_index == end_index:
            break

        # INDEX -> ID（因为 outEdges 使用 Vertex ID）
        current_id = fgraph.getVertexID(current_index)

        # 遍历当前顶点出边
        for edge in fgraph.outEdges(current_id):
            # 这里按 FLAMEGPU 语义：getEdgeDestination() 返回 Vertex ID
            dest_id = edge.getEdgeDestination()
            if dest_id < 1 or dest_id > VERTEX_COUNT:
                continue
            dest_index = fgraph.getVertexIndex(dest_id)

            if pyflamegpu.getVariableIntArray176("visited", dest_index) != 0:
                continue

            w = edge.getPropertyFloat("foo")
            cur_d = pyflamegpu.getVariableFloatArray176("distances", current_index)
            new_d = cur_d + w
            old_d = pyflamegpu.getVariableFloatArray176("distances", dest_index)
            if new_d < old_d:
                pyflamegpu.setVariableFloatArray176("distances", dest_index, new_d)
                pyflamegpu.setVariableIntArray176("previous", dest_index, current_index)

    # 回溯路径（存 Vertex ID）
    if pyflamegpu.getVariableFloatArray176("distances", end_index) == INF:
        pyflamegpu.setVariableInt("error_code", 2)
        return pyflamegpu.ALIVE

    cur = end_index
    path_len = 0
    while cur != -1 and path_len < MAX_PATH_LEN:
        vid = fgraph.getVertexID(cur)
        pyflamegpu.setVariableIntArray256("shortest_path", path_len, vid)
        path_len += 1
        if cur == start_index:
            break
        cur = pyflamegpu.getVariableIntArray176("previous", cur)

    pyflamegpu.setVariableInt("path_length", path_len)
    return pyflamegpu.ALIVE


ShortestPathFn_translated = pyflamegpu.codegen.translate(ShortestPathFn)
ShortestPathFn_fn = agent.newRTCFunction("ShortestPathFn", ShortestPathFn_translated)

model.addInitFunction(import_graph_hostfn())
model.addExecutionRoot(ShortestPathFn_fn)
model.generateLayers()


def main():
    cuda_model = pyflamegpu.CUDASimulation(model)

    # 只放 1 个 agent，先把最短路跑通
    pop = pyflamegpu.AgentVector(model.Agent("point"), 1)
    a = pop[0]

    # IMPORTANT: Vertex ID 必须从 1 开始（renumbered 图是 1..176）
    a.setVariableInt("start_vertex_id", 24)
    a.setVariableInt("end_vertex_id", 10)

    cuda_model.setPopulationData(pop)
    cuda_model.initialise(sys.argv)
    cuda_model.simulate()

    out_pop = pyflamegpu.AgentVector(model.Agent("point"))
    cuda_model.getPopulationData(out_pop)
    for ag in out_pop:
        start_id = ag.getVariableInt("start_vertex_id")
        end_id = ag.getVariableInt("end_vertex_id")
        err = ag.getVariableInt("error_code")
        path_len = ag.getVariableInt("path_length")
        print(f"start_id={start_id}, end_id={end_id}, error_code={err}, path_length={path_len}")
        if err == 0 and path_len > 0:
            arr = ag.getVariableArrayInt("shortest_path")
            # arr[0] 是终点，arr[path_len-1] 是起点（逆序）
            print("path (end -> start):", arr[:path_len])


if __name__ == "__main__":
    main()


