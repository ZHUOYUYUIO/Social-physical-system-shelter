#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visualization Demo Script
Demonstrate population scatter visualization effects for different floors
"""

import os
import json
import pandas as pd
from collections import Counter

def show_visualization_info():
    """Display visualization file information"""
    
    print("🎨 Population Scatter Visualization in Buildings")
    print("=" * 50)
    
    # Check generated visualization files
    visualization_files = [
            'data/output/population_visualization.png',
    'data/output/building_population_3d.png',
    'data/output/building_population_interactive.html'
    ]
    
    print("📊 Generated visualization files:")
    for file_path in visualization_files:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            print(f"  ✓ {file_path}")
            print(f"    Size: {file_size:.1f} MB")
        else:
            print(f"  ✗ {file_path} (file not found)")
    
    print("\n📈 Visualization features:")
    print("1. population_visualization.png")
    print("   - 2D plan view, different floors shown in different colors")
    print("   - Left: scatter distribution, Right: floor population statistics bar chart")
    print("   - Uses viridis color mapping, higher floors in darker colors")
    
    print("\n2. building_population_3d.png")
    print("   - 3D view, Z-axis represents floor height")
    print("   - Clearly shows population distribution across different floors")
    print("   - Building outlines shown as base plane")
    
    print("\n3. building_population_interactive.html")
    print("   - Interactive HTML file, can be opened in browser")
    print("   - Supports mouse hover for detailed information")
    print("   - Can zoom, pan, and select specific floors to display")
    
    # Display floor distribution statistics
    print("\n📋 Floor distribution statistics:")
    try:
        with open('data/output/population_points.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        agents = data['agents']['prey']['states']['default']['agents']
        floors = [agent['variables']['floor'] for agent in agents]
        
        floor_counts = Counter(floors)
        print(f"Total population: {len(agents)}")
        print(f"Floor range: {min(floors)} - {max(floors)}")
        print("\nPopulation distribution by floor:")
        for floor in sorted(floor_counts.keys()):
            count = floor_counts[floor]
            percentage = (count / len(agents)) * 100
            print(f"  Floor {floor}: {count} people ({percentage:.1f}%)")
            
    except Exception as e:
        print(f"Failed to read data: {e}")
    
    print("\n🎯 Usage suggestions:")
    print("- View 2D chart to understand overall distribution")
    print("- View 3D chart to understand floor height distribution")
    print("- Open HTML file for interactive exploration")
    print("- All scatter points contain floor information for FlameGPU simulation")

def show_color_mapping():
    """Display color mapping information"""
    
    print("\n🎨 Color mapping information:")
    print("=" * 30)
    print("Floor colors use viridis color mapping:")
    print("- Lower floors: Blue-green")
    print("- Middle floors: Yellow")
    print("- Higher floors: Red")
    print("- Smooth color gradient for easy floor distinction")
    
    print("\n📊 Visualization optimization features:")
    print("- Appropriate scatter point size for easy observation")
    print("- Transparency settings to avoid overlap occlusion")
    print("- White borders for enhanced contrast")
    print("- Legend shows population count for each floor")
    print("- Statistics box displays overall data")

if __name__ == "__main__":
    show_visualization_info()
    show_color_mapping()
    
    print("\n✅ Visualization optimization completed!")
    print("Now each scatter point displays different colors based on its floor information,")
    print("allowing intuitive visualization of population distribution across different floors in buildings.") 