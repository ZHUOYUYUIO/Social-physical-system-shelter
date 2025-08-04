#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
建筑物内人口散点生成器
功能：
1. 读取转换后的建筑物geojson文件
2. 在每个建筑物内部生成散点
3. 根据建筑物层数随机分配固定人数
4. 输出符合FlameGPU格式的散点数据
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import random
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
import json
import os
import warnings
warnings.filterwarnings('ignore')
import yaml

class PopulationPointGenerator:
    """人口散点生成器"""
    
    def __init__(self, buildings_file='data/output/transformed_buildings.geojson'):
        """
        初始化生成器
        
        Parameters:
        -----------
        buildings_file : str
            转换后的建筑物geojson文件路径
        """
        self.buildings_file = buildings_file
        self.buildings_gdf = None
        self.population_points = []
        self.point_data = []
        
    def load_buildings(self):
        """
        加载建筑物数据
        
        Returns:
        --------
        bool : 是否成功加载
        """
        try:
            if not os.path.exists(self.buildings_file):
                print(f"❌ 找不到建筑物文件: {self.buildings_file}")
                print("请先运行坐标转换脚本生成建筑物文件")
                return False
            
            print(f"正在加载建筑物文件: {self.buildings_file}")
            self.buildings_gdf = gpd.read_file(self.buildings_file)
            
            if len(self.buildings_gdf) == 0:
                print("❌ 建筑物文件为空")
                return False
            
            print(f"✓ 成功加载 {len(self.buildings_gdf)} 个建筑物")
            return True
            
        except Exception as e:
            print(f"❌ 加载建筑物文件失败: {e}")
            return False
    
    def add_building_floors(self, floors_range=(1, 20)):
        """
        为建筑物添加楼层信息（如果尚未有楼层信息）
        """
        if 'floors' in self.buildings_gdf.columns:
            print("✓ 已检测到建筑物已有楼层信息，直接使用")
            return
        
        # 如果没有楼层信息，则随机生成
        print("⚠ 未检测到楼层信息，将随机生成楼层")
        np.random.seed(42)
        n = len(self.buildings_gdf)
        min_floor, max_floor = floors_range
        floors = np.random.randint(min_floor, max_floor + 1, size=n)
        self.buildings_gdf['floors'] = floors
        print(f"为建筑物添加随机层数信息: {floors}")
    
    def calculate_population_per_floor(self, base_population=50, variance=0.3):
        """
        计算每层的人口数量
        
        Parameters:
        -----------
        base_population : int
            每层基础人口数
        variance : float
            人口变化幅度 (0-1)
            
        Returns:
        --------
        dict : 建筑物ID到人口数的映射
        """
        building_population = {}
        
        for idx, building in self.buildings_gdf.iterrows():
            floors = building['floors']
            # 每层人口数在基础人口数的基础上随机变化
            population_per_floor = int(base_population * (1 + random.uniform(-variance, variance)))
            total_population = floors * population_per_floor
            building_population[idx] = total_population
        
        return building_population
    
    def generate_points_in_building(self, building_geom, num_points, building_id):
        """
        在单个建筑物内生成散点
        
        Parameters:
        -----------
        building_geom : Polygon
            建筑物几何对象
        num_points : int
            要生成的点数
        building_id : int
            建筑物ID
            
        Returns:
        --------
        list : 生成的点列表
        """
        points = []
        attempts = 0
        max_attempts = num_points * 100  # 最大尝试次数
        
        # 获取建筑物的楼层数
        building_floors = self.buildings_gdf.loc[building_id, 'floors']
        
        while len(points) < num_points and attempts < max_attempts:
            attempts += 1
            
            # 获取建筑物的边界框
            minx, miny, maxx, maxy = building_geom.bounds
            
            # 在边界框内随机生成点
            x = random.uniform(minx, maxx)
            y = random.uniform(miny, maxy)
            
            point = Point(x, y)
            
            # 检查点是否在建筑物内部
            if building_geom.contains(point):
                # 随机分配楼层（1到建筑物最高层）
                floor = random.randint(1, building_floors)
                
                points.append({
                    'x': x,
                    'y': y,
                    'building_id': building_id,
                    'point_id': len(points),
                    'floor': floor
                })
        
        if len(points) < num_points:
            print(f"⚠ 建筑物 {building_id} 只能生成 {len(points)}/{num_points} 个点")
        
        return points
    
    def generate_all_population_points(self, base_population=50, variance=0.3):
        """
        为所有建筑物生成人口散点
        
        Parameters:
        -----------
        base_population : int
            每层基础人口数
        variance : float
            人口变化幅度
        """
        print(f"\n=== 生成人口散点 ===")
        print(f"基础人口数/层: {base_population}")
        print(f"人口变化幅度: {variance}")
        
        # 计算每个建筑物的人口数
        building_population = self.calculate_population_per_floor(base_population, variance)
        
        total_population = sum(building_population.values())
        print(f"总人口数: {total_population}")
        
        # 为每个建筑物生成散点
        all_points = []
        for idx, building in self.buildings_gdf.iterrows():
            building_id = idx
            building_geom = building.geometry
            num_points = building_population[building_id]
            
            print(f"建筑物 {building_id}: {building['floors']}层, {num_points}人")
            
            # 生成该建筑物内的散点
            building_points = self.generate_points_in_building(
                building_geom, num_points, building_id
            )
            
            all_points.extend(building_points)
        
        self.population_points = all_points
        print(f"\n✓ 成功生成 {len(all_points)} 个散点")
        
        return all_points
    
    def save_to_flamegpu_format(self, output_file='data/output/population_points.json'):
        """
        保存为FlameGPU格式的数据
        
        Parameters:
        -----------
        output_file : str
            输出文件路径
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 转换为FlameGPU格式
        flamegpu_data = {
            "agents": {
                "student_agent": {
                    "variables": {
                        "x": {"type": "float", "default": 0.0},
                        "y": {"type": "float", "default": 0.0},
                        "building_id": {"type": "int", "default": -1},
                        "point_id": {"type": "int", "default": -1},
                        "floor": {"type": "int", "default": 1}
                    },
                    "states": {
                        "default": {
                            "agents": []
                        }
                    }
                }
            }
        }
        
        # 添加所有散点数据
        for point in self.population_points:
            agent_data = {
                "variables": {
                    "x": point['x'],
                    "y": point['y'],
                    "building_id": point['building_id'],
                    "point_id": point['point_id'],
                    "floor": point['floor']
                }
            }
            flamegpu_data["agents"]["student_agent"]["states"]["default"]["agents"].append(agent_data)
        
        # 保存JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(flamegpu_data, f, indent=2, ensure_ascii=False)
        
        print(f"FlameGPU格式数据已保存: {output_file}")
        
        return flamegpu_data
    
    def save_to_csv(self, output_file='data/output/population_points.csv'):
        """
        保存为CSV格式的数据
        
        Parameters:
        -----------
        output_file : str
            输出文件路径
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 创建DataFrame
        df = pd.DataFrame(self.population_points)
        
        # 保存CSV文件
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        print(f"CSV格式数据已保存: {output_file}")
        
        return df
    
    def save_to_geojson(self, output_file='data/output/population_points.geojson'):
        """
        保存为GeoJSON格式的数据
        
        Parameters:
        -----------
        output_file : str
            输出文件路径
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 创建点几何对象
        points = [Point(point['x'], point['y']) for point in self.population_points]
        
        # 创建GeoDataFrame
        gdf = gpd.GeoDataFrame(
            {
                'building_id': [p['building_id'] for p in self.population_points],
                'point_id': [p['point_id'] for p in self.population_points],
                'floor': [p['floor'] for p in self.population_points]
            },
            geometry=points,
            crs=self.buildings_gdf.crs
        )
        
        # 保存GeoJSON文件
        gdf.to_file(output_file, driver='GeoJSON')
        
        print(f"GeoJSON格式数据已保存: {output_file}")
        
        return gdf
    
    def generate_flamegpu_code(self, output_file='data/output/flamegpu_population_code.py'):
        """
        生成FlameGPU代码示例
        
        Parameters:
        -----------
        output_file : str
            输出文件路径
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 创建散点数据字符串
        points_str = "[\n"
        for i, point in enumerate(self.population_points):
            points_str += f"        {{'x': {point['x']}, 'y': {point['y']}, 'building_id': {point['building_id']}, 'point_id': {point['point_id']}, 'floor': {point['floor']}}}{',' if i < len(self.population_points) - 1 else ''}\n"
        points_str += "    ]"
        
        code_template = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FlameGPU人口散点初始化代码
基于生成的散点数据
"""

import random

def initialize_student_agent_population(studentAgentPopulation):
    """
    初始化学生代理种群
    使用从建筑物散点生成的数据
    """
    # 从JSON文件加载的散点数据
    population_data = {points_str}
    
    num_student_agents = len(population_data)
    print(f"初始化 {{num_student_agents}} 个学生代理个体")
    
    for i in range(num_student_agents):
        student_agent = studentAgentPopulation[i]
        point_data = population_data[i]
        
        # 设置位置坐标
        student_agent.setVariableFloat("x", point_data['x'])
        student_agent.setVariableFloat("y", point_data['y'])
        
        # 设置建筑物信息
        student_agent.setVariableInt("building_id", point_data['building_id'])
        student_agent.setVariableInt("point_id", point_data['point_id'])
        student_agent.setVariableInt("floor", point_data['floor'])
    
    print("学生代理种群初始化完成")

# 使用示例：
# from flamegpu import *
# 
# # 创建模型
# model = pyflamegpu.ModelDescription("Population Model")
# 
# # 添加代理类型
# student_agent = model.newAgent("student_agent")
# student_agent.newVariableFloat("x")
# student_agent.newVariableFloat("y")
# student_agent.newVariableInt("building_id")
# student_agent.newVariableInt("point_id")
# student_agent.newVariableInt("floor")
# 
# # 初始化种群
# init_population = model.newAgentFunction("init_population")
# init_population.setFunction(initialize_student_agent_population)
# 
# # 运行模型...
'''
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code_template)
        
        print(f"FlameGPU代码示例已保存: {output_file}")
    
    def create_visualization(self, output_file='data/output/population_visualization.png'):
        """
        创建人口散点可视化图表
        
        Parameters:
        -----------
        output_file : str
            输出文件路径
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            from matplotlib.colors import ListedColormap
            import numpy as np
            
            # 准备数据
            df = pd.DataFrame(self.population_points)
            
            # 创建图形和子图
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
            
            # 获取所有楼层
            unique_floors = sorted(df['floor'].unique())
            
            # 创建颜色映射
            colors = plt.cm.viridis(np.linspace(0, 1, len(unique_floors)))
            
            # 绘制散点图
            for i, floor in enumerate(unique_floors):
                floor_points = df[df['floor'] == floor]
                ax1.scatter(floor_points['x'], floor_points['y'], 
                           c=[colors[i]], alpha=0.7, s=30, edgecolors='white', linewidth=0.5,
                           label=f'Floor {floor} ({len(floor_points)} people)')
            
            # 绘制建筑物轮廓
            for idx, building in self.buildings_gdf.iterrows():
                coords = list(building.geometry.exterior.coords)
                x_coords = [coord[0] for coord in coords]
                y_coords = [coord[1] for coord in coords]
                ax1.plot(x_coords, y_coords, 'k-', linewidth=2, alpha=0.8)
            
            # 设置散点图属性
            ax1.set_title('Population Distribution in Buildings (Colored by Floor)', fontsize=14, fontweight='bold')
            ax1.set_xlabel('X Coordinate (meters)', fontsize=12)
            ax1.set_ylabel('Y Coordinate (meters)', fontsize=12)
            ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
            ax1.grid(True, alpha=0.3)
            ax1.set_aspect('equal')
            
            # 绘制楼层分布柱状图
            floor_counts = df['floor'].value_counts().sort_index()
            bars = ax2.bar(floor_counts.index, floor_counts.values, 
                          color='lightblue', alpha=0.8, edgecolor='black', linewidth=1)
            
            # 在柱状图上添加数值标签
            for bar, count in zip(bars, floor_counts.values):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + max(floor_counts.values)*0.01,
                        f'{count}', ha='center', va='bottom', fontweight='bold')
            
            # 设置柱状图属性
            ax2.set_title('Population Distribution by Floor', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Floor', fontsize=12)
            ax2.set_ylabel('Population Count', fontsize=12)
            ax2.grid(True, alpha=0.3, axis='y')
            
            # 添加统计信息
            total_population = len(df)
            floors = df['floor'].unique()
            ax2.text(0.02, 0.98, f'Total Population: {total_population} people\nFloor Range: {min(floors)}-{max(floors)}\nBuildings: {len(self.buildings_gdf)}',
                    transform=ax2.transAxes, fontsize=10, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            # 调整布局
            plt.tight_layout()
            
            # 保存图片
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"可视化图表已保存: {output_file}")
            
        except ImportError:
            print("⚠ matplotlib未安装，跳过可视化")
        except Exception as e:
            print(f"创建可视化失败: {e}")
    
    def create_3d_visualization(self, output_file='data/output/building_population_3d.png'):
        """
        创建3D人口散点可视化图表
        
        Parameters:
        -----------
        output_file : str
            输出文件路径
        """
        try:
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            import numpy as np
            
            # 准备数据
            df = pd.DataFrame(self.population_points)
            
            # 创建3D图形
            fig = plt.figure(figsize=(14, 10))
            ax = fig.add_subplot(111, projection='3d')
            
            # 获取所有楼层
            unique_floors = sorted(df['floor'].unique())
            
            # 创建颜色映射
            colors = plt.cm.viridis(np.linspace(0, 1, len(unique_floors)))
            
            # 绘制3D散点图
            for i, floor in enumerate(unique_floors):
                floor_points = df[df['floor'] == floor]
                ax.scatter(floor_points['x'], floor_points['y'], floor_points['floor'],
                          c=[colors[i]], alpha=0.7, s=40, edgecolors='white', linewidth=0.5,
                          label=f'Floor {floor} ({len(floor_points)} people)')
            
            # 绘制建筑物底面轮廓
            for idx, building in self.buildings_gdf.iterrows():
                coords = list(building.geometry.exterior.coords)
                x_coords = [coord[0] for coord in coords]
                y_coords = [coord[1] for coord in coords]
                z_coords = [0] * len(x_coords)  # 底面
                ax.plot(x_coords, y_coords, z_coords, 'k-', linewidth=2, alpha=0.8)
            
            # 设置3D图属性
            ax.set_title('3D Population Distribution in Buildings', fontsize=16, fontweight='bold')
            ax.set_xlabel('X Coordinate (meters)', fontsize=12)
            ax.set_ylabel('Y Coordinate (meters)', fontsize=12)
            ax.set_zlabel('Floor', fontsize=12)
            ax.legend(bbox_to_anchor=(1.15, 1), loc='upper left', fontsize=10)
            
            # 设置视角
            ax.view_init(elev=20, azim=45)
            
            # 保存图片
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"3D可视化图表已保存: {output_file}")
            
        except ImportError:
            print("⚠ matplotlib 3D未安装，跳过3D可视化")
        except Exception as e:
            print(f"创建3D可视化失败: {e}")
    
    def create_interactive_visualization(self, output_file='data/output/building_population_interactive.html'):
        """
        创建交互式HTML可视化
        
        Parameters:
        -----------
        output_file : str
            输出文件路径
        """
        try:
            import plotly.graph_objects as go
            import plotly.express as px
            from plotly.subplots import make_subplots
            
            # 准备数据
            df = pd.DataFrame(self.population_points)
            
            # 创建子图
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Population Distribution in Buildings', 'Population Statistics by Floor'),
                specs=[[{"type": "scatter"}, {"type": "bar"}]]
            )
            
            # 获取所有楼层
            unique_floors = sorted(df['floor'].unique())
            
            # 为每个楼层创建散点图
            for floor in unique_floors:
                floor_data = df[df['floor'] == floor]
                
                fig.add_trace(
                    go.Scatter(
                        x=floor_data['x'],
                        y=floor_data['y'],
                        mode='markers',
                        name=f'Floor {floor}',
                        marker=dict(
                            size=8,
                            opacity=0.7,
                            line=dict(width=1, color='white')
                        ),
                        hovertemplate=f'Floor {floor}<br>X: %{{x:.2f}}<br>Y: %{{y:.2f}}<br>Building ID: %{{text}}<extra></extra>',
                        text=floor_data['building_id']
                    ),
                    row=1, col=1
                )
            
            # 添加建筑物轮廓
            for idx, building in self.buildings_gdf.iterrows():
                coords = list(building.geometry.exterior.coords)
                x_coords = [coord[0] for coord in coords]
                y_coords = [coord[1] for coord in coords]
                
                fig.add_trace(
                    go.Scatter(
                        x=x_coords,
                        y=y_coords,
                        mode='lines',
                        name=f'Building {idx}',
                        line=dict(color='black', width=2),
                        showlegend=False,
                        hoverinfo='skip'
                    ),
                    row=1, col=1
                )
            
            # 楼层分布柱状图
            floor_counts = df['floor'].value_counts().sort_index()
            
            fig.add_trace(
                go.Bar(
                    x=floor_counts.index,
                    y=floor_counts.values,
                    name='Population by Floor',
                    marker_color='lightblue',
                    hovertemplate='Floor %{x}<br>Population: %{y}<extra></extra>'
                ),
                row=1, col=2
            )
            
            # 更新布局
            fig.update_layout(
                title_text="Interactive Population Distribution Visualization",
                title_x=0.5,
                showlegend=True,
                height=600,
                width=1200
            )
            
            # 更新坐标轴
            fig.update_xaxes(title_text="X Coordinate (meters)", row=1, col=1)
            fig.update_yaxes(title_text="Y Coordinate (meters)", row=1, col=1)
            fig.update_xaxes(title_text="Floor", row=1, col=2)
            fig.update_yaxes(title_text="Population Count", row=1, col=2)
            
            # 保存HTML文件
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            fig.write_html(output_file)
            print(f"交互式可视化已保存: {output_file}")
            
        except ImportError:
            print("⚠ plotly未安装，跳过交互式可视化")
        except Exception as e:
            print(f"创建交互式可视化失败: {e}")
    
    def process_data(self, base_population, variance=0.3):
        """
        完整的数据处理流程
        
        Parameters:
        -----------
        base_population : int
            每层基础人口数
        variance : float
            人口变化幅度
            
        Returns:
        --------
        dict : 处理结果
        """
        print("=== 建筑物内人口散点生成器 ===")
        
        # 1. 加载建筑物数据
        if not self.load_buildings():
            return None
        
        # 2. 添加建筑物层数信息
        self.add_building_floors()
        
        # 3. 生成人口散点
        points = self.generate_all_population_points(base_population, variance)
        
        # 4. 保存各种格式的数据
        flamegpu_data = self.save_to_flamegpu_format()
        csv_data = self.save_to_csv()
        geojson_data = self.save_to_geojson()
        
        # 5. 生成FlameGPU代码示例
        self.generate_flamegpu_code()
        
        # 6. 创建可视化
        self.create_visualization()
        self.create_3d_visualization()
        self.create_interactive_visualization()
        
        # 7. 显示统计信息
        print(f"\n=== 生成结果统计 ===")
        print(f"建筑物数量: {len(self.buildings_gdf)}")
        print(f"散点总数: {len(self.population_points)}")
        print(f"平均每建筑物散点数: {len(self.population_points)/len(self.buildings_gdf):.1f}")
        
        # 按建筑物统计
        building_stats = {}
        for point in self.population_points:
            building_id = point['building_id']
            if building_id not in building_stats:
                building_stats[building_id] = 0
            building_stats[building_id] += 1
        
        print(f"散点分布:")
        for building_id, count in building_stats.items():
            floors = self.buildings_gdf.loc[building_id, 'floors']
            print(f"  建筑物{building_id}: {floors}层, {count}个散点")
        
        return {
            'points': self.population_points,
            'buildings': self.buildings_gdf,
            'flamegpu_data': flamegpu_data,
            'csv_data': csv_data,
            'geojson_data': geojson_data
        }

def main():
    """主函数"""
    print("建筑物内人口散点生成器")
    print("=" * 50)
    
    # 读取配置参数
    config_path = os.path.join(os.path.dirname(__file__), '../config/env.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        base_population = config.get('base_population', 50) 
    else:
        base_population = 50
    variance = 0.3  # 人口变化幅度
    
    # 创建生成器
    generator = PopulationPointGenerator()
    
    try:
        # 执行生成
        result = generator.process_data(base_population, variance)
        
        if result:
            print("\n✅ 散点生成成功！")
            print("输出文件保存在 data/output/ 目录下：")
            print("- data/output/population_points.json (FlameGPU格式)")
            print("- data/output/population_points.csv (CSV格式)")
            print("- data/output/population_points.geojson (GeoJSON格式)")
            print("- data/output/flamegpu_population_code.py (FlameGPU代码示例)")
            print("- data/output/population_visualization.png (可视化图表)")
            print("- data/output/building_population_3d.png (3D可视化图表)")
            print("- data/output/building_population_interactive.html (交互式可视化)")
        else:
            print("\n❌ 散点生成失败")
            
    except Exception as e:
        print(f"❌ 运行失败: {e}")

if __name__ == "__main__":
    main() 