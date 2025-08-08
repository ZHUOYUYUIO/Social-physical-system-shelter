#这个test.py是用来测试pyflame的可视性的

from pyflamegpu import *
import pyflamegpu.codegen
import sys
import math

# Define some useful constants
AGENT_COUNT = 16384
ENV_WIDTH = 10

# Define the FLAME GPU model: 这个可以在后续的可视化窗口改名字
model = pyflamegpu.ModelDescription("Social_physical_shelter_Opt")

# Define a message of type MessageSpatial2D named location
# MessageSpatial2D: Each agent outputs a message at a specific location in 2D space
# agents only read messages located close to a particular search origin（搜素的中心点）.
# 可以获取一定距离内的消息
message = model.newMessageSpatial3D("location")
# Configure the message list
message.setMin(0, 0,0)
message.setMax(ENV_WIDTH, ENV_WIDTH,ENV_WIDTH)
message.setRadius(2)
# Add extra variables to the message
# X Y (Z) are implicit for spatial messages
message.newVariableID("id")

stairwell_message = model.newMessageSpatial3D("location_stairwell")
stairwell_message.setMin(0, 0,0)
stairwell_message.setMax(500, 500, 500)
message.setRadius(200)
stairwell_message.newVariableID("id")
stairwell_message.newVariableFloat("class")

# Assign the agent some variables (ID is implicit to agents, so we don't define it ourselves)
student_agent = model.newAgent("student_agent")
student_agent.newVariableFloat("x")
student_agent.newVariableFloat("y")
student_agent.newVariableInt("building_id")
student_agent.newVariableInt("point_id")
student_agent.newVariableFloat("z")
student_agent.newVariableFloat("drift", 0)
#set the states for student agents
student_agent.newState("not evacuate")
student_agent.newState("focused")
student_agent.newState("building evacuate")
student_agent.newState("stairwell evacuate")
student_agent.newState("neighborhood evacuate")

stairwell_agent = model.newAgent("stairwell_agent")
stairwell_agent.newVariableFloat("x")
stairwell_agent.newVariableFloat("y")
stairwell_agent.newVariableInt("stairwell_id")
stairwell_agent.newVariableFloat("z")

#如何用python版本，为不同类型的agents设置

# Define environment properties
env = model.Environment()
env.newPropertyUInt("AGENT_COUNT", AGENT_COUNT)
env.newPropertyFloat("ENV_WIDTH", ENV_WIDTH)
env.newPropertyFloat("repulse", 0.05)

'''
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
'''
@pyflamegpu.agent_function
def move(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageNone):
    x=pyflamegpu.getVariableFloat("x")
    y=pyflamegpu.getVariableFloat("y")
    z=pyflamegpu.getVariableFloat("z")

    
    pyflamegpu.setVariableFloat("x", x+1)
    pyflamegpu.setVariableFloat("y", y+1)
    pyflamegpu.setVariableFloat("z", z+1)


    return pyflamegpu.ALIVE

@pyflamegpu.agent_function
def student_output_message(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageArray3D):
    message_out.setVariableUInt("id", pyflamegpu.getID())
    message_out.setVariable
    message_out.setLocation(
        pyflamegpu.getVariableFloat("x"),
        pyflamegpu.getVariableFloat("y"),
        pyflamegpu.getVariableFloat("z")
        )
    return pyflamegpu.ALIVE



#纯靠函数内判断距离：
@pyflamegpu.agent_function
def find_and_premove(message_in: pyflamegpu.MessageArray3D, message_out: pyflamegpu.MessageNone):
    rad = pyflamegpu.environment.getPropertyFloat("rad")
    x1=pyflamegpu.getVariableFloat("x")
    y1=pyflamegpu.getVariableFloat("y")
    z1=pyflamegpu.getVariableFloat("z")

    for message in pyflamegpu.message_in:
        x2 = message.getVariableFloat("x")
        y2 = message.getVariableFloat("y")        
        z2 = message.getVariableFloat("z")  
        x21 = x2 - x1
        y21 = y2 - y1
        z21 = z2 - z1
        separation = math.sqrtf(x21*x21 + y21*y21 + z21*z21)
        if separation < rad and separation > 0 :


######
## AGENT STATES SHIFT AND AGENT MOVE
######

#STUDENT AGENT: FOCUSED --> BUILDING EVACUATE

def student_agent_move_F_to_BE(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageNone):
    #这里要获取周围有多少BE的agents:具体做法是：获取message的信息，根据message的状态？现在的问题是如何获取agent的状态并放进message里面。
    


#STUDENT AGENT: NOT EVACUATE --> BUILDING EVACUATE

def student_agent_move_NE_to_BE(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageNone):

#STUDENT AGENT: BUILDING EVACUATE --> STAIRWELL EVACUATE
@pyflamegpu.agent_function
def student_agent_move_BE_to_SE(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageNone):
    #这里我需要为agent添加一个变量：target_stairwell。最好是list那种，我直接获取这个点的坐标，现在简单一点，我就用直线距离？
    #有一个大问题：就是，碰到墙壁了该怎么办？还有行人之间的拥堵怎么设置啊。飞鸟模型？？
 
 #condition for transition from BE to SE
@pyflamegpu.agent_function_condition
def BE_to_SE_DISTANCE() -> bool:
    return pyflamegpu.getVariableInt("distance") <= 0


# translate the agent functions from Python to C++
#output_func_translated = pyflamegpu.codegen.translate(output_message)
#input_func_translated = pyflamegpu.codegen.translate(input_message)

move_func_translated= pyflamegpu.codegen.translate(move)
move_fn = student_agent.newRTCFunction("move",move_func_translated)

move_s_fn = stairwell_agent.newRTCFunction("move",move_func_translated)

move_s_fn.dependsOn(move_fn)


#转换stairwell的输出函数并绑定到agent上
stairwell_output_func_translated = pyflamegpu.codegen.translate(student_output_message)
student_output_message_fn = stairwell_agent.newRTCFunction("student_output_message",stairwell_output_func_translated)
#为stairwell输出函数绑定stairwell的专属消息类型
student_output_message_fn.setMessageOutput("location_stairwell")


model.addExecutionRoot(move_fn)
model.generateLayers()

'''
# Setup the two agent functions这里可以设置嗷嗷
out_fn = student_agent.newRTCFunction("output_message", output_func_translated)
out_fn.setMessageOutput("location")
in_fn = student_agent.newRTCFunction("input_message", input_func_translated)
in_fn.setMessageInput("location")

# Message input depends on output
in_fn.dependsOn(out_fn)
'''


# 添加学生代理类型
# 基于data/output/flamegpu_init_code.py的学生代理初始化


# Dependency specification
# Output is the root of our graph
#model.addExecutionRoot(move)
# model.generateLayers()


# Create and init the simulation
cuda_model = pyflamegpu.CUDASimulation(model)

# 导入flamegpu_init_code.py中的初始化函数
import sys 
import os
sys.path.append('data/output')
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



# Only run this block if pyflamegpu was built with visualisation support
if pyflamegpu.VISUALISATION:
    # Create visualisation
    m_vis = cuda_model.getVisualisation()
    # Set the initial camera location and speed

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
    pen.addVertex(171.1506859746878, 502.3716148252133, 0) # 起始点
    pen.addVertex(105.09561226965161, 359.44766954286024, 0)
    pen.addVertex(0.0, 229.08098894753493, 0)
    pen.addVertex(239.17631635762518, 0.0, 0)
    pen.addVertex(389.8694328930578, 124.25844648550265, 0)
    pen.addVertex(404.1783638363704, 443.24738321383484, 0)
    pen.addVertex(295.51630976161687, 477.6256132465787, 0)
    pen.addVertex(171.1506859746878, 502.3716148252133, 0) # 闭合点
    # Open the visualiser window 
    m_vis.activate()

# Run the simulation
cuda_model.simulate()

if pyflamegpu.VISUALISATION:
    # Keep the visualisation window active after the simulation has completed
    m_vis.join()


# python src/test_3d_with_function.py -s 10 --out-step step.json