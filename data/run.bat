@echo off
chcp 65001 >nul
echo 社区建筑物坐标转换工具
echo ================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.7或更高版本
    pause
    exit /b 1
)

REM 检查依赖包是否安装
echo 检查依赖包...
python -c "import geopandas, shapely, pyproj" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误：依赖包安装失败
        pause
        exit /b 1
    )
)

REM 创建必要的目录
if not exist "data" mkdir data
if not exist "output" mkdir output

echo.
echo 请确保以下文件已放置在正确位置：
echo - data\boundary.shp    (社区边界文件)
echo - data\buildings.shp   (建筑物文件)
echo.

REM 检查输入文件
if not exist "data\boundary.shp" (
    echo 警告：未找到 data\boundary.shp
    echo 请将社区边界文件重命名为 boundary.shp 并放入 data 目录
    echo.
)

if not exist "data\buildings.shp" (
    echo 警告：未找到 data\buildings.shp
    echo 请将建筑物文件重命名为 buildings.shp 并放入 data 目录
    echo.
)

if not exist "data\boundary.shp" (
    echo 是否要运行示例程序？(y/n)
    set /p choice=
    if /i "%choice%"=="y" (
        echo 运行示例程序...
        python community_building_transformer.py
    ) else (
        echo 请准备好输入文件后重新运行此脚本
        pause
        exit /b 1
    )
) else (
    echo 开始转换...
    python run_transformation.py
)

echo.
echo 处理完成！
echo 输出文件保存在 output 目录下
echo.
pause 