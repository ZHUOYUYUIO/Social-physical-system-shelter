import argparse
import json
from pathlib import Path

from data_io import (
    project_root,
    build_demands_from_outstops,
    load_candidate_shelters,
)
from graph_distance import (
    load_graph,
    nearest_node_id,
    build_distance_matrix,
)
from solvers_uncap import solve_k_median_uncap
from solvers_cap import solve_k_median_cap


def parse_args():
    p = argparse.ArgumentParser(description="基于路网最短路的 shelter 选址优化（K-median）")
    p.add_argument(
        "--mode",
        choices=["uncap", "cap"],
        default="uncap",
        help="uncap=不考虑容量；cap=考虑容量",
    )
    p.add_argument("--k", type=int, required=True, help="固定开启的 shelter 数量 K")
    p.add_argument(
        "--capacity-per-shelter",
        type=float,
        default=500.0,
        help="cap 模式：每个 shelter 的容量（人数）。默认 500",
    )
    p.add_argument("--max-swap-rounds", type=int, default=15, help="局部搜索 swap 迭代轮数（默认 15）")
    p.add_argument("--no-swap", action="store_true", help="只用贪心初始化，不做 swap 改进")

    # 路径（默认使用你项目里已有的文件）
    p.add_argument("--graph", default="data/env_data/expanded_visibility_graph_renumbered.json")
    p.add_argument("--shelter-csv", default="data/output/shelter_points_with_graph_id.csv")
    p.add_argument("--population-csv", default="data/output/population_points.csv")
    p.add_argument("--outstop-geojson", default="data/output/stairwell_withoutput.geojson")

    p.add_argument("--out-json", default="compare_experiment/solution.json", help="输出结果 JSON（相对项目根目录）")
    return p.parse_args()


def main():
    args = parse_args()
    root = project_root()

    graph_path = root / args.graph
    shelter_csv = root / args.shelter_csv
    pop_csv = root / args.population_csv
    outstop_geojson = root / args.outstop_geojson
    out_json = root / args.out_json

    # 1) 读需求点（用 outstop 作为需求点，权重=该楼人数均分到该楼多个 outstop）
    demands = build_demands_from_outstops(pop_csv, outstop_geojson)
    if not demands:
        raise RuntimeError("demands 为空：请检查 population_points.csv 与 stairwell_withoutput.geojson")

    # 2) 读候选 shelter 点（csv 里已有 graph_id）
    shelters = load_candidate_shelters(shelter_csv)
    if not shelters:
        raise RuntimeError("候选 shelter 为空：请检查 shelter_points_with_graph_id.csv")

    # 3) 读路网图
    pos, adj = load_graph(graph_path)

    # 4) 把需求点映射到图节点（最近 node）
    demand_node_ids = []
    weights = []
    for d in demands:
        nid, _ = nearest_node_id(pos, d["x"], d["y"])
        demand_node_ids.append(nid)
        weights.append(float(d["w"]))

    # 5) 把 shelter 映射到图节点（优先用 csv 的 graph_id，兜底用最近 node）
    shelter_node_ids = []
    for s in shelters:
        hint = s.get("graph_id")
        if hint is not None and str(hint) in pos:
            shelter_node_ids.append(str(hint))
        else:
            nid, _ = nearest_node_id(pos, s["x"], s["y"])
            shelter_node_ids.append(nid)

    # 6) 预计算距离矩阵（每个 demand 节点跑一次 Dijkstra，取到每个 shelter 的最短路距离）
    dist = build_distance_matrix(adj, demand_node_ids, shelter_node_ids)

    # 7) 求解
    if args.mode == "uncap":
        open_idx, best_cost = solve_k_median_uncap(
            dist_matrix=dist,
            weights=weights,
            k=args.k,
            max_swap_rounds=0 if args.no_swap else args.max_swap_rounds,
        )
        capacities = None
    else:
        open_idx, best_cost = solve_k_median_cap(
            dist_matrix=dist,
            weights=weights,
            k=args.k,
            capacity_per_shelter=float(args.capacity_per_shelter),
            max_swap_rounds=0 if args.no_swap else args.max_swap_rounds,
        )
        capacities = float(args.capacity_per_shelter)

    chosen = []
    for j in open_idx:
        s = shelters[j]
        chosen.append(
            {
                "candidate_index": int(j),
                "shelter_id": int(s["shelter_id"]),
                "x": float(s["x"]),
                "y": float(s["y"]),
                "graph_id": int(s["graph_id"]) if s.get("graph_id") is not None else None,
            }
        )

    result = {
        "mode": args.mode,
        "k": int(args.k),
        "capacity_per_shelter": capacities,
        "total_weighted_distance": float(best_cost),
        "chosen_shelters": chosen,
        "inputs": {
            "graph": str(graph_path),
            "shelter_csv": str(shelter_csv),
            "population_csv": str(pop_csv),
            "outstop_geojson": str(outstop_geojson),
            "demand_count": len(demands),
            "candidate_count": len(shelters),
        },
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"mode={args.mode} K={args.k} cost={best_cost:.3f}")
    print(f"chosen shelter_id = {[c['shelter_id'] for c in chosen]}")
    print(f"写出: {out_json}")


if __name__ == "__main__":
    main()

