import heapq
import json
import math

INF = 1e30


def load_graph(graph_json_path):
    """加载 expanded_visibility_graph_renumbered.json 一类文件。"""
    g = json.loads(graph_json_path.read_text(encoding="utf-8"))
    nodes = g["nodes"]
    links = g["links"]

    # node_id(str) -> (x(int), y(int))
    pos = {str(n["id"]): (int(n["bar"][0]), int(n["bar"][1])) for n in nodes}

    adj = {}
    for e in links:
        s = str(e["source"])
        t = str(e["target"])
        w = float(e.get("foo", 1.0))
        adj.setdefault(s, []).append((t, w))

    return pos, adj


def nearest_node_id(pos, x: float, y: float):
    """把坐标点映射到最近的图节点（线性扫，图规模不大时足够快）。"""
    best_id = None
    best_d2 = INF
    for nid, (nx, ny) in pos.items():
        dx = nx - x
        dy = ny - y
        d2 = dx * dx + dy * dy
        if d2 < best_d2:
            best_d2 = d2
            best_id = nid
    return best_id, math.sqrt(best_d2)


def dijkstra_all(adj, start_id: str):
    dist = {start_id: 0.0}
    pq = [(0.0, start_id)]
    while pq:
        d, u = heapq.heappop(pq)
        if d != dist.get(u, INF):
            continue
        for v, w in adj.get(u, []):
            nd = d + w
            if nd < dist.get(v, INF):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def build_distance_matrix(adj, demand_node_ids, shelter_node_ids):
    """dist_matrix[i][j] = demand_i 到 shelter_j 的最短路距离。"""
    cache = {}
    dist_matrix = []
    for dnid in demand_node_ids:
        if dnid not in cache:
            cache[dnid] = dijkstra_all(adj, dnid)
        dist_all = cache[dnid]
        row = [dist_all.get(snid, INF) for snid in shelter_node_ids]
        dist_matrix.append(row)
    return dist_matrix


