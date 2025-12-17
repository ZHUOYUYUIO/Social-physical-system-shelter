import json
from collections import Counter
from pathlib import Path

import pandas as pd


def project_root() -> Path:
    """返回项目根目录（compare_experiment/ 的上一级）。"""
    return Path(__file__).resolve().parents[1]


def load_candidate_shelters(shelter_csv: Path):
    """读取候选 shelter 点（要求至少包含 index,x,y,graph_id）。"""
    df = pd.read_csv(shelter_csv)
    shelters = []
    for _, r in df.iterrows():
        shelters.append(
            {
                "shelter_id": int(r["index"]),
                "x": float(r["x"]),
                "y": float(r["y"]),
                "graph_id": int(r["graph_id"]) if "graph_id" in df.columns else None,
            }
        )
    return shelters


def build_demands_from_outstops(pop_csv: Path, outstop_geojson: Path):
    """以 outstop 作为需求点。

    权重 w：用 population_points.csv 中每栋楼的点数（视为人数），均分到该楼的多个 outstop。
    """
    pop = pd.read_csv(pop_csv)
    pop_by_building = pop.groupby("building_id").size().to_dict()

    gj = json.loads(outstop_geojson.read_text(encoding="utf-8"))
    feats = gj.get("features", [])

    outstops = []
    for ft in feats:
        props = ft.get("properties", {})
        if "building_id" not in props:
            continue
        bid = int(props["building_id"])
        ox = float(props["outstop_x"])
        oy = float(props["outstop_y"])
        outstops.append((bid, ox, oy))

    if not outstops:
        return []

    cnt = Counter(bid for bid, _, _ in outstops)

    demands = []
    for bid, ox, oy in outstops:
        w_total = float(pop_by_building.get(bid, 0))
        if w_total <= 0:
            continue
        w = w_total / float(cnt[bid])
        demands.append({"building_id": bid, "x": ox, "y": oy, "w": w})

    return demands


