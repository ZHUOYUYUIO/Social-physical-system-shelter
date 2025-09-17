import os
from obstacles_graph_gen import generate_building_graph
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
    return True


def main():
    run_env_data_pipeline()


if __name__ == "__main__":
    main()


