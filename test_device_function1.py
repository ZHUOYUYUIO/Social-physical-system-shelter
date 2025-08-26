import math
import numpy as np
from pyflamegpu import *
import pyflamegpu.codegen


class write_env_hostfn(pyflamegpu.HostFunction):
  
  def __init__(self):
    super().__init__()  
  
  def run(self,FLAMEGPU):

      # Retrieve the environment macro property bar of type int array[5][5]

      # Update some of the values
      # foo = 12.0; is not allowed
      FLAMEGPU.environment.importMacroProperty("obstacle1", "obstacle1.json");
      FLAMEGPU.environment.importMacroProperty("obstacle2", "obstacle2.json");
      FLAMEGPU.environment.importMacroProperty("obstacle3", "obstacle3.json");

model = pyflamegpu.ModelDescription("F_MAP_tutorial1")

env = model.Environment()
env.newMacroPropertyInt("obstacle1", 2, 4)  
env.newMacroPropertyInt("obstacle2", 2, 6)
env.newMacroPropertyInt("obstacle3", 2, 6) 

# Define an agent named point
agent = model.newAgent("point")
# Assign the agent some variables (ID is implicit to agents, so we don't define it ourselves)
agent.newVariableFloat("x")
agent.newVariableFloat("y")
agent.newVariableFloat("test_value") 
agent.newVariableArrayFloat("location", 10)  # 路径点数组，最大100个点

agent.newVariableFloat("drift", 0)


find_path_ultra_consolidated = r"""
FLAMEGPU_AGENT_FUNCTION(find_path_ultra_consolidated, flamegpu::MessageNone, flamegpu::MessageNone) {
    const float start_x = FLAMEGPU->getVariable<float>("x");
    const float start_y = FLAMEGPU->getVariable<float>("y");
    const float end_x = 8.0;
    const float end_y = 8.0;
    auto obstacle1 = FLAMEGPU->environment.getMacroProperty<int, 2,4>("obstacle1");
    auto obstacle2 = FLAMEGPU->environment.getMacroProperty<int, 2,6>("obstacle2");
    auto obstacle3 = FLAMEGPU->environment.getMacroProperty<int, 2,6>("obstacle3");

    obstacles = [obstacle1, obstacle2, obstacle3]
    // =================================================================
    // 1. 处理起点在障碍物内部的情况
    // =================================================================
    float actual_start_x = start_x;
    float actual_start_y = start_y;
    int inside_obstacle_index = -1;
    
    // 检查起点是否在任何障碍物内部
    for (int obs_idx = 0; obs_idx < obstacles.size(); obs_idx++) {
        const auto& obstacle = obstacles[obs_idx];
        
        // 使用射线法判断点是否在多边形内部
        float x = start_x, y = start_y;
        int n = obstacle.size();
        bool inside = false;
        
        float p1x = obstacle[0][0];
        float p1y = obstacle[0][1];
        
        for (int i = 1; i <= n; i++) {
            float p2x = obstacle[i % n][0];
            float p2y = obstacle[i % n][1];
            
            if (y > std::min(p1y, p2y)) {
                if (y <= std::max(p1y, p2y)) {
                    if (x <= std::max(p1x, p2x)) {
                        if (p1y != p2y) {
                            float xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x;
                            if (p1x == p2x || x <= xinters) {
                                inside = !inside;
                            }
                        }
                    }
                }
            }
            p1x = p2x;
            p1y = p2y;
        }
        
        if (inside) {
            inside_obstacle_index = obs_idx;
            break;
        }
    }
    
    // 如果起点在障碍物内部，找到最近的出口点
    if (inside_obstacle_index != -1) {
        const auto& inside_obstacle = obstacles[inside_obstacle_index];
        float min_distance = std::numeric_limits<float>::infinity();
        float best_exit_x = start_x;
        float best_exit_y = start_y;
        
        int n = inside_obstacle.size();
        for (int i = 0; i < n; i++) {
            float x1 = inside_obstacle[i][0];
            float y1 = inside_obstacle[i][1];
            float x2 = inside_obstacle[(i + 1) % n][0];
            float y2 = inside_obstacle[(i + 1) % n][1];
            
            // 计算点到线段的最短距离和投影点
            float x = start_x, y = start_y;
            float line_len_sq = (x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1);
            float exit_x, exit_y;
            
            if (line_len_sq == 0) {
                exit_x = x1;
                exit_y = y1;
            } else {
                float t = std::max(0.0f, std::min(1.0f, ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / line_len_sq));
                exit_x = x1 + t * (x2 - x1);
                exit_y = y1 + t * (y2 - y1);
            }
            
            float dist = std::sqrt((start_x - exit_x) * (start_x - exit_x) + (start_y - exit_y) * (start_y - exit_y));
            
            if (dist < min_distance) {
                min_distance = dist;
                
                // 计算边的法向量（向外）
                float edge_x = x2 - x1;
                float edge_y = y2 - y1;
                // 逆时针旋转90度得到外法向量
                float normal_x = -edge_y;
                float normal_y = edge_x;
                float normal_len = std::sqrt(normal_x * normal_x + normal_y * normal_y);
                
                if (normal_len > 0) {
                    normal_x /= normal_len;
                    normal_y /= normal_len;
                    
                    // 检查法向量方向是否正确（应该指向多边形外部）
                    float test_x = exit_x + normal_x * 0.1f;
                    float test_y = exit_y + normal_y * 0.1f;
                    
                    // 检查测试点是否在多边形内
                    bool inside_test = false;
                    float p1x = inside_obstacle[0][0];
                    float p1y = inside_obstacle[0][1];
                    for (int j = 1; j <= n; j++) {
                        float p2x = inside_obstacle[j % n][0];
                        float p2y = inside_obstacle[j % n][1];
                        if (test_y > std::min(p1y, p2y)) {
                            if (test_y <= std::max(p1y, p2y)) {
                                if (test_x <= std::max(p1x, p2x)) {
                                    if (p1y != p2y) {
                                        float xinters = (test_y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x;
                                        if (p1x == p2x || test_x <= xinters) {
                                            inside_test = !inside_test;
                                        }
                                    }
                                }
                            }
                        }
                        p1x = p2x;
                        p1y = p2y;
                    }
                    
                    if (inside_test) {
                        // 如果测试点还在多边形内，说明法向量方向错误，需要反向
                        normal_x = -normal_x;
                        normal_y = -normal_y;
                    }
                    
                    // 沿法向量向外移动
                    best_exit_x = exit_x + normal_x * 0.5f;
                    best_exit_y = exit_y + normal_y * 0.5f;
                } else {
                    // 如果无法计算法向量，使用原来的方法
                    float direction_x = exit_x - start_x;
                    float direction_y = exit_y - start_y;
                    float dir_len = std::sqrt(direction_x * direction_x + direction_y * direction_y);
                    if (dir_len > 0) {
                        direction_x /= dir_len;
                        direction_y /= dir_len;
                        best_exit_x = exit_x + direction_x * 0.5f;
                        best_exit_y = exit_y + direction_y * 0.5f;
                    } else {
                        best_exit_x = exit_x;
                        best_exit_y = exit_y;
                    }
                }
            }
        }
        
        actual_start_x = best_exit_x;
        actual_start_y = best_exit_y;
    }
    
    // =================================================================
    // 2. 检查是否可以直接到达终点
    // =================================================================
    bool can_go_direct = true;
    for (const auto& obstacle : obstacles) {
        int n = obstacle.size();
        
        // 检查端点是否在多边形内
        float x = actual_start_x, y = actual_start_y;
        bool inside_start = false;
        float p1x = obstacle[0][0];
        float p1y = obstacle[0][1];
        for (int i = 1; i <= n; i++) {
            float p2x = obstacle[i % n][0];
            float p2y = obstacle[i % n][1];
            if (y > std::min(p1y, p2y)) {
                if (y <= std::max(p1y, p2y)) {
                    if (x <= std::max(p1x, p2x)) {
                        if (p1y != p2y) {
                            float xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x;
                            if (p1x == p2x || x <= xinters) {
                                inside_start = !inside_start;
                            }
                        }
                    }
                }
            }
            p1x = p2x;
            p1y = p2y;
        }
        
        x = end_x, y = end_y;
        bool inside_end = false;
        p1x = obstacle[0][0];
        p1y = obstacle[0][1];
        for (int i = 1; i <= n; i++) {
            float p2x = obstacle[i % n][0];
            float p2y = obstacle[i % n][1];
            if (y > std::min(p1y, p2y)) {
                if (y <= std::max(p1y, p2y)) {
                    if (x <= std::max(p1x, p2x)) {
                        if (p1y != p2y) {
                            float xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x;
                            if (p1x == p2x || x <= xinters) {
                                inside_end = !inside_end;
                            }
                        }
                    }
                }
            }
            p1x = p2x;
            p1y = p2y;
        }
        
        if (inside_start || inside_end) {
            can_go_direct = false;
            break;
        }
        
        // 检查线段是否与多边形的任何边相交
        for (int i = 0; i < n; i++) {
            float x1 = actual_start_x, y1 = actual_start_y;
            float x2 = end_x, y2 = end_y;
            float x3 = obstacle[i][0], y3 = obstacle[i][1];
            float x4 = obstacle[(i + 1) % n][0], y4 = obstacle[(i + 1) % n][1];
            
            float denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
            
            if (std::abs(denom) < 1e-10f) {
                continue;
            }
            
            float t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom;
            float u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom;
            
            if (0 <= t && t <= 1 && 0 <= u && u <= 1) {
                can_go_direct = false;
                break;
            }
        }
        
        if (!can_go_direct) {
            break;
        }
    }
    
    // 如果可以直接到达，返回直线路径
    if (can_go_direct) {
        std::vector<float> float_array;
        if (actual_start_x == start_x && actual_start_y == start_y) {
            float_array = {start_x, start_y, end_x, end_y};
        } else {
            float_array = {start_x, start_y, actual_start_x, actual_start_y, end_x, end_y};
        }
        return float_array;
    }
    
    // =================================================================
    // 3. 收集所有关键点（起点、终点、障碍物扩展顶点）
    // =================================================================
    std::vector<float> waypoints_x = {actual_start_x, end_x};
    std::vector<float> waypoints_y = {actual_start_y, end_y};
    
    for (const auto& obstacle : obstacles) {
        int n = obstacle.size();
        
        // 对于矩形障碍物，使用简单的向外扩展
        if (n == 4) {
            // 计算边界框
            float min_x = obstacle[0][0], max_x = obstacle[0][0];
            float min_y = obstacle[0][1], max_y = obstacle[0][1];
            
            for (const auto& vertex : obstacle) {
                min_x = std::min(min_x, vertex[0]);
                max_x = std::max(max_x, vertex[0]);
                min_y = std::min(min_y, vertex[1]);
                max_y = std::max(max_y, vertex[1]);
            }
            
            // 向外扩展
            waypoints_x.push_back(min_x - 1.0f);  // 左下
            waypoints_y.push_back(min_y - 1.0f);
            waypoints_x.push_back(max_x + 1.0f);  // 右下
            waypoints_y.push_back(min_y - 1.0f);
            waypoints_x.push_back(max_x + 1.0f);  // 右上
            waypoints_y.push_back(max_y + 1.0f);
            waypoints_x.push_back(min_x - 1.0f);  // 左上
            waypoints_y.push_back(max_y + 1.0f);
        } else {
            // 对于其他多边形，使用角平分线方法
            float margin = 1.0f;
            
            for (int i = 0; i < n; i++) {
                float prev_x = obstacle[(i - 1 + n) % n][0];
                float prev_y = obstacle[(i - 1 + n) % n][1];
                float curr_x = obstacle[i][0];
                float curr_y = obstacle[i][1];
                float next_x = obstacle[(i + 1) % n][0];
                float next_y = obstacle[(i + 1) % n][1];
                
                float v1x = prev_x - curr_x;
                float v1y = prev_y - curr_y;
                float v2x = next_x - curr_x;
                float v2y = next_y - curr_y;
                
                float len1 = std::sqrt(v1x * v1x + v1y * v1y);
                float len2 = std::sqrt(v2x * v2x + v2y * v2y);
                
                if (len1 > 0) {
                    v1x /= len1;
                    v1y /= len1;
                }
                if (len2 > 0) {
                    v2x /= len2;
                    v2y /= len2;
                }
                
                float bisector_x = v1x + v2x;
                float bisector_y = v1y + v2y;
                float bisector_len = std::sqrt(bisector_x * bisector_x + bisector_y * bisector_y);
                
                if (bisector_len > 0) {
                    bisector_x /= bisector_len;
                    bisector_y /= bisector_len;
                    float extended_x = curr_x + bisector_x * margin;
                    float extended_y = curr_y + bisector_y * margin;
                    waypoints_x.push_back(extended_x);
                    waypoints_y.push_back(extended_y);
                } else {
                    float perp_x = -v1y;
                    float perp_y = v1x;
                    float extended_x = curr_x + perp_x * margin;
                    float extended_y = curr_y + perp_y * margin;
                    waypoints_x.push_back(extended_x);
                    waypoints_y.push_back(extended_y);
                }
            }
        }
    }
    
    // =================================================================
    // 4. 建立连接图
    // =================================================================
    std::vector<std::vector<int>> connections(waypoints_x.size());
    int n = waypoints_x.size();
    
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if (i != j) {
                // 检查两点之间是否可以直接连接
                bool can_connect = true;
                for (const auto& obstacle : obstacles) {
                    int n_poly = obstacle.size();
                    
                    // 检查端点是否在多边形内
                    float x = waypoints_x[i], y = waypoints_y[i];
                    bool inside_i = false;
                    float p1x = obstacle[0][0];
                    float p1y = obstacle[0][1];
                    for (int k = 1; k <= n_poly; k++) {
                        float p2x = obstacle[k % n_poly][0];
                        float p2y = obstacle[k % n_poly][1];
                        if (y > std::min(p1y, p2y)) {
                            if (y <= std::max(p1y, p2y)) {
                                if (x <= std::max(p1x, p2x)) {
                                    if (p1y != p2y) {
                                        float xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x;
                                        if (p1x == p2x || x <= xinters) {
                                            inside_i = !inside_i;
                                        }
                                    }
                                }
                            }
                        }
                        p1x = p2x;
                        p1y = p2y;
                    }
                    
                    x = waypoints_x[j], y = waypoints_y[j];
                    bool inside_j = false;
                    p1x = obstacle[0][0];
                    p1y = obstacle[0][1];
                    for (int k = 1; k <= n_poly; k++) {
                        float p2x = obstacle[k % n_poly][0];
                        float p2y = obstacle[k % n_poly][1];
                        if (y > std::min(p1y, p2y)) {
                            if (y <= std::max(p1y, p2y)) {
                                if (x <= std::max(p1x, p2x)) {
                                    if (p1y != p2y) {
                                        float xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x;
                                        if (p1x == p2x || x <= xinters) {
                                            inside_j = !inside_j;
                                        }
                                    }
                                }
                            }
                        }
                        p1x = p2x;
                        p1y = p2y;
                    }
                    
                    if (inside_i || inside_j) {
                        can_connect = false;
                        break;
                    }
                    
                    // 检查线段是否与多边形的任何边相交
                    for (int k = 0; k < n_poly; k++) {
                        float x1 = waypoints_x[i], y1 = waypoints_y[i];
                        float x2 = waypoints_x[j], y2 = waypoints_y[j];
                        float x3 = obstacle[k][0], y3 = obstacle[k][1];
                        float x4 = obstacle[(k + 1) % n_poly][0], y4 = obstacle[(k + 1) % n_poly][1];
                        
                        float denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
                        
                        if (std::abs(denom) < 1e-10f) {
                            continue;
                        }
                        
                        float t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom;
                        float u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom;
                        
                        if (0 <= t && t <= 1 && 0 <= u && u <= 1) {
                            can_connect = false;
                            break;
                        }
                    }
                    
                    if (!can_connect) {
                        break;
                    }
                }
                
                if (can_connect) {
                    connections[i].push_back(j);
                }
            }
        }
    }
    
    // =================================================================
    // 5. 使用Dijkstra算法找最短路径并重建路径
    // =================================================================
    std::vector<float> distances(n, std::numeric_limits<float>::infinity());
    distances[0] = 0;
    std::vector<int> previous(n, -1);
    std::set<int> unvisited;
    
    for (int i = 0; i < n; i++) {
        unvisited.insert(i);
    }
    
    while (!unvisited.empty()) {
        // 找到距离最小的未访问节点
        int current = -1;
        float min_dist = std::numeric_limits<float>::infinity();
        for (int node : unvisited) {
            if (distances[node] < min_dist) {
                min_dist = distances[node];
                current = node;
            }
        }
        
        if (current == -1) break;
        
        unvisited.erase(current);
        
        if (current == 1) {  // 到达终点
            break;
        }
        
        for (int neighbor : connections[current]) {
            if (unvisited.find(neighbor) != unvisited.end()) {
                // 计算距离
                float dx = waypoints_x[current] - waypoints_x[neighbor];
                float dy = waypoints_y[current] - waypoints_y[neighbor];
                float dist = std::sqrt(dx * dx + dy * dy);
                float new_distance = distances[current] + dist;
                
                if (new_distance < distances[neighbor]) {
                    distances[neighbor] = new_distance;
                    previous[neighbor] = current;
                }
            }
        }
    }
    
    // 重建路径
    if (previous[1] == -1) {
        return std::vector<float>();  // 无法到达
    }
    
    std::vector<float> path_x;
    std::vector<float> path_y;
    int current = 1;
    while (current != -1) {
        path_x.push_back(waypoints_x[current]);
        path_y.push_back(waypoints_y[current]);
        current = previous[current];
    }
    
    std::reverse(path_x.begin(), path_x.end());
    std::reverse(path_y.begin(), path_y.end());
    
    // =================================================================
    // 6. 路径后处理
    // =================================================================
    // 如果实际起点不是原始起点，在路径前面加上原始起点
    if (actual_start_x != start_x || actual_start_y != start_y) {
        path_x.insert(path_x.begin(), start_x);
        path_y.insert(path_y.begin(), start_y);
    }
    
    // 转换为float数组格式
    std::vector<float> float_array;
    for (int i = 0; i < path_x.size(); i++) {
        float_array.push_back(path_x[i]);
        float_array.push_back(path_y[i]);
    }
    // 将路径点数组存储到agent的location变量中
    int path_length = float_array.size();
    
    // 首先设置数组长度
    FLAMEGPU->setVariable<int>("location", 0, path_length);
    
    // 然后依次将数组中的值存储到location变量中
    for (int i = 0; i < path_length; i++) {
        FLAMEGPU->setVariable<float>("location", i + 1, float_array[i]);
    }
    
}

"""

# 对于C++格式的函数，直接使用RTCFunction
find_path_ultra_consolidated_fn = agent.newRTCFunction("find_path_ultra_consolidated", find_path_ultra_consolidated)
model.addExecutionRoot(find_path_ultra_consolidated_fn)
model.generateLayers()


# Specify the desired StepLoggingConfig
step_log_cfg = pyflamegpu.StepLoggingConfig(model)
# Log every step
step_log_cfg.setFrequency(1)
# Include the mean of the "point" agent population's variable 'drift'
step_log_cfg.agent("point").logMeanFloat("drift")

# Create and init the simulation
cuda_model = pyflamegpu.CUDASimulation(model)

import random
import sys

AGENT_COUNT=3
ENV_WIDTH=10
AgentPopulation = pyflamegpu.AgentVector(model.Agent("point"), AGENT_COUNT)
for i in range(AGENT_COUNT):
    agent = AgentPopulation[i]
    agent.setVariableFloat("x", random.uniform(0, ENV_WIDTH))
    agent.setVariableFloat("y", random.uniform(0, ENV_WIDTH))


cuda_model.initialise(sys.argv)

# Attach the logging config
cuda_model.setStepLog(step_log_cfg)

# Run the simulation
cuda_model.simulate()

out_pop = pyflamegpu.AgentVector(model.Agent("point"))
cuda_model.getPopulationData(out_pop)
for agent in out_pop:
    print("Agent location array length: %d" % agent.getVariableArrayFloat("location")[0])
    print("Agent location values: %s" % str(agent.getVariableArrayFloat("location")[1:]))