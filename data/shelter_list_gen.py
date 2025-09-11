import os
import json
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon

def generate_standardized_points(boundary_gdf, step=10):
    """生成以step为间隔的标准化点集，覆盖边界"""
    minx, miny, maxx, maxy = boundary_gdf.total_bounds
    points = []
    for x in range(int(minx), int(maxx)+1, step):
        for y in range(int(miny), int(maxy)+1, step):
            pt = Point(x, y)
            if boundary_gdf.contains(pt).any():
                points.append({'x': x, 'y': y, 'geometry': pt})
    return pd.DataFrame(points)

def filter_points_in_shelters(points_df, shelter_gdf):
    """筛选出位于shelter可用框内的点"""
    # shelter_gdf每个geometry是Polygon
    mask = points_df['geometry'].apply(lambda pt: shelter_gdf.contains(pt).any())
    return points_df[mask].reset_index(drop=True)

def main():
    # 路径
    boundary_path = os.path.join(os.path.dirname(__file__), '../data/output/transformed_boundary.geojson')
    shelter_path = os.path.join(os.path.dirname(__file__), '../data/output/transformed_shelter_available.geojson')
    output_path = os.path.join(os.path.dirname(__file__), '../data/output/shelter_points.csv')

    # 读取边界
    boundary_gdf = gpd.read_file(boundary_path)
    # 生成标准化点集
    points_df = generate_standardized_points(boundary_gdf, step=20)

    # 读取可用shelter框
    shelter_gdf = gpd.read_file(shelter_path)
    # 筛选在shelter框内的点
    filtered_points = filter_points_in_shelters(points_df, shelter_gdf)

    # 排序并重建索引
    filtered_points = filtered_points.sort_values(['x', 'y']).reset_index(drop=True)
    filtered_points['index'] = filtered_points.index

    # 只保留x, y, index列
    result_df = filtered_points[['index', 'x', 'y']]

    # 输出为csv
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result_df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"✅ 已生成 shelter_points.csv，点数: {len(result_df)}，保存于: {output_path}")

if __name__ == "__main__":
    main()
