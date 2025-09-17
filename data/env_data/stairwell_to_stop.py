import os
import json
from shapely.geometry import shape, mapping, Point, LineString, Polygon
from shapely.ops import nearest_points
import matplotlib.pyplot as plt

def load_geojson_features(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"GeoJSON文件不存在: {os.path.abspath(path)}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["features"]

def save_geojson_features(features, path, crs=None):
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    if crs:
        geojson["crs"] = crs
    with open(path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

def get_building_polygons(building_features):
    polygons = []
    for feat in building_features:
        geom = shape(feat["geometry"])
        if isinstance(geom, Polygon):
            polygons.append(geom)
        elif geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                polygons.append(poly)
    return polygons

def find_nearest_building(point, building_polygons):
    min_dist = float("inf")
    nearest_poly = None
    for poly in building_polygons:
        d = poly.exterior.distance(point)
        if d < min_dist:
            min_dist = d
            nearest_poly = poly
    return nearest_poly

def project_point_outside(point, polygon, extend_dist=5.0):
    # Find nearest point on polygon exterior
    nearest_on_poly = polygon.exterior.interpolate(polygon.exterior.project(point))
    # Direction vector from stairwell to nearest point on building edge
    dx = nearest_on_poly.x - point.x
    dy = nearest_on_poly.y - point.y
    norm = (dx**2 + dy**2) ** 0.5
    if norm == 0:
        # If the stairwell is exactly on the edge, use the normal of the edge
        # Find the nearest segment
        min_seg_dist = float("inf")
        out_vec = (1, 0)  # fallback
        coords = list(polygon.exterior.coords)
        for i in range(len(coords) - 1):
            seg = LineString([coords[i], coords[i+1]])
            proj = seg.project(point)
            nearest_on_seg = seg.interpolate(proj)
            d = point.distance(nearest_on_seg)
            if d < min_seg_dist:
                min_seg_dist = d
                # Get segment vector
                sx, sy = coords[i+1][0] - coords[i][0], coords[i+1][1] - coords[i][1]
                # Normal vector (perpendicular, outward)
                out_vec = (-sy, sx)
        norm2 = (out_vec[0]**2 + out_vec[1]**2) ** 0.5
        if norm2 == 0:
            out_vec = (1, 0)
            norm2 = 1
        dx, dy = out_vec[0]/norm2, out_vec[1]/norm2
    else:
        dx, dy = dx/norm, dy/norm
    # Move from nearest point on edge outward by extend_dist
    out_x = nearest_on_poly.x + dx * extend_dist
    out_y = nearest_on_poly.y + dy * extend_dist
    return out_x, out_y

def visualize(stairwell_features, building_polygons, outstop_points):
    fig, ax = plt.subplots(figsize=(10, 10))
    # Plot buildings
    for poly in building_polygons:
        x, y = poly.exterior.xy
        ax.fill(x, y, color="#cccccc", alpha=0.5, zorder=1, label="Building" if 'Building' not in ax.get_legend_handles_labels()[1] else "")
    # Plot stairwell points
    stairwell_x = []
    stairwell_y = []
    for feat in stairwell_features:
        geom = shape(feat["geometry"])
        if isinstance(geom, Point):
            stairwell_x.append(geom.x)
            stairwell_y.append(geom.y)
    ax.scatter(stairwell_x, stairwell_y, color="blue", s=40, label="Stairwell", zorder=2)
    # Plot outstop points
    out_x = [pt[0] for pt in outstop_points]
    out_y = [pt[1] for pt in outstop_points]
    ax.scatter(out_x, out_y, color="red", s=40, label="Outstop", zorder=3)
    # Draw lines from stairwell to outstop
    for sx, sy, ox, oy in zip(stairwell_x, stairwell_y, out_x, out_y):
        ax.plot([sx, ox], [sy, oy], color="green", linestyle="--", linewidth=1, zorder=2)
    ax.set_aspect("equal")
    ax.legend()
    ax.set_title("Stairwells, Outstop Points, and Buildings")
    plt.show()

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, "..", "output")
    stairwell_path = os.path.join(data_dir, "transformed_stairwell.geojson")
    building_path = os.path.join(data_dir, "transformed_buildings.geojson")
    output_path = os.path.join(data_dir, "stairwell.geojson")

    # 检查文件是否存在，给出更友好的报错
    if not os.path.exists(stairwell_path):
        print(f"找不到楼梯间GeoJSON文件: {os.path.abspath(stairwell_path)}")
        print("请确认文件路径和文件名是否正确。")
        return
    if not os.path.exists(building_path):
        print(f"找不到建筑物GeoJSON文件: {os.path.abspath(building_path)}")
        print("请确认文件路径和文件名是否正确。")
        return

    stairwell_features = load_geojson_features(stairwell_path)
    building_features = load_geojson_features(building_path)
    building_polygons = get_building_polygons(building_features)

    new_features = []
    outstop_points = []
    for feat in stairwell_features:
        geom = shape(feat["geometry"])
        if not isinstance(geom, Point):
            # Only process Point stairwells
            continue
        # Find nearest building polygon
        nearest_poly = find_nearest_building(geom, building_polygons)
        if nearest_poly is None:
            # No building found, skip
            continue
        out_x, out_y = project_point_outside(geom, nearest_poly, extend_dist=5.0)
        outstop_points.append((out_x, out_y))
        # Add outstop_x, outstop_y to properties
        new_props = dict(feat.get("properties", {}))
        new_props["outstop_x"] = out_x
        new_props["outstop_y"] = out_y
        new_feat = {
            "type": "Feature",
            "geometry": mapping(geom),
            "properties": new_props
        }
        new_features.append(new_feat)

    # Save new geojson
    save_geojson_features(new_features, output_path)

    # Visualization
    visualize(stairwell_features, building_polygons, outstop_points)

if __name__ == "__main__":
    main()


