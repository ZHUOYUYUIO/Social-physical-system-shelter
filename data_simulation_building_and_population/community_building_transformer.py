#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
社区建筑物坐标转换工具
专门处理社区地理边界和建筑物polygon的坐标转换
功能：
1. 读取社区边界polygon文件
2. 读取建筑物polygon文件
3. 读取楼梯间polygon文件
4. 识别坐标系并转换为EPSG:3415
5. 将左下角设置为(0,0)原点
6. 保存转换后的数据
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
    
    def load_stairwell(self, file_path):
        """
        加载楼梯间数据
        
        Parameters:
        -----------
        file_path : str
            楼梯间文件路径（支持shp, geojson, gpkg等格式）
            
        Returns:
        --------
        GeoDataFrame : 楼梯间数据
        """
        try:
            print(f"正在加载楼梯间文件: {file_path}")
            stairwell_gdf = gpd.read_file(file_path)
            
            # 检查数据
            if len(stairwell_gdf) == 0:
                raise ValueError("楼梯间文件为空")
            
            print(f"成功加载楼梯间数据，共 {len(stairwell_gdf)} 个楼梯间")
            print(f"坐标系: {stairwell_gdf.crs}")
            print(f"边界框: {stairwell_gdf.total_bounds}")
            
            return stairwell_gdf
            
        except Exception as e:
            print(f"加载楼梯间文件失败: {e}")
            raise
    
    def load_shelter(self, file_path):
        """
        加载避难所可用区域数据

        Parameters:
        -----------
        file_path : str
            避难所文件路径（支持shp, geojson, gpkg等格式）

        Returns:
        --------
        GeoDataFrame : 避难所数据
        """
        try:
            print(f"正在加载避难所文件: {file_path}")
            shelter_gdf = gpd.read_file(file_path)

            if len(shelter_gdf) == 0:
                raise ValueError("避难所文件为空")

            print(f"成功加载避难所数据，共 {len(shelter_gdf)} 个要素")
            print(f"坐标系: {shelter_gdf.crs}")
            print(f"边界框: {shelter_gdf.total_bounds}")

            return shelter_gdf

        except Exception as e:
            print(f"加载避难所文件失败: {e}")
            raise

    def load_familiar_point(self, file_path):
        """
        加载熟悉点数据

        Parameters:
        -----------
        file_path : str
            熟悉点文件路径（支持shp, geojson, gpkg等格式）

        Returns:
        --------
        GeoDataFrame : 熟悉点数据
        """
        try:
            print(f"正在加载熟悉点文件: {file_path}")
            familiar_point_gdf = gpd.read_file(file_path)

            if len(familiar_point_gdf) == 0:
                raise ValueError("熟悉点文件为空")

            print(f"成功加载熟悉点数据，共 {len(familiar_point_gdf)} 个点")
            print(f"坐标系: {familiar_point_gdf.crs}")
            print(f"边界框: {familiar_point_gdf.total_bounds}")

            return familiar_point_gdf

        except Exception as e:
            print(f"加载熟悉点文件失败: {e}")
            raise

    def check_coordinate_systems(self, boundary_gdf, buildings_gdf, stairwell_gdf=None, shelter_gdf=None, familiar_point_gdf=None):
        """
        检查数据集的坐标系是否一致
        
        Parameters:
        -----------
        boundary_gdf : GeoDataFrame
            社区边界数据
        buildings_gdf : GeoDataFrame
            建筑物数据
        stairwell_gdf : GeoDataFrame, optional
            楼梯间数据
        shelter_gdf : GeoDataFrame, optional
            避难所数据
        familiar_point_gdf : GeoDataFrame, optional
            熟悉点数据
            
        Returns:
        --------
        bool : 坐标系是否一致
        """
        boundary_crs = boundary_gdf.crs
        buildings_crs = buildings_gdf.crs

        print(f"社区边界坐标系: {boundary_crs}")
        print(f"建筑物坐标系: {buildings_crs}")

        if stairwell_gdf is not None:
            stairwell_crs = stairwell_gdf.crs
            print(f"楼梯间坐标系: {stairwell_crs}")
        if shelter_gdf is not None:
            shelter_crs = shelter_gdf.crs
            print(f"避难所坐标系: {shelter_crs}")
        if familiar_point_gdf is not None:
            familiar_point_crs = familiar_point_gdf.crs
            print(f"熟悉点坐标系: {familiar_point_crs}")

        crs_list = [boundary_crs, buildings_crs]
        if stairwell_gdf is not None:
            crs_list.append(stairwell_gdf.crs)
        if shelter_gdf is not None:
            crs_list.append(shelter_gdf.crs)
        if familiar_point_gdf is not None:
            crs_list.append(familiar_point_gdf.crs)

        unique_crs = set(map(str, crs_list))
        if len(unique_crs) == 1:
            print("✓ 所有数据集的坐标系一致")
            return True
        else:
            print("⚠ 数据集的坐标系不一致，需要统一转换")
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
    
    def set_origin_to_bottom_left(self, boundary_gdf, buildings_gdf, stairwell_gdf=None, shelter_gdf=None, familiar_point_gdf=None):
        """
        将社区边界、建筑物、楼梯间、避难所和熟悉点的左下角设置为(0,0)原点
        
        Parameters:
        -----------
        boundary_gdf : GeoDataFrame
            社区边界数据
        buildings_gdf : GeoDataFrame
            建筑物数据
        stairwell_gdf : GeoDataFrame, optional
            楼梯间数据
        shelter_gdf : GeoDataFrame, optional
            避难所数据
        familiar_point_gdf : GeoDataFrame, optional
            熟悉点数据
            
        Returns:
        --------
        tuple : (转换后的边界数据, 转换后的建筑物数据, 转换后的楼梯间数据, 转换后的避难所数据, 转换后的熟悉点数据, 偏移量)
        """
        # 计算整体边界框（包含边界、建筑物和楼梯间）
        boundary_bounds = boundary_gdf.total_bounds
        buildings_bounds = buildings_gdf.total_bounds
        
        overall_bounds = [
            min(boundary_bounds[0], buildings_bounds[0]),  # minx
            min(boundary_bounds[1], buildings_bounds[1]),  # miny
            max(boundary_bounds[2], buildings_bounds[2]),  # maxx
            max(boundary_bounds[3], buildings_bounds[3])   # maxy
        ]
        
        if stairwell_gdf is not None:
            stairwell_bounds = stairwell_gdf.total_bounds
            overall_bounds = [
                min(overall_bounds[0], stairwell_bounds[0]),  # minx
                min(overall_bounds[1], stairwell_bounds[1]),  # miny
                max(overall_bounds[2], stairwell_bounds[2]),  # maxx
                max(overall_bounds[3], stairwell_bounds[3])   # maxy
            ]
        if shelter_gdf is not None:
            shelter_bounds = shelter_gdf.total_bounds
            overall_bounds = [
                min(overall_bounds[0], shelter_bounds[0]),  # minx
                min(overall_bounds[1], shelter_bounds[1]),  # miny
                max(overall_bounds[2], shelter_bounds[2]),  # maxx
                max(overall_bounds[3], shelter_bounds[3])   # maxy
            ]
        if familiar_point_gdf is not None:
            familiar_point_bounds = familiar_point_gdf.total_bounds
            overall_bounds = [
                min(overall_bounds[0], familiar_point_bounds[0]),  # minx
                min(overall_bounds[1], familiar_point_bounds[1]),  # miny
                max(overall_bounds[2], familiar_point_bounds[2]),  # maxx
                max(overall_bounds[3], familiar_point_bounds[3])   # maxy
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
        
        # 转换楼梯间
        transformed_stairwell = None
        if stairwell_gdf is not None:
            def translate_stairwell_geometry(geom):
                if geom is not None:
                    return transform(lambda x, y: (x - minx, y - miny), geom)
                return None
            
            transformed_stairwell = stairwell_gdf.copy()
            transformed_stairwell.geometry = transformed_stairwell.geometry.apply(translate_stairwell_geometry)

        # 转换避难所
        transformed_shelter = None
        if shelter_gdf is not None:
            def translate_shelter_geometry(geom):
                if geom is not None:
                    return transform(lambda x, y: (x - minx, y - miny), geom)
                return None

            transformed_shelter = shelter_gdf.copy()
            transformed_shelter.geometry = transformed_shelter.geometry.apply(translate_shelter_geometry)

        # 转换熟悉点
        transformed_familiar_point = None
        if familiar_point_gdf is not None:
            def translate_familiar_point_geometry(geom):
                if geom is not None:
                    return transform(lambda x, y: (x - minx, y - miny), geom)
                return None

            transformed_familiar_point = familiar_point_gdf.copy()
            transformed_familiar_point.geometry = transformed_familiar_point.geometry.apply(translate_familiar_point_geometry)

        return transformed_boundary, transformed_buildings, transformed_stairwell, transformed_shelter, transformed_familiar_point, offset
    
    def process_community_data(self, boundary_file, buildings_file, stairwell_file=None, shelter_file=None, familiar_point_file=None):
        """
        完整的社区数据处理流程
        
        Parameters:
        -----------
        boundary_file : str
            社区边界文件路径
        buildings_file : str
            建筑物文件路径
        stairwell_file : str, optional
            楼梯间文件路径
        shelter_file : str, optional
            避难所文件路径
        familiar_point_file : str, optional
            熟悉点文件路径
            
        Returns:
        --------
        dict : 包含处理结果的字典
        """
        print("=== 社区建筑物坐标转换流程 ===")
        
        # 1. 加载数据
        print("\n1. 加载数据文件")
        boundary_gdf = self.load_community_boundary(boundary_file)
        buildings_gdf = self.load_buildings(buildings_file)
        
        stairwell_gdf = None
        if stairwell_file:
            stairwell_gdf = self.load_stairwell(stairwell_file)
        shelter_gdf = None
        if shelter_file:
            shelter_gdf = self.load_shelter(shelter_file)
        familiar_point_gdf = None
        if familiar_point_file:
            familiar_point_gdf = self.load_familiar_point(familiar_point_file)
        
        # 2. 检查坐标系
        print("\n2. 检查坐标系")
        self.check_coordinate_systems(boundary_gdf, buildings_gdf, stairwell_gdf, shelter_gdf, familiar_point_gdf)
        
        # 3. 转换为目标坐标系
        print("\n3. 转换为目标坐标系")
        transformed_boundary = self.transform_to_target_crs(boundary_gdf)
        transformed_buildings = self.transform_to_target_crs(buildings_gdf)
        
        transformed_stairwell = None
        if stairwell_gdf is not None:
            transformed_stairwell = self.transform_to_target_crs(stairwell_gdf)
        transformed_shelter = None
        if shelter_gdf is not None:
            transformed_shelter = self.transform_to_target_crs(shelter_gdf)
        transformed_familiar_point = None
        if familiar_point_gdf is not None:
            transformed_familiar_point = self.transform_to_target_crs(familiar_point_gdf)
        
        # 4. 设置原点为左下角
        print("\n4. 设置原点为左下角")
        final_boundary, final_buildings, final_stairwell, final_shelter, final_familiar_point, offset = self.set_origin_to_bottom_left(
            transformed_boundary, transformed_buildings, transformed_stairwell, transformed_shelter, transformed_familiar_point
        )
        
        # 5. 显示结果信息
        print("\n5. 转换完成！")
        print(f"社区边界数量: {len(final_boundary)}")
        print(f"建筑物数量: {len(final_buildings)}")
        if final_stairwell is not None:
            print(f"楼梯间数量: {len(final_stairwell)}")
        if final_shelter is not None:
            print(f"避难所数量: {len(final_shelter)}")
        if final_familiar_point is not None:
            print(f"熟悉点数量: {len(final_familiar_point)}")
        print(f"新的社区边界框: {final_boundary.total_bounds}")
        print(f"新的建筑物边界框: {final_buildings.total_bounds}")
        if final_stairwell is not None:
            print(f"新的楼梯间边界框: {final_stairwell.total_bounds}")
        if final_shelter is not None:
            print(f"新的避难所边界框: {final_shelter.total_bounds}")
        if final_familiar_point is not None:
            print(f"新的熟悉点边界框: {final_familiar_point.total_bounds}")
        print(f"左下角坐标: ({final_boundary.total_bounds[0]:.2f}, {final_boundary.total_bounds[1]:.2f})")
        
        result = {
            'boundary_data': final_boundary,
            'buildings_data': final_buildings,
            'offset': offset,
            'target_crs': self.target_crs,
            'original_boundary_crs': str(boundary_gdf.crs),
            'original_buildings_crs': str(buildings_gdf.crs)
        }
        
        if final_stairwell is not None:
            result['stairwell_data'] = final_stairwell
            result['original_stairwell_crs'] = str(stairwell_gdf.crs)
        if final_shelter is not None:
            result['shelter_data'] = final_shelter
            result['original_shelter_crs'] = str(shelter_gdf.crs)
        if final_familiar_point is not None:
            result['familiar_point_data'] = final_familiar_point
            result['original_familiar_point_crs'] = str(familiar_point_gdf.crs)
        
        return result
    
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
        
        # 保存楼梯间（如果存在）
        if 'stairwell_data' in result:
            stairwell_output = os.path.join(output_dir, 'transformed_stairwell.shp')
            result['stairwell_data'].to_file(stairwell_output)
            print(f"楼梯间数据已保存到: {stairwell_output}")
            
            # 保存楼梯间为GeoJSON格式
            stairwell_geojson = os.path.join(output_dir, 'transformed_stairwell.geojson')
            result['stairwell_data'].to_file(stairwell_geojson, driver='GeoJSON')
            print(f"楼梯间数据已保存到: {stairwell_geojson}")

        # 保存避难所（如果存在）
        if 'shelter_data' in result:
            shelter_output = os.path.join(output_dir, 'transformed_shelter_available.shp')
            result['shelter_data'].to_file(shelter_output)
            print(f"避难所数据已保存到: {shelter_output}")

            shelter_geojson = os.path.join(output_dir, 'transformed_shelter_available.geojson')
            result['shelter_data'].to_file(shelter_geojson, driver='GeoJSON')
            print(f"避难所数据已保存到: {shelter_geojson}")

        # 保存熟悉点（如果存在）
        if 'familiar_point_data' in result:
            familiar_point_output = os.path.join(output_dir, 'transformed_familiar_point.shp')
            result['familiar_point_data'].to_file(familiar_point_output)
            print(f"熟悉点数据已保存到: {familiar_point_output}")

            familiar_point_geojson = os.path.join(output_dir, 'transformed_familiar_point.geojson')
            result['familiar_point_data'].to_file(familiar_point_geojson, driver='GeoJSON')
            print(f"熟悉点数据已保存到: {familiar_point_geojson}")
        
        # 保存转换信息
        info_output = os.path.join(output_dir, 'transformation_info.txt')
        with open(info_output, 'w', encoding='utf-8') as f:
            f.write("坐标转换信息\n")
            f.write("=" * 50 + "\n")
            f.write(f"原始社区边界坐标系: {result['original_boundary_crs']}\n")
            f.write(f"原始建筑物坐标系: {result['original_buildings_crs']}\n")
            if 'original_stairwell_crs' in result:
                f.write(f"原始楼梯间坐标系: {result['original_stairwell_crs']}\n")
            if 'original_shelter_crs' in result:
                f.write(f"原始避难所坐标系: {result['original_shelter_crs']}\n")
            if 'original_familiar_point_crs' in result:
                f.write(f"原始熟悉点坐标系: {result['original_familiar_point_crs']}\n")
            f.write(f"目标坐标系: {result['target_crs']}\n")
            f.write(f"偏移量: {result['offset']}\n")
            f.write(f"社区边界数量: {len(result['boundary_data'])}\n")
            f.write(f"建筑物数量: {len(result['buildings_data'])}\n")
            if 'stairwell_data' in result:
                f.write(f"楼梯间数量: {len(result['stairwell_data'])}\n")
            if 'shelter_data' in result:
                f.write(f"避难所数量: {len(result['shelter_data'])}\n")
            if 'familiar_point_data' in result:
                f.write(f"熟悉点数量: {len(result['familiar_point_data'])}\n")
            f.write(f"新的社区边界框: {result['boundary_data'].total_bounds}\n")
            f.write(f"新的建筑物边界框: {result['buildings_data'].total_bounds}\n")
            if 'stairwell_data' in result:
                f.write(f"新的楼梯间边界框: {result['stairwell_data'].total_bounds}\n")
            if 'shelter_data' in result:
                f.write(f"新的避难所边界框: {result['shelter_data'].total_bounds}\n")
            if 'familiar_point_data' in result:
                f.write(f"新的熟悉点边界框: {result['familiar_point_data'].total_bounds}\n")
        
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
    
    # 创建示例楼梯间
    stairwells = [
        Polygon([(120, 120), (140, 120), (140, 140), (120, 140)]),
        Polygon([(320, 170), (340, 170), (340, 190), (320, 190)]),
        Polygon([(520, 320), (540, 320), (540, 340), (520, 340)])
    ]
    stairwell_gdf = gpd.GeoDataFrame(geometry=stairwells, crs='EPSG:4326')
    
    # 创建示例避难所
    shelters = [
        Polygon([(50, 50), (150, 50), (150, 150), (50, 150)]),
        Polygon([(600, 500), (750, 500), (750, 650), (600, 650)])
    ]
    shelter_gdf = gpd.GeoDataFrame(geometry=shelters, crs='EPSG:4326')
    
    # 创建示例熟悉点
    familiar_points = [
        Point(150, 150),
        Point(350, 200),
        Point(550, 350),
        Point(750, 250),
        Point(200, 550),
        Point(450, 450),
        Point(80, 300)
    ]
    familiar_point_gdf = gpd.GeoDataFrame(geometry=familiar_points, crs='EPSG:4326')
    
    return boundary_gdf, buildings_gdf, stairwell_gdf, shelter_gdf, familiar_point_gdf

def main():
    """主函数 - 演示使用方法"""
    print("社区建筑物坐标转换工具")
    print("=" * 60)
    
    # 创建转换器
    transformer = CommunityBuildingTransformer(target_crs='EPSG:3415')
    
    # 创建示例数据
    print("创建示例数据...")
    boundary_gdf, buildings_gdf, stairwell_gdf, shelter_gdf, familiar_point_gdf = create_sample_data()
    
    # 保存示例数据
    os.makedirs('sample_data', exist_ok=True)
    boundary_gdf.to_file('sample_data/sample_boundary.shp')
    buildings_gdf.to_file('sample_data/sample_buildings.shp')
    stairwell_gdf.to_file('sample_data/sample_stairwell.geojson', driver='GeoJSON')
    shelter_gdf.to_file('sample_data/sample_shelter_available.geojson', driver='GeoJSON')
    familiar_point_gdf.to_file('sample_data/sample_familiar_point.geojson', driver='GeoJSON')
    print("示例数据已保存到 sample_data/ 目录")
    
    # 执行转换
    result = transformer.process_community_data(
        'sample_data/sample_boundary.shp',
        'sample_data/sample_buildings.shp', 
        'sample_data/sample_stairwell.geojson',
        'sample_data/sample_shelter_available.geojson',
        'sample_data/sample_familiar_point.geojson'
    )
    
    # 保存结果
    transformer.save_transformed_data(result, 'output')
    
    print("\n转换完成！")
    return result

if __name__ == "__main__":
    main() 