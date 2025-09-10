#!/usr/bin/env python
# coding: utf-8

# In[15]:





# In[16]:


import sys
import os

# 切换到你的项目根目录
project_root = r"D:\programming\python_script\socio-physical system for shelter"
os.chdir(project_root)

# 添加 data/output 目录到 Python 路径
sys.path.append('data/output')


# ## define model

# In[17]:


#这个test.py是用来测试pyflame的可视性的

from pyflamegpu import *
import pyflamegpu.codegen
import sys

# Define some useful constants



# Define the FLAME GPU model: 这个可以在后续的可视化窗口改名字
model = pyflamegpu.ModelDescription("First test using default visualization")


# ## messages setting

# In[18]:


# Define a message of type MessageSpatial2D named location
# MessageSpatial2D: Each agent outputs a message at a specific location in 2D space
# agents only read messages located close to a particular search origin（搜素的中心点）.
# 可以获取一定距离内的消息
message = model.newMessageSpatial3D("location")
# Configure the message list

message.setMin(0, 0,0)
message.setMax(500, 500,100)
message.setRadius(200)
# Add extra variables to the message
# X Y (Z) are implicit for spatial messages
message.newVariableID("id")



# In[19]:


stairwell_message = model.newMessageSpatial3D("stairwell_location")
# Configure the message list

stairwell_message.setMin(0, 0,0)
stairwell_message.setMax(500, 500,100)
stairwell_message.setRadius(200)
# Add extra variables to the message
# X Y (Z) are implicit for spatial messages
stairwell_message.newVariableID("id")
stairwell_message.newVariableInt("building_id")


# ## agent_variables_definition

# In[20]:


# Assign the agent some variables (ID is implicit to agents, so we don't define it ourselves)
student_agent = model.newAgent("student_agent")
student_agent.newVariableFloat("x")
student_agent.newVariableFloat("y")
student_agent.newVariableInt("building_id")
student_agent.newVariableInt("point_id")
student_agent.newVariableFloat("z")
student_agent.newVariableFloat("drift", 0)
student_agent.newVariableInt("target_stairwell_id", -1)
student_agent.newVariableFloat("target_stairwell_x")
student_agent.newVariableFloat("target_stairwell_y")


stairwell_agent = model.newAgent("stairwell_agent")
stairwell_agent.newVariableFloat("x")
stairwell_agent.newVariableFloat("y")
stairwell_agent.newVariableInt("stairwell_id")
stairwell_agent.newVariableInt("building_id")
stairwell_agent.newVariableFloat("z")



# ## environment setting

# In[21]:


# Define environment properties
env = model.Environment()
env.newPropertyUInt("AGENT_COUNT", 10000)
env.newPropertyFloat("ENV_WIDTH", 500)
env.newPropertyFloat("repulse", 0.05)


# ## agent function

# In[22]:


@pyflamegpu.agent_function
def stairwell_output_message(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageSpatial3D):
    message_out.setVariableUInt("id", pyflamegpu.getID())
    message_out.setVariableInt("building_id", pyflamegpu.getVariableInt("building_id"))
    message_out.setLocation(
        pyflamegpu.getVariableFloat("x"),
        pyflamegpu.getVariableFloat("y"),
        pyflamegpu.getVariableFloat("z")
        )
    return pyflamegpu.ALIVE


# In[23]:


@pyflamegpu.agent_function
def set_target_stairwell(message_in: pyflamegpu.MessageSpatial3D, message_out: pyflamegpu.MessageNone):
    # Get this agent's x, y, z variables
    x = pyflamegpu.getVariableFloat("x")
    y = pyflamegpu.getVariableFloat("y")
    z = pyflamegpu.getVariableFloat("z")
    target_stairwell_id = pyflamegpu.getVariableInt("target_stairwell_id")

    min_dist = 100000
    if target_stairwell_id == -1:
        for message in message_in(x,y,z):
            # Process the message's variables e.g.
            if message.getVariableInt("building_id") == pyflamegpu.getVariableInt("building_id"):
                #找到距离最近的楼梯
                # 找到距离最近的楼梯

                stairwell_x = message.getVariableFloat("x")
                stairwell_y = message.getVariableFloat("y")

                # 计算欧氏距离
                dx = stairwell_x - x
                dy = stairwell_y - y

                dist = math.sqrtf(dx*dx + dy*dy)
                if dist < min_dist:
                    min_dist = dist
                    nearest_stairwell_id = message.getVariableInt("id")
                    # 记录最近楼梯的坐标
                    pyflamegpu.setVariableInt("target_stairwell_id", nearest_stairwell_id)
                    pyflamegpu.setVariableFloat("target_stairwell_x", stairwell_x)
                    pyflamegpu.setVariableFloat("target_stairwell_y", stairwell_y)

            #设置目标楼梯
    return pyflamegpu.ALIVE


# In[ ]:


@pyflamegpu.agent_function
def move_to_stairwell(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageSpatial3D):
    target_stairwell_x = pyflamegpu.getVariableFloat("target_stairwell_x")
    target_stairwell_y = pyflamegpu.getVariableFloat("target_stairwell_y")
    x = pyflamegpu.getVariableFloat("x")
    y = pyflamegpu.getVariableFloat("y")
    # 计算目标点与当前位置的差值
    delta_x = target_stairwell_x - x
    delta_y = target_stairwell_y - y

    # 计算到目标的距离
    distance = math.sqrtf(delta_x * delta_x + delta_y * delta_y)

    # 如果距离大于1，则每次移动0.8单位长度
    if distance > 1.0:
        step_x = delta_x / distance 
        step_y = delta_y / distance 
        next_x = x + step_x
        next_y = y + step_y
    else:
        # 距离小于等于1，直接到达目标
        next_x = target_stairwell_x
        next_y = target_stairwell_y

    # 更新代理的新位置
    pyflamegpu.setVariableFloat("x", next_x)
    pyflamegpu.setVariableFloat("y", next_y)

    # 输出当前位置
    message_out.setLocation(next_x, next_y, pyflamegpu.getVariableFloat("z"))
    return pyflamegpu.ALIVE
    


# In[25]:


@pyflamegpu.agent_function
def output_message(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageSpatial3D):
    message_out.setVariableUInt("id", pyflamegpu.getID())
    message_out.setLocation(
        pyflamegpu.getVariableFloat("x"),
        pyflamegpu.getVariableFloat("y"),
        pyflamegpu.getVariableFloat("z")
        )
    return pyflamegpu.ALIVE


@pyflamegpu.agent_function
def input_message(message_in: pyflamegpu.MessageSpatial3D, message_out: pyflamegpu.MessageNone):
    ID = pyflamegpu.getID()
    REPULSE_FACTOR = pyflamegpu.environment.getPropertyFloat("repulse")
    RADIUS = message_in.radius()
    fx = 0.0
    fy = 0.0
    fz = 0.0
    x1 = pyflamegpu.getVariableFloat("x")
    y1 = pyflamegpu.getVariableFloat("y")
    z1 = pyflamegpu.getVariableFloat("z")
    count = 0 
    for message in message_in(x1, y1, z1):
        if message.getVariableUInt("id") != ID :
            x2 = message.getVariableFloat("x")
            y2 = message.getVariableFloat("y")
            z2 = message.getVariableFloat("z")
            x21 = x2 - x1
            y21 = y2 - y1
            z21 = z2 - y2
            separation = math.sqrtf(x21*x21 + y21*y21 + z21*z21)
            if separation < RADIUS and separation > 0 :
                k = math.sinf((separation / RADIUS)*3.141*-2)*REPULSE_FACTOR
                # Normalise without recalculating separation
                x21 /= separation
                y21 /= separation
                z21 /= separation
                fx += k * x21
                fy += k * y21
                fz += k* z21
                count += 1
    fx /= count if count > 0 else 1
    fy /= count if count > 0 else 1
    fz /= count if count > 0 else 1
    pyflamegpu.setVariableFloat("x", x1 + fx)
    pyflamegpu.setVariableFloat("y", y1 + fy)
    pyflamegpu.setVariableFloat("z", z1 + fz)

    pyflamegpu.setVariableFloat("drift", math.sqrtf(fx*fx + fy*fy + fz*fz))
    return pyflamegpu.ALIVE

# ## function write in

# In[26]:


# translate the agent functions from Python to C++
output_func_translated = pyflamegpu.codegen.translate(output_message)
stairwell_output_func_translated = pyflamegpu.codegen.translate(stairwell_output_message)
set_target_stairwell_func_translated = pyflamegpu.codegen.translate(set_target_stairwell)
move_to_stairwell_func_translated = pyflamegpu.codegen.translate(move_to_stairwell)

# Setup the two agent functions
out_fn = student_agent.newRTCFunction("output_message", output_func_translated)
out_fn.setMessageOutput("location")

stairwell_output_fn = stairwell_agent.newRTCFunction("stairwell_output_message", stairwell_output_func_translated)
stairwell_output_fn.setMessageOutput("stairwell_location")

set_target_stairwell_fn = student_agent.newRTCFunction("set_target_stairwell", set_target_stairwell_func_translated)
set_target_stairwell_fn.setMessageInput("stairwell_location")

move_to_stairwell_fn = student_agent.newRTCFunction("move_to_stairwell", move_to_stairwell_func_translated)
move_to_stairwell_fn.setMessageOutput("location")

# Message input depends on output
out_fn.dependsOn(stairwell_output_fn)
set_target_stairwell_fn.dependsOn(stairwell_output_fn)
move_to_stairwell_fn.dependsOn(set_target_stairwell_fn)
move_to_stairwell_fn.dependsOn(out_fn)


# 添加学生代理类型
# 基于data/output/flamegpu_init_code.py的学生代理初始化


# Dependency specification
# Output is the root of our graph
model.addExecutionRoot(stairwell_output_fn) 
model.generateLayers()



# ## simulation creation

# In[27]:


# Create and init the simulation
cuda_model = pyflamegpu.CUDASimulation(model)



# ## initialization

# In[28]:


from flamegpu_init_code import initialize_student_agent_population

# 初始化学生代理种群
initialize_student_agent_population(model, cuda_model)

# Specify the desired StepLoggingConfig
step_log_cfg = pyflamegpu.StepLoggingConfig(model)
# Log every step
step_log_cfg.setFrequency(1) 
# Include the mean of the "point" agent population's variable 'drift'
step_log_cfg.agent("student_agent").logMeanFloat("drift")
step_log_cfg.agent("student_agent").logMeanFloat("x")
step_log_cfg.agent("student_agent").logMeanFloat("y")


cuda_model.initialise(sys.argv)


# Attach the logging config
cuda_model.setStepLog(step_log_cfg)


# ## visualization

# In[ ]:


WIDTH=500

# Only run this block if pyflamegpu was built with visualisation support
if pyflamegpu.VISUALISATION:
    # Create visualisation
    m_vis = cuda_model.getVisualisation()
    # Set the initial camera location and speed
    INIT_CAM = WIDTH / 2
    m_vis.setInitialCameraTarget(270, 205, 0)
    m_vis.setInitialCameraLocation(240, 100, 100)
    m_vis.setCameraSpeed(0.01)
    m_vis.setSimulationSpeed(25)
    # Add "point" agents to the visualisation

    
    # Add "student_agent" agents to the visualisation
    student_agt = m_vis.addAgent("student_agent")
    student_agt.setModel(pyflamegpu.ICOSPHERE);
    student_agt.setModelScale(1/1.0);
    # Mark the environment bounds.

    stairwell_agt = m_vis.addAgent("stairwell_agent")
    stairwell_agt.setModel(pyflamegpu.ICOSPHERE);
    stairwell_agt.setModelScale(1/0.5);
    stairwell_agt.setColor(pyflamegpu.RED);
    
    pen = m_vis.newPolylineSketch(1, 1, 1, 0.2)
    pen.addVertex(275, 637, 0) # 起始点
    pen.addVertex(69, 510, 0)
    pen.addVertex(0, 301, 0)
    pen.addVertex(1, 167, 0)
    pen.addVertex(29, 142, 0)
    pen.addVertex(57, 98, 0)
    pen.addVertex(118, 67, 0)
    pen.addVertex(109, 24, 0)
    pen.addVertex(287, 0, 0)
    pen.addVertex(286, 45, 0)
    pen.addVertex(405, 154, 0)
    pen.addVertex(435, 131, 0)
    pen.addVertex(436, 72, 0)
    pen.addVertex(467, 41, 0)
    pen.addVertex(501, 35, 0)
    pen.addVertex(543, 47, 0)
    pen.addVertex(275, 637, 0) # 闭合点 
    # Open the visualiser window 
    m_vis.activate()

# Run the simulation
for i in range(100):
    cuda_model.step()



if pyflamegpu.VISUALISATION:
    # Keep the visualisation window active after the simulation has completed
    m_vis.join()


# ## data collection

# In[ ]:



