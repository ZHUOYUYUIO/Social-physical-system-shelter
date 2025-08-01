# SHELTER_FLAMEGPU2 - 建筑物内人口散点生成工具

## 📋 项目概述

这是一个完整的建筑物内人口散点生成工具，支持从地理数据到FlameGPU模拟的完整工作流程。主要功能包括：

- 🔄 **坐标转换**：将地理坐标转换为EPSG:3415坐标系
- 🏢 **建筑物处理**：支持建筑物楼层信息添加
- 👥 **人口散点生成**：在建筑物内生成带楼层信息的人口散点
- 🎨 **可视化**：多种可视化方式展示人口分布
- 🔧 **FlameGPU集成**：生成可直接用于FlameGPU模拟的代码

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt
```

### 2. 准备数据文件

将以下文件放在项目根目录：
- `boundary.geojson` - 社区边界数据
- `buildings.geojson` - 建筑物数据

### 3. 运行完整工作流程

```bash
# 一键运行完整流程
python complete_workflow.py
```

## 📁 项目结构

```
SHELTER_FLAMEGPU2/
├── 📄 核心脚本 (4个)
│   ├── complete_workflow.py              # 完整工作流程
│   ├── community_building_transformer.py # 坐标转换工具
│   ├── generate_population_points.py     # 散点生成器
│   └── generate_flamegpu_code.py         # FlameGPU代码生成器
├── 📊 数据文件 (2个)
│   ├── boundary.geojson                  # 社区边界
│   └── buildings.geojson                 # 建筑物数据
├── 📈 工具脚本 (3个)
│   ├── visualization_demo.py             # 可视化演示
│   ├── check_floor_distribution.py       # 楼层分布检查
│   └── test_all_functions.py             # 功能测试
├── 📂 输出目录 (11个文件)
│   ├── 数据文件 (4个)
│   │   ├── population_points.json        # FlameGPU格式数据
│   │   ├── population_points.csv         # CSV格式数据
│   │   ├── population_points.geojson     # GeoJSON格式数据
│   │   └── transformation_info.txt       # 转换信息
│   ├── 可视化文件 (3个)
│   │   ├── population_visualization.png  # 2D可视化
│   │   ├── building_population_3d.png    # 3D可视化
│   │   └── building_population_interactive.html # 交互式可视化
│   ├── FlameGPU代码 (2个)
│   │   ├── flamegpu_init_code.py         # 基于散点数据
│   │   └── flamegpu_init_code_random.py  # 随机分布版本
│   └── 转换结果 (2个)
│       ├── transformed_buildings.geojson # 转换后的建筑物
│       └── transformed_boundary.geojson  # 转换后的边界
├── 📖 文档文件 (4个)
│   ├── README.md                         # 项目说明
│   ├── 使用说明.md                       # 详细使用指南
│   ├── 项目总结.md                       # 项目总结
│   └── 项目精简说明.md                   # 精简说明
├── ⚙️ 配置文件 (2个)
│   ├── requirements.txt                  # 依赖列表
│   └── run.bat                          # Windows批处理脚本
└── 📁 其他目录
    ├── __pycache__/                      # Python缓存
    └── sample_data/                      # 示例数据
```

## 🔧 主要功能

### 1. 坐标转换 (`community_building_transformer.py`)

- 自动检测坐标系
- 转换为EPSG:3415坐标系
- 设置原点为左下角(0,0)
- 支持多种输入格式

```bash
python community_building_transformer.py
```

### 2. 散点生成 (`generate_population_points.py`)

- 在建筑物内生成随机散点
- 为每个散点分配楼层信息
- 支持人口密度参数调整
- 多种输出格式

```bash
python generate_population_points.py
```

### 3. 可视化功能

#### 2D可视化
- 按楼层着色的散点图
- 楼层人口统计柱状图
- 建筑物轮廓显示

#### 3D可视化
- 立体楼层分布图
- Z轴表示楼层高度
- 建筑物底面轮廓

#### 交互式可视化
- HTML格式，支持浏览器交互
- 鼠标悬停查看详细信息
- 可缩放、平移、筛选

### 4. FlameGPU集成

生成可直接用于FlameGPU的初始化代码：

```python
# 使用生成的代码初始化FlameGPU模型
from flamegpu import *

model = pyflamegpu.ModelDescription("Population Model")
prey = model.newAgent("prey")
prey.newVariableFloat("x")
prey.newVariableFloat("y")
prey.newVariableInt("building_id")
prey.newVariableInt("point_id")
prey.newVariableInt("floor")

# 使用生成的初始化函数
init_population = model.newAgentFunction("init_population")
init_population.setFunction(initialize_prey_population)
```

## 📊 输出文件说明

### 坐标转换结果
- `transformed_boundary.shp` - 转换后的边界数据
- `transformed_buildings.shp` - 转换后的建筑物数据
- `transformation_info.txt` - 转换信息记录

### 散点数据
- `population_points.json` - FlameGPU格式数据
- `population_points.csv` - CSV格式数据
- `population_points.geojson` - GeoJSON格式数据

### 可视化文件
- `population_visualization.png` - 2D可视化图
- `building_population_3d.png` - 3D可视化图
- `building_population_interactive.html` - 交互式可视化

### FlameGPU代码
- `flamegpu_init_code.py` - 基于散点数据的初始化代码
- `flamegpu_init_code_random.py` - 随机分布版本

## ⚙️ 参数配置

### 人口生成参数
- `base_population`: 每层基础人口数 (默认: 50)
- `variance`: 人口变化幅度 (默认: 0.3)

### 楼层设置
- 支持自定义楼层范围
- 自动随机分配楼层信息
- 楼层验证和统计

## 🎨 可视化特性

### 颜色映射
- 使用viridis颜色映射
- 低楼层：蓝绿色
- 高楼层：红色
- 平滑渐变便于区分

### 交互功能
- 鼠标悬停显示详细信息
- 支持图层显示/隐藏
- 缩放和平移操作
- 楼层筛选功能

## 📈 数据统计

项目提供详细的数据统计功能：

- 建筑物数量和分布
- 各楼层人口统计
- 散点分布分析
- 楼层验证检查

## 🔍 使用示例

### 完整工作流程
```bash
# 运行完整流程
python complete_workflow.py

# 查看可视化效果
python visualization_demo.py

# 检查楼层分布
python check_floor_distribution.py
```

### 单独运行各模块
```bash
# 坐标转换
python community_building_transformer.py

# 散点生成
python generate_population_points.py

# FlameGPU代码生成
python generate_flamegpu_code.py
```

## 📋 依赖要求

```
geopandas>=0.12.0
pandas>=1.5.0
shapely>=1.8.0
pyproj>=3.4.0
numpy>=1.21.0
matplotlib>=3.5.0
plotly>=5.0.0
```

## 🎯 应用场景

- 🏢 建筑物疏散模拟
- 🚨 应急响应规划
- 📊 人口分布分析
- 🎮 游戏场景生成
- 🔬 社会科学研究

## 📞 技术支持

如有问题或建议，请查看：
- `使用说明.md` - 详细使用指南
- `example_usage.py` - 使用示例
- `example_with_geojson.py` - GeoJSON数据示例

## ✅ 测试结果

项目已通过完整测试：
- ✅ 坐标转换功能正常
- ✅ 散点生成功能正常
- ✅ 可视化功能正常
- ✅ FlameGPU代码生成正常
- ✅ 楼层信息分配正确
- ✅ 多种输出格式支持

---

**版本**: 2.0  
**更新时间**: 2024年  
**许可证**: MIT # population_crs_transfer
