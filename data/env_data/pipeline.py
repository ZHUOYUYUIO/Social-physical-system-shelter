import os
from obstacles_graph_gen import generate_building_graph
from obstacles_graph_gen import is_edge_visible, load_buildings_from_geojson
from extract_connected_nodes import (
    analyze_graph_connectivity,
    save_connected_nodes_to_file,
    reassign_node_ids,
)


def run_env_data_pipeline(
    margin: float = 0.05,
    scale_factor: float = 1.0,
):
    """
    Orchestrate env_data generation:
    1) Generate buildings visibility graph from transformed buildings
    2) Extract connected nodes and save to file
    3) Renumber graph to contiguous IDs and save
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Inputs and outputs
    transformed_buildings_path = os.path.join(current_dir, "..", "output", "transformed_buildings.geojson")
    # 优先使用坐标已转换的shelter；若不存在，回退到用户提供的位置（可能坐标未转换）
    candidate_shelter_paths = [
        os.path.join(current_dir, "..", "output", "transformed_shelter_available.geojson"),
        os.path.join(current_dir, "shelter_available.geojson"),  # 用户提到的 data/env_data/shelter_available.geojson
        os.path.join(current_dir, "..", "shelter_available.geojson"),  # 原始 data/shelter_available.geojson
    ]
    shelters_geojson_path = next((p for p in candidate_shelter_paths if os.path.exists(p)), None)

    # shelter CSV（优先使用）
    shelters_csv_path = os.path.join(current_dir, "..", "output", "shelter_points.csv")
    visibility_graph_path = os.path.join(current_dir, "buildings_visibility_graph.json")
    connected_nodes_path = os.path.join(current_dir, "connected_nodes.json")
    renumbered_graph_path = os.path.join(current_dir, "buildings_visibility_graph_renumbered.json")
    stairwell_withoutput_path = os.path.join(current_dir, "..", "output", "stairwell_withoutput.geojson")
    stop_visibility_output_path = os.path.join(current_dir, "..", "output", "stairwell_stop_visibility.geojson")

    # Validate inputs
    if not os.path.exists(transformed_buildings_path):
        print(
            f"错误：找不到输入文件 {transformed_buildings_path}。请先运行坐标转换流程，生成 transformed_buildings.geojson。"
        )
        return False

    # 1) Generate visibility graph
    print("[1/3] 生成建筑物可视图(buildings_visibility_graph.json)...")
    if not os.path.exists(shelters_csv_path) and shelters_geojson_path is None:
        print("  (提示) 未发现shelter_points.csv或shelter的GeoJSON，跳过shelter点并入。")
    else:
        # 简短提示路径与坐标注意事项
        if os.path.exists(shelters_csv_path):
            rel_csv = os.path.relpath(shelters_csv_path, start=os.path.join(current_dir, "..", ".."))
            print(f"  使用shelter点(CSV): {rel_csv}")
        elif shelters_geojson_path is not None:
            rel_path = os.path.relpath(shelters_geojson_path, start=os.path.join(current_dir, "..", ".."))
            if not rel_path:
                rel_path = shelters_geojson_path
            print(f"  使用shelter点(GeoJSON): {rel_path}")
        if shelters_geojson_path and not shelters_geojson_path.endswith("transformed_shelter_available.geojson"):
            print("  (注意) 使用的shelter文件可能未经过同样的坐标转换，结果可能偏移。建议先生成 transformed_shelter_available.geojson。")
    generate_building_graph(
        geojson_path=transformed_buildings_path,
        output_path=visibility_graph_path,
        margin=margin,
        scale_factor=scale_factor,
        shelters_geojson_path=shelters_geojson_path,
        shelters_csv_path=shelters_csv_path if os.path.exists(shelters_csv_path) else None,
    )

    if not os.path.exists(visibility_graph_path):
        print("生成可视图失败：未找到输出文件。")
        return False

    # 2) Analyze connectivity and save connected nodes
    print("[2/3] 分析连接节点并保存 connected_nodes.json...")
    analysis = analyze_graph_connectivity(visibility_graph_path)
    if not analysis:
        print("图连接性分析失败。")
        return False

    save_connected_nodes_to_file(analysis["connected_node_ids"], connected_nodes_path)

    # 3) Renumber graph to contiguous IDs
    print("[3/3] 依据连接节点重编号，生成 buildings_visibility_graph_renumbered.json...")
    ok = reassign_node_ids(
        graph_file_path=visibility_graph_path,
        connected_nodes_file_path=connected_nodes_path,
        output_file_path=renumbered_graph_path,
    )

    if not ok or not os.path.exists(renumbered_graph_path):
        print("重编号失败。")
        return False

    print("完成：已生成以下文件：")
    print(f"  - {visibility_graph_path}")
    print(f"  - {connected_nodes_path}")
    print(f"  - {renumbered_graph_path}")

    # 4) 可选：扩展可视图，加入 stop 节点及其可见连边
    expanded_graph_path = os.path.join(current_dir, "expanded_visibility_graph.json")
    expanded_graph_renum_path = os.path.join(current_dir, "expanded_visibility_graph_renumbered.json")
    if os.path.exists(stairwell_withoutput_path):
        try:
            print("[4/5] 扩展图：加入 stop(outstop_x, outstop_y) 节点并按可视连边连接...")
            buildings_geojson_path = os.path.join(current_dir, "..", "output", "transformed_buildings.geojson")
            # 加载障碍（原始多边形）
            original_obstacles = load_buildings_from_geojson(buildings_geojson_path)
            original_obstacles_list = []
            for poly in original_obstacles:
                original_obstacles_list.append([ (float(x), float(y)) for x,y in poly.tolist() ])

            import json
            with open(stairwell_withoutput_path, 'r', encoding='utf-8') as f:
                sw_data = json.load(f)
            features = sw_data.get('features', [])

            # 使用重编号后的连通图作为扩展基底，确保计数与口径一致
            with open(renumbered_graph_path, 'r', encoding='utf-8') as f:
                vg = json.load(f)
            nodes = vg.get('nodes', [])
            links = vg.get('links', [])
            node_points = [ (int(n['bar'][0]), int(n['bar'][1])) for n in nodes if 'bar' in n ]
            # 最大已有 id
            used_ids = set(int(n['id']) for n in nodes if 'id' in n)
            next_id = max(used_ids) + 1 if used_ids else 1

            base_node_count = len(nodes)

            added_nodes = 0
            added_links = 0
            for feat in features:
                props = feat.get('properties', {})
                ox = props.get('outstop_x')
                oy = props.get('outstop_y')
                if ox is None or oy is None:
                    continue
                stop_point = (int(round(float(ox))), int(round(float(oy))))
                # 加入 stop 节点
                stop_id = str(next_id)
                nodes.append({ 'id': stop_id, 'bar': [stop_point[0], stop_point[1]] })
                next_id += 1
                added_nodes += 1
                # 对所有节点测试可视连边（双向）
                for i, np in enumerate(node_points):
                    if is_edge_visible(original_obstacles_list, stop_point, np):
                        src = stop_id
                        tgt = str(i+1)  # 注意：i+1 只有在原节点id为1..N 连续时才成立
                        # 更稳健：从 nodes[i]['id'] 取真实id
                        tgt = nodes[i]['id']
                        dist = ((stop_point[0]-np[0])**2 + (stop_point[1]-np[1])**2) ** 0.5
                        links.append({ 'source': src, 'target': tgt, 'foo': float(dist) })
                        links.append({ 'source': tgt, 'target': src, 'foo': float(dist) })
                        added_links += 2
                # 同步追加 stop 点到 node_points，以便后续 stop 之间的连通也可评估（如需要可开启）
                node_points.append(stop_point)

            expanded = { 'nodes': nodes, 'links': links }
            with open(expanded_graph_path, 'w', encoding='utf-8') as f:
                json.dump(expanded, f, ensure_ascii=False, indent=2)
            print(f"  扩展图写出: {expanded_graph_path}，基底节点 {base_node_count} + 新增节点 {added_nodes}，新增边 {added_links}")

            # 基于 connected_nodes.json 重编号扩展图
            print("[5/5] 对扩展图进行重编号...")
            # 先对扩展图做连接性分析，得到连接节点id列表
            with open(expanded_graph_path, 'r', encoding='utf-8') as f:
                expg = json.load(f)
            # 提取连接节点（简单：只要出现在任一边的source/target即认为连接）
            connected_ids = set()
            for e in expg.get('links', []):
                s = e.get('source')
                t = e.get('target')
                if s is not None and t is not None:
                    connected_ids.add(str(s))
                    connected_ids.add(str(t))
            connected_id_list = sorted(list(connected_ids), key=lambda x: int(x))
            # 构建映射并重写
            id_mapping = { old: str(i+1) for i, old in enumerate(connected_id_list) }
            new_nodes = []
            for n in expg.get('nodes', []):
                if n.get('id') in id_mapping:
                    new_nodes.append({ 'id': id_mapping[n['id']], 'bar': n['bar'] })
            new_links = []
            seen = set()
            for e in expg.get('links', []):
                s = e.get('source')
                t = e.get('target')
                if s in id_mapping and t in id_mapping:
                    a = id_mapping[s]
                    b = id_mapping[t]
                    key = tuple(sorted((a,b)))
                    if key in seen:
                        continue
                    new_links.append({ 'source': a, 'target': b, 'foo': e.get('foo', 0.0) })
                    new_links.append({ 'source': b, 'target': a, 'foo': e.get('foo', 0.0) })
                    seen.add(key)
            with open(expanded_graph_renum_path, 'w', encoding='utf-8') as f:
                json.dump({ 'nodes': new_nodes, 'links': new_links }, f, ensure_ascii=False, indent=2)
            print(f"  扩展图重编号写出: {expanded_graph_renum_path}")
        except Exception as e:
            print(f"  扩展图构建失败: {e}")
    else:
        print("[4/5] 跳过：未找到 stairwell_withoutput.geojson。")
    return True


def main():
    run_env_data_pipeline()


if __name__ == "__main__":
    main()


