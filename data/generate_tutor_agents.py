#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tutor 代理表格生成器

目标：
- 从已有的学生散点（population_points.csv / population_points.json）中挑选点
- 生成“每一栋楼的每一层都有一个 tutor agent”的独立表格

输出：
- data/output/tutor_points.csv
- data/output/tutor_points.json

选择策略（可复现）：
- 对每个 (building_id, floor)：
  - 若该层存在散点：选择该层散点中“最接近该层均值中心”的点
  - 若该层不存在散点：回退到该 building 任意散点中“最接近全楼均值中心”的点，并强制 floor=目标楼层
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Tuple


def _read_population_points_from_json(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    agents = data["agents"]["student_agent"]["states"]["default"]["agents"]
    points = []
    for a in agents:
        v = a["variables"]
        points.append(
            {
                "x": float(v["x"]),
                "y": float(v["y"]),
                "building_id": int(v["building_id"]),
                "point_id": int(v["point_id"]),
                "floor": int(v["floor"]),
            }
        )
    return points


def _read_population_points_from_csv(path: str) -> List[Dict[str, Any]]:
    points: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"x", "y", "building_id", "point_id", "floor"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"CSV 缺少必要列: {sorted(required)}，实际列: {reader.fieldnames}")
        for row in reader:
            points.append(
                {
                    "x": float(row["x"]),
                    "y": float(row["y"]),
                    "building_id": int(float(row["building_id"])),
                    "point_id": int(float(row["point_id"])),
                    "floor": int(float(row["floor"])),
                }
            )
    return points


def _read_building_floors_from_geojson(path: str) -> Dict[int, int]:
    with open(path, "r", encoding="utf-8") as f:
        gj = json.load(f)
    floors_by_building: Dict[int, int] = {}
    for feat in gj.get("features", []):
        props = feat.get("properties", {})
        b_id = int(props.get("building_id"))
        floors = int(props.get("floors"))
        floors_by_building[b_id] = floors
    if not floors_by_building:
        raise ValueError(f"未在 {path} 读取到任何 buildings floors 信息（features 为空？）")
    return floors_by_building


def _mean_xy(points: Iterable[Dict[str, Any]]) -> Tuple[float, float]:
    xs: List[float] = []
    ys: List[float] = []
    for p in points:
        xs.append(float(p["x"]))
        ys.append(float(p["y"]))
    if not xs:
        return 0.0, 0.0
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _pick_closest_to_center(points: List[Dict[str, Any]], cx: float, cy: float) -> Dict[str, Any]:
    # 稳健：若距离相同，以 point_id 小者优先
    best = None
    best_key = None
    for p in points:
        dx = float(p["x"]) - cx
        dy = float(p["y"]) - cy
        dist2 = dx * dx + dy * dy
        key = (dist2, int(p["point_id"]))
        if best is None or key < best_key:
            best = p
            best_key = key
    assert best is not None
    return best


def generate_tutor_points(
    population_points: List[Dict[str, Any]],
    floors_by_building: Dict[int, int],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Returns:
        tutor_points: list of dicts
        warnings: list of warning strings
    """
    by_building: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    by_building_floor: Dict[Tuple[int, int], List[Dict[str, Any]]] = defaultdict(list)
    for p in population_points:
        b = int(p["building_id"])
        f = int(p["floor"])
        by_building[b].append(p)
        by_building_floor[(b, f)].append(p)

    warnings: List[str] = []
    tutor_points: List[Dict[str, Any]] = []
    tutor_id = 0

    for building_id in sorted(floors_by_building.keys()):
        floors = int(floors_by_building[building_id])
        b_points = by_building.get(building_id, [])
        if not b_points:
            warnings.append(f"building_id={building_id} 在 population 里没有任何散点，跳过该楼（无法挑选）")
            continue
        b_cx, b_cy = _mean_xy(b_points)

        for floor in range(1, floors + 1):
            layer_points = by_building_floor.get((building_id, floor), [])
            if layer_points:
                cx, cy = _mean_xy(layer_points)
                chosen = _pick_closest_to_center(layer_points, cx, cy)
                source_floor = int(chosen["floor"])
            else:
                # 兜底：该层未出现散点（理论上 base_population/层 足够大时很少发生）
                chosen = _pick_closest_to_center(b_points, b_cx, b_cy)
                source_floor = int(chosen["floor"])
                warnings.append(
                    f"building_id={building_id} floor={floor} 未找到该层散点，"
                    f"回退使用 point_id={chosen['point_id']} (source_floor={source_floor}) 并强制 floor={floor}"
                )

            tutor_points.append(
                {
                    "tutor_id": tutor_id,
                    "building_id": int(building_id),
                    "floor": int(floor),
                    "x": float(chosen["x"]),
                    "y": float(chosen["y"]),
                    "source_point_id": int(chosen["point_id"]),
                    "source_floor": int(source_floor),
                }
            )
            tutor_id += 1

    return tutor_points, warnings


def _write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = ["tutor_id", "building_id", "floor", "x", "y", "source_point_id", "source_floor"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def _write_json(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"tutor_agents": rows}, f, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 tutor agent 表格（每栋楼每层 1 个）")
    parser.add_argument(
        "--population",
        default="data/output/population_points.csv",
        help="输入人口散点（CSV 或 JSON）。默认优先使用 CSV：data/output/population_points.csv",
    )
    parser.add_argument(
        "--buildings",
        default="data/output/transformed_buildings.geojson",
        help="包含 floors/building_id 的建筑物 GeoJSON（默认：data/output/transformed_buildings.geojson）",
    )
    parser.add_argument("--out_csv", default="data/output/tutor_points.csv", help="输出 CSV 路径")
    parser.add_argument("--out_json", default="data/output/tutor_points.json", help="输出 JSON 路径")
    args = parser.parse_args()

    if not os.path.exists(args.population):
        # 自动回退到 JSON
        fallback = "data/output/population_points.json"
        if os.path.exists(fallback):
            args.population = fallback
        else:
            print(f"❌ 找不到人口散点文件: {args.population}（也未找到 {fallback}）")
            return 1

    if not os.path.exists(args.buildings):
        print(f"❌ 找不到建筑物文件: {args.buildings}")
        return 1

    # 读取 population points
    try:
        if args.population.lower().endswith(".json"):
            population_points = _read_population_points_from_json(args.population)
        else:
            population_points = _read_population_points_from_csv(args.population)
    except Exception as e:
        print(f"❌ 读取 population 失败: {e}")
        return 1

    # 读取 building floors
    try:
        floors_by_building = _read_building_floors_from_geojson(args.buildings)
    except Exception as e:
        print(f"❌ 读取 buildings floors 失败: {e}")
        return 1

    tutor_points, warnings = generate_tutor_points(population_points, floors_by_building)

    _write_csv(args.out_csv, tutor_points)
    _write_json(args.out_json, tutor_points)

    expected_total = sum(int(v) for v in floors_by_building.values())
    print("✅ tutor agent 表格生成完成")
    print(f"- population: {args.population}")
    print(f"- buildings: {args.buildings}")
    print(f"- 输出 CSV: {args.out_csv}")
    print(f"- 输出 JSON: {args.out_json}")
    print(f"- tutor 数量: {len(tutor_points)}（期望: {expected_total} = sum(building_floors)）")
    if warnings:
        print(f"⚠ 警告: {len(warnings)} 条（常见于某些楼层随机分配刚好没点）")
        for w in warnings[:20]:
            print("  - " + w)
        if len(warnings) > 20:
            print(f"  ... 其余 {len(warnings) - 20} 条省略")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


