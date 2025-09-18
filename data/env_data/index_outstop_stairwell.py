import json
import math
import os
from typing import Any, Dict, List, Tuple, Optional


def load_graph_nodes(graph_json_path: str) -> List[Dict[str, Any]]:
    with open(graph_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("nodes", [])


def build_bar_lookup_by_int_round(nodes: List[Dict[str, Any]]) -> Dict[Tuple[int, int], str]:
    lookup: Dict[Tuple[int, int], str] = {}
    for n in nodes:
        bar = n.get("bar")
        if not bar or not isinstance(bar, list) or len(bar) < 2:
            continue
        try:
            bx = int(round(float(bar[0])))
            by = int(round(float(bar[1])))
        except Exception:
            continue
        lookup[(bx, by)] = str(n.get("id"))
    return lookup


def compute_squared_distance(ax: float, ay: float, bx: float, by: float) -> float:
    return (ax - bx) * (ax - bx) + (ay - by) * (ay - by)


def find_nearest_graph_id(px: float, py: float, nodes: List[Dict[str, Any]]) -> Tuple[Optional[str], float]:
    best_id: Optional[str] = None
    best_d2: float = float("inf")
    for n in nodes:
        bar = n.get("bar")
        if not bar or not isinstance(bar, list) or len(bar) < 2:
            continue
        try:
            nx = float(bar[0])
            ny = float(bar[1])
        except Exception:
            continue
        d2 = compute_squared_distance(px, py, nx, ny)
        if d2 < best_d2:
            best_d2 = d2
            best_id = str(n.get("id"))
    return best_id, math.sqrt(best_d2) if best_d2 < float("inf") else float("inf")


def load_geojson(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_geojson(data: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def process(
    graph_path: str,
    stairwell_withoutput_path: str,
    output_geojson_path: str,
) -> None:
    if not os.path.exists(graph_path):
        raise FileNotFoundError(f"找不到图文件: {os.path.abspath(graph_path)}")
    if not os.path.exists(stairwell_withoutput_path):
        raise FileNotFoundError(f"找不到输入GeoJSON: {os.path.abspath(stairwell_withoutput_path)}")

    nodes = load_graph_nodes(graph_path)

    src = load_geojson(stairwell_withoutput_path)
    features = src.get("features", [])

    updated_features: List[Dict[str, Any]] = []
    processed_cnt = 0

    for feat in features:
        props = dict(feat.get("properties", {}))
        ox = props.get("outstop_x")
        oy = props.get("outstop_y")
        graph_id: Optional[str] = None

        if ox is not None and oy is not None:
            try:
                oxf = float(ox)
                oyf = float(oy)
            except Exception:
                oxf = None
                oyf = None

            if oxf is not None and oyf is not None:
                nid, _ = find_nearest_graph_id(oxf, oyf, nodes)
                graph_id = nid if nid is not None else ""
                processed_cnt += 1

        props["graph_id"] = graph_id if graph_id is not None else ""

        updated_features.append(
            {
                "type": "Feature",
                "geometry": feat.get("geometry"),
                "properties": props,
            }
        )

    out_data = {
        "type": "FeatureCollection",
        "features": updated_features,
    }
    # 透传可能存在的其他顶层字段
    for extra_key in ("crs", "name", "bbox"):
        if extra_key in src and extra_key not in out_data:
            out_data[extra_key] = src[extra_key]

    save_geojson(out_data, output_geojson_path)

    print(
        f"完成: 写出 {os.path.relpath(output_geojson_path, start=os.path.join(os.path.dirname(__file__), '..'))} "
        f"(全部使用最近邻匹配，共处理 {processed_cnt} 个要素)"
    )


def main() -> int:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    graph_path = os.path.join(current_dir, "expanded_visibility_graph_renumbered.json")
    stairwell_withoutput_path = os.path.join(current_dir, "..", "output", "stairwell_withoutput.geojson")
    output_geojson_path = os.path.join(current_dir, "..", "output", "stairwell_withoutput_new.geojson")

    try:
        process(
            graph_path=graph_path,
            stairwell_withoutput_path=stairwell_withoutput_path,
            output_geojson_path=output_geojson_path,
        )
    except Exception as e:
        print(f"处理失败: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


