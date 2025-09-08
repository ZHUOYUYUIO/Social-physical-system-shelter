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

if __name__ == "__main__":
    main()
