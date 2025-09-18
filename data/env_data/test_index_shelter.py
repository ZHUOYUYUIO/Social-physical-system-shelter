import json
import math
import os
import sys
from typing import List, Tuple, Dict, Any

import csv


def load_graph_nodes(graph_json_path: str) -> List[Dict[str, Any]]:
	with open(graph_json_path, "r", encoding="utf-8") as f:
		data = json.load(f)
	# Expect structure {"nodes": [{"id": "1", "bar": [x, y]}, ...]}
	nodes = data.get("nodes", [])
	return nodes


def load_shelter_points(shelter_csv_path: str) -> List[Dict[str, Any]]:
	points: List[Dict[str, Any]] = []
	with open(shelter_csv_path, "r", encoding="utf-8") as f:
		reader = csv.DictReader(f)
		# Expect headers: index,x,y
		for row in reader:
			points.append({
				"index": row.get("index"),
				"x": float(row.get("x")),
				"y": float(row.get("y")),
			})
	return points


def compute_squared_distance(ax: float, ay: float, bx: float, by: float) -> float:
	return (ax - bx) * (ax - bx) + (ay - by) * (ay - by)


def build_exact_bar_lookup(nodes: List[Dict[str, Any]]) -> Dict[Tuple[float, float], str]:
	lookup: Dict[Tuple[float, float], str] = {}
	for n in nodes:
		bar = n.get("bar")
		if not bar or not isinstance(bar, list) or len(bar) < 2:
			continue
		xn = float(bar[0])
		yn = float(bar[1])
		lookup[(xn, yn)] = str(n.get("id"))
	return lookup


def find_nearest_graph_id_for_point(px: float, py: float, nodes: List[Dict[str, Any]]) -> str:
	best_id: str = ""
	best_d2: float = float("inf")
	for n in nodes:
		bar = n.get("bar")
		if not bar or not isinstance(bar, list) or len(bar) < 2:
			continue
		xn = float(bar[0])
		yn = float(bar[1])
		d2 = compute_squared_distance(px, py, xn, yn)
		if d2 < best_d2:
			best_d2 = d2
			best_id = str(n.get("id"))
	return best_id


def write_shelters_with_graph_id(points: List[Dict[str, Any]], output_csv_path: str) -> None:
	fieldnames = ["index", "x", "y", "graph_id"]
	with open(output_csv_path, "w", encoding="utf-8", newline="") as f:
		writer = csv.DictWriter(f, fieldnames=fieldnames)
		writer.writeheader()
		for p in points:
			writer.writerow(p)


def main():
	# Resolve paths relative to this file inside data/env_data
	current_dir = os.path.dirname(os.path.abspath(__file__))
	graph_json_path = os.path.join(current_dir, "expanded_visibility_graph_renumbered.json")
	shelter_csv_path = os.path.join(current_dir, "..", "output", "shelter_points.csv")
	output_csv_path = os.path.join(current_dir, "..", "output", "shelter_points_with_graph_id.csv")

	if not os.path.exists(graph_json_path):
		print(f"找不到图文件: {graph_json_path}")
		return 1
	if not os.path.exists(shelter_csv_path):
		print(f"找不到shelter CSV: {shelter_csv_path}")
		return 1

	nodes = load_graph_nodes(graph_json_path)
	shelters = load_shelter_points(shelter_csv_path)

	# Build exact (x,y) -> id lookup for precise matches
	exact_lookup = build_exact_bar_lookup(nodes)

	# For each shelter, prefer exact match; otherwise, find nearest by bar coordinates
	for s in shelters:
		key = (s["x"], s["y"])
		gid = exact_lookup.get(key)
		if gid is None:
			gid = find_nearest_graph_id_for_point(s["x"], s["y"], nodes)
		s["graph_id"] = gid

	write_shelters_with_graph_id(shelters, output_csv_path)
	print(f"已写出: {output_csv_path}")
	return 0


if __name__ == "__main__":
	sys.exit(main())
