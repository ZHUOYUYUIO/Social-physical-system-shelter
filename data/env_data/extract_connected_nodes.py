##这个是用来提取连接的节点ID
import json
import os
from typing import Set, List

def extract_connected_node_ids(graph_file_path: str) -> List[str]:
    """
    从图文件中提取所有有连接关系的节点ID

    Args:
        graph_file_path: 图JSON文件的路径

    Returns:
        有连接关系的节点ID列表（排序后的）
    """
    try:
        with open(graph_file_path, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)

        # 使用集合来存储唯一的节点ID
        connected_nodes = set()

        # 遍历所有边，收集连接的节点
        if 'links' in graph_data:
            for link in graph_data['links']:
                if 'source' in link and 'target' in link:
                    connected_nodes.add(link['source'])
                    connected_nodes.add(link['target'])

        # 转换为排序后的列表
        connected_node_list = sorted(list(connected_nodes), key=lambda x: int(x))

        return connected_node_list

    except FileNotFoundError:
        print(f"错误：找不到文件 {graph_file_path}")
        return []
    except json.JSONDecodeError:
        print(f"错误：JSON文件格式不正确 {graph_file_path}")
        return []
    except Exception as e:
        print(f"处理文件时出现错误: {e}")
        return []

def analyze_graph_connectivity(graph_file_path: str) -> dict:
    """
    分析图的连接性，返回详细的统计信息

    Args:
        graph_file_path: 图JSON文件的路径

    Returns:
        包含统计信息的字典
    """
    try:
        with open(graph_file_path, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)

        total_nodes = len(graph_data.get('nodes', []))
        total_links = len(graph_data.get('links', []))

        # 提取连接的节点
        connected_nodes = extract_connected_node_ids(graph_file_path)
        connected_count = len(connected_nodes)

        # 计算孤立节点
        isolated_nodes = []
        if 'nodes' in graph_data:
            all_node_ids = {node['id'] for node in graph_data['nodes']}
            connected_set = set(connected_nodes)
            isolated_nodes = sorted(list(all_node_ids - connected_set), key=lambda x: int(x))

        # 计算边的密度
        if connected_count > 1:
            max_possible_edges = connected_count * (connected_count - 1)
            edge_density = total_links / max_possible_edges if max_possible_edges > 0 else 0
        else:
            edge_density = 0

        return {
            'total_nodes': total_nodes,
            'connected_nodes': connected_count,
            'isolated_nodes': len(isolated_nodes),
            'total_edges': total_links,
            'edge_density': round(edge_density, 4),
            'connected_node_ids': connected_nodes,
            'isolated_node_ids': isolated_nodes
        }

    except Exception as e:
        print(f"分析图时出现错误: {e}")
        return {}

def save_connected_nodes_to_file(connected_nodes: List[str], output_file_path: str):
    """
    将连接的节点ID保存到文件

    Args:
        connected_nodes: 连接的节点ID列表
        output_file_path: 输出文件路径
    """
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump({
                'connected_node_count': len(connected_nodes),
                'connected_node_ids': connected_nodes
            }, f, indent=2, ensure_ascii=False)

        print(f"连接的节点ID已保存到: {output_file_path}")

    except Exception as e:
        print(f"保存文件时出现错误: {e}")

def main():
    """
    主函数：处理buildings_visibility_graph.json文件
    """
    # 设置文件路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    graph_file = os.path.join(current_dir, "buildings_visibility_graph.json")
    output_file = os.path.join(current_dir, "connected_nodes.json")

    # 检查输入文件是否存在
    if not os.path.exists(graph_file):
        print(f"错误：找不到图文件: {graph_file}")
        return

    print("正在分析图的连接性...")
    analysis_result = analyze_graph_connectivity(graph_file)

    if not analysis_result:
        return

    # 输出分析结果
    print("\n=== 图连接性分析结果 ===")
    print(f"总节点数: {analysis_result['total_nodes']}")
    print(f"连接节点数: {analysis_result['connected_nodes']}")
    print(f"孤立节点数: {analysis_result['isolated_nodes']}")
    print(f"总边数: {analysis_result['total_edges']}")
    print(f"边密度: {analysis_result['edge_density']}")

    print(f"\n连接的节点ID ({len(analysis_result['connected_node_ids'])} 个):")
    for i, node_id in enumerate(analysis_result['connected_node_ids'], 1):
        print(f"  {i}. {node_id}")

    if analysis_result['isolated_nodes'] > 0:
        print(f"\n孤立节点ID ({analysis_result['isolated_nodes']} 个):")
        for i, node_id in enumerate(analysis_result['isolated_node_ids'], 1):
            print(f"  {i}. {node_id}")

    # 保存连接的节点到文件
    save_connected_nodes_to_file(analysis_result['connected_node_ids'], output_file)

    print(f"\n分析完成！结果已保存到 {output_file}")

def reassign_node_ids(graph_file_path: str, connected_nodes_file_path: str, output_file_path: str):
    """
    从图文件中过滤出连接节点，并重新分配ID从1开始连续编号

    Args:
        graph_file_path: 原始图JSON文件路径
        connected_nodes_file_path: 连接节点ID文件路径
        output_file_path: 输出文件路径
    """
    import json
    import os

    try:
        # 读取连接节点ID列表
        with open(connected_nodes_file_path, 'r', encoding='utf-8') as f:
            connected_data = json.load(f)
            connected_node_ids = connected_data['connected_node_ids']

        print(f"读取到 {len(connected_node_ids)} 个连接节点ID")

        # 读取原始图数据
        with open(graph_file_path, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)

        # 创建ID映射：原ID -> 新连续ID
        id_mapping = {}
        for i, old_id in enumerate(sorted(connected_node_ids, key=int), 1):
            id_mapping[old_id] = str(i)

        print(f"创建ID映射: {len(id_mapping)} 个映射")

        # 过滤和重新编号节点
        filtered_nodes = []
        for node in graph_data['nodes']:
            if node['id'] in connected_node_ids:
                new_node = {
                    'id': id_mapping[node['id']],
                    'bar': node['bar']
                }
                filtered_nodes.append(new_node)

        print(f"过滤后剩余 {len(filtered_nodes)} 个节点")

        # 过滤和重新编号边
        filtered_links = []
        processed_edges = set()  # 用于记录已处理的边，避免重复

        for link in graph_data['links']:
            if link['source'] in connected_node_ids and link['target'] in connected_node_ids:
                # 创建有序的边标识符，确保 (A,B) 和 (B,A) 被认为是同一条边
                edge_key = tuple(sorted([link['source'], link['target']]))

                if edge_key not in processed_edges:
                    # 添加正向边
                    new_link = {
                        'source': id_mapping[link['source']],
                        'target': id_mapping[link['target']],
                        'foo': link['foo']
                    }
                    filtered_links.append(new_link)

                    # 添加反向边
                    reverse_link = {
                        'source': id_mapping[link['target']],
                        'target': id_mapping[link['source']],
                        'foo': link['foo']
                    }
                    filtered_links.append(reverse_link)

                    # 标记这条边已处理
                    processed_edges.add(edge_key)

        print(f"过滤后剩余 {len(filtered_links)} 条边")

        # 构建输出数据
        output_data = {
            'nodes': filtered_nodes,
            'links': filtered_links
        }

        # 保存到文件
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"重新编号的图已保存到: {output_file_path}")
        print(f"节点ID范围: 1 - {len(filtered_nodes)}")

        return True

    except Exception as e:
        print(f"重新编号过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    主函数：处理buildings_visibility_graph.json文件
    """
    # 设置文件路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    graph_file = os.path.join(current_dir, "buildings_visibility_graph.json")
    connected_file = os.path.join(current_dir, "connected_nodes.json")
    output_file = os.path.join(current_dir, "buildings_visibility_graph_renumbered.json")

    # 检查输入文件是否存在
    if not os.path.exists(graph_file):
        print(f"错误：找不到图文件: {graph_file}")
        return

    if not os.path.exists(connected_file):
        print(f"错误：找不到连接节点文件: {connected_file}")
        return

    print("正在重新编号连接节点的ID...")
    success = reassign_node_ids(graph_file, connected_file, output_file)

    if success:
        print("ID重新编号成功！")
    else:
        print("ID重新编号失败！")

if __name__ == "__main__":
    main()
