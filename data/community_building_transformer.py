#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
社区建筑物坐标转换工具
专门处理社区地理边界和建筑物polygon的坐标转换
功能：
1. 读取社区边界polygon文件
2. 读取建筑物polygon文件
3. 识别坐标系并转换为EPSG:3415
4. 将左下角设置为(0,0)原点
5. 保存转换后的数据
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, Point
from shapely.ops import transform
import pyproj
from pyproj import CRS, Transformer
import numpy as np
import warnings
import os
warnings.filterwarnings('ignore')

class CommunityBuildingTransformer:
    """社区建筑物坐标转换器"""
    
    def __init__(self, target_crs='EPSG:3415'):
        """
        初始化坐标转换器
        
        Parameters:
        -----------
        target_crs : str
            目标坐标系，默认为EPSG:3415
        """
        self.target_crs = target_crs
        self.target_crs_obj = CRS.from_epsg(3415)
        
    def load_community_boundary(self, file_path):
        """
        加载社区边界数据
        
        Parameters:
        -----------
        file_path : str
            社区边界文件路径（支持shp, geojson, gpkg等格式）
            
        Returns:
        --------
        GeoDataFrame : 社区边界数据
        """
        try:
            print(f"正在加载社区边界文件: {file_path}")
            boundary_gdf = gpd.read_file(file_path)
            
            # 检查数据
            if len(boundary_gdf) == 0:
                raise ValueError("社区边界文件为空")
            
            print(f"成功加载社区边界数据，共 {len(boundary_gdf)} 个多边形")
            print(f"坐标系: {boundary_gdf.crs}")
            print(f"边界框: {boundary_gdf.total_bounds}")
            
            return boundary_gdf
            
        except Exception as e:
            print(f"加载社区边界文件失败: {e}")
            raise
    
    def load_buildings(self, file_path):
        """
        加载建筑物数据
        
        Parameters:
        -----------
        file_path : str
            建筑物文件路径（支持shp, geojson, gpkg等格式）
            
        Returns:
        --------
        GeoDataFrame : 建筑物数据
        """
        try:
            print(f"正在加载建筑物文件: {file_path}")
            buildings_gdf = gpd.read_file(file_path)
            
            # 检查数据
            if len(buildings_gdf) == 0:
                raise ValueError("建筑物文件为空")
            
            print(f"成功加载建筑物数据，共 {len(buildings_gdf)} 个建筑物")
            print(f"坐标系: {buildings_gdf.crs}")
            print(f"边界框: {buildings_gdf.total_bounds}")
            
            return buildings_gdf
            
        except Exception as e:
            print(f"加载建筑物文件失败: {e}")
            raise
    
    def check_coordinate_systems(self, boundary_gdf, buildings_gdf):
        """
        检查两个数据集的坐标系是否一致
        
        Parameters:
        -----------
        boundary_gdf : GeoDataFrame
            社区边界数据
        buildings_gdf : GeoDataFrame
            建筑物数据
            
        Returns:
        --------
        bool : 坐标系是否一致
        """
        boundary_crs = boundary_gdf.crs
        buildings_crs = buildings_gdf.crs
        
        print(f"社区边界坐标系: {boundary_crs}")
        print(f"建筑物坐标系: {buildings_crs}")
        
        if boundary_crs == buildings_crs:
            print("✓ 两个数据集的坐标系一致")
            return True
        else:
            print("⚠ 两个数据集的坐标系不一致，需要统一转换")
            return False
    
    def transform_to_target_crs(self, geodata):
        """
        将地理数据转换为目标坐标系
        
        Parameters:
        -----------
        geodata : GeoDataFrame
            输入的地理数据
            
        Returns:
        --------
        GeoDataFrame : 转换后的地理数据
        """
        if geodata.crs is None:
            print("警告：数据没有坐标系信息，假设为WGS84")
            geodata = geodata.set_crs('EPSG:4326')
        
        if str(geodata.crs) != self.target_crs:
            print(f"正在转换坐标系: {geodata.crs} -> {self.target_crs}")
            transformed = geodata.to_crs(self.target_crs)
            return transformed
        else:
            print(f"数据已经是目标坐标系 {self.target_crs}，无需转换")
            return geodata
    
    def set_origin_to_bottom_left(self, boundary_gdf, buildings_gdf):
        """
        将社区边界和建筑物的左下角设置为(0,0)原点
        
        Parameters:
        -----------
        boundary_gdf : GeoDataFrame
            社区边界数据
        buildings_gdf : GeoDataFrame
            建筑物数据
            
        Returns:
        --------
        tuple : (转换后的边界数据, 转换后的建筑物数据, 偏移量)
        """
        # 计算整体边界框（包含边界和建筑物）
        boundary_bounds = boundary_gdf.total_bounds
        buildings_bounds = buildings_gdf.total_bounds
        
        # 计算整体边界
        overall_bounds = [
            min(boundary_bounds[0], buildings_bounds[0]),  # minx
            min(boundary_bounds[1], buildings_bounds[1]),  # miny
            max(boundary_bounds[2], buildings_bounds[2]),  # maxx
            max(boundary_bounds[3], buildings_bounds[3])   # maxy
        ]
        
        minx, miny = overall_bounds[0], overall_bounds[1]
        offset = (minx, miny)
        
        print(f"整体边界框: X({overall_bounds[0]:.2f}, {overall_bounds[2]:.2f}), Y({overall_bounds[1]:.2f}, {overall_bounds[3]:.2f})")
        print(f"偏移量: ({minx:.2f}, {miny:.2f})")
        
        # 转换社区边界
        def translate_boundary_geometry(geom):
            if geom is not None:
                return transform(lambda x, y: (x - minx, y - miny), geom)
            return None
        
        transformed_boundary = boundary_gdf.copy()
        transformed_boundary.geometry = transformed_boundary.geometry.apply(translate_boundary_geometry)
        
        # 转换建筑物
        def translate_building_geometry(geom):
            if geom is not None:
                return transform(lambda x, y: (x - minx, y - miny), geom)
            return None
        
        transformed_buildings = buildings_gdf.copy()
        transformed_buildings.geometry = transformed_buildings.geometry.apply(translate_building_geometry)
        
        return transformed_boundary, transformed_buildings, offset
    
    def process_community_data(self, boundary_file, buildings_file):
        """
        完整的社区数据处理流程
        
        Parameters:
        -----------
        boundary_file : str
            社区边界文件路径
        buildings_file : str
            建筑物文件路径
            
        Returns:
        --------
        dict : 包含处理结果的字典
        """
        print("=== 社区建筑物坐标转换流程 ===")
        
        # 1. 加载数据
        print("\n1. 加载数据文件")
        boundary_gdf = self.load_community_boundary(boundary_file)
        buildings_gdf = self.load_buildings(buildings_file)
        
        # 2. 检查坐标系
        print("\n2. 检查坐标系")
        self.check_coordinate_systems(boundary_gdf, buildings_gdf)
        
        # 3. 转换为目标坐标系
        print("\n3. 转换为目标坐标系")
        transformed_boundary = self.transform_to_target_crs(boundary_gdf)
        transformed_buildings = self.transform_to_target_crs(buildings_gdf)
        
        # 4. 设置原点为左下角
        print("\n4. 设置原点为左下角")
        final_boundary, final_buildings, offset = self.set_origin_to_bottom_left(
            transformed_boundary, transformed_buildings
        )
        
        # 5. 显示结果信息
        print("\n5. 转换完成！")
        print(f"社区边界数量: {len(final_boundary)}")
        print(f"建筑物数量: {len(final_buildings)}")
        print(f"新的社区边界框: {final_boundary.total_bounds}")
        print(f"新的建筑物边界框: {final_buildings.total_bounds}")
        print(f"左下角坐标: ({final_boundary.total_bounds[0]:.2f}, {final_boundary.total_bounds[1]:.2f})")
        
        return {
            'boundary_data': final_boundary,
            'buildings_data': final_buildings,
            'offset': offset,
            'target_crs': self.target_crs,
            'original_boundary_crs': str(boundary_gdf.crs),
            'original_buildings_crs': str(buildings_gdf.crs)
        }
    
    def save_transformed_data(self, result, output_dir='output'):
        """
        保存转换后的数据
        
        Parameters:
        -----------
        result : dict
            转换结果
        output_dir : str
            输出目录
        """
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存社区边界
        boundary_output = os.path.join(output_dir, 'transformed_boundary.shp')
        result['boundary_data'].to_file(boundary_output)
        print(f"社区边界已保存到: {boundary_output}")
        
        # 保存社区边界为GeoJSON格式
        boundary_geojson = os.path.join(output_dir, 'transformed_boundary.geojson')
        result['boundary_data'].to_file(boundary_geojson, driver='GeoJSON')
        print(f"社区边界已保存到: {boundary_geojson}")
        
        # 保存建筑物
        buildings_output = os.path.join(output_dir, 'transformed_buildings.shp')
        result['buildings_data'].to_file(buildings_output)
        print(f"建筑物数据已保存到: {buildings_output}")
        
        # 保存建筑物为GeoJSON格式
        buildings_geojson = os.path.join(output_dir, 'transformed_buildings.geojson')
        result['buildings_data'].to_file(buildings_geojson, driver='GeoJSON')
        print(f"建筑物数据已保存到: {buildings_geojson}")
        
        # 保存转换信息
        info_output = os.path.join(output_dir, 'transformation_info.txt')
        with open(info_output, 'w', encoding='utf-8') as f:
            f.write("坐标转换信息\n")
            f.write("=" * 50 + "\n")
            f.write(f"原始社区边界坐标系: {result['original_boundary_crs']}\n")
            f.write(f"原始建筑物坐标系: {result['original_buildings_crs']}\n")
            f.write(f"目标坐标系: {result['target_crs']}\n")
            f.write(f"偏移量: {result['offset']}\n")
            f.write(f"社区边界数量: {len(result['boundary_data'])}\n")
            f.write(f"建筑物数量: {len(result['buildings_data'])}\n")
            f.write(f"新的社区边界框: {result['boundary_data'].total_bounds}\n")
            f.write(f"新的建筑物边界框: {result['buildings_data'].total_bounds}\n")
        
        print(f"转换信息已保存到: {info_output}")

def create_sample_data():
    """创建示例数据用于测试"""
    # 创建示例社区边界
    community_polygon = Polygon([
        (0, 0), (1000, 0), (1000, 800), (0, 800)
    ])
    boundary_gdf = gpd.GeoDataFrame(geometry=[community_polygon], crs='EPSG:4326')
    
    # 创建示例建筑物
    buildings = [
        Polygon([(100, 100), (200, 100), (200, 200), (100, 200)]),
        Polygon([(300, 150), (400, 150), (400, 250), (300, 250)]),
        Polygon([(500, 300), (600, 300), (600, 400), (500, 400)]),
        Polygon([(700, 200), (800, 200), (800, 300), (700, 300)]),
        Polygon([(150, 500), (250, 500), (250, 600), (150, 600)])
    ]
    buildings_gdf = gpd.GeoDataFrame(geometry=buildings, crs='EPSG:4326')
    
    return boundary_gdf, buildings_gdf

def main():
    """主函数 - 演示使用方法"""
    print("社区建筑物坐标转换工具")
    print("=" * 60)
    
    # 创建转换器
    transformer = CommunityBuildingTransformer(target_crs='EPSG:3415')
    
    # 创建示例数据
    print("创建示例数据...")
    boundary_gdf, buildings_gdf = create_sample_data()
    
    # 保存示例数据
    os.makedirs('sample_data', exist_ok=True)
    boundary_gdf.to_file('sample_data/sample_boundary.shp')
    buildings_gdf.to_file('sample_data/sample_buildings.shp')
    print("示例数据已保存到 sample_data/ 目录")
    
    # 执行转换
    result = transformer.process_community_data(
        'sample_data/sample_boundary.shp',
        'sample_data/sample_buildings.shp'
    )
    
    # 保存结果
    transformer.save_transformed_data(result, 'output')
    
    print("\n转换完成！")
    return result

if __name__ == "__main__":
    main() 