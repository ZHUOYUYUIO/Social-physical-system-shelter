#这个test.py是用来测试pyflame的可视性的

from pyflamegpu import *
import pyflamegpu.codegen
import sys

# Define some useful constants
AGENT_COUNT = 16384
ENV_WIDTH = int(AGENT_COUNT**(1/3))

# Define the FLAME GPU model: 这个可以在后续的可视化窗口改名字
model = pyflamegpu.ModelDescription("First test using default visualization")

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


# Assign the agent some variables (ID is implicit to agents, so we don't define it ourselves)
student_agent = model.newAgent("student_agent")
student_agent.newVariableFloat("x")
student_agent.newVariableFloat("y")
student_agent.newVariableInt("building_id")
student_agent.newVariableInt("point_id")
student_agent.newVariableFloat("z")
student_agent.newVariableFloat("drift", 0)

# Define environment properties
env = model.Environment()
env.newPropertyUInt("AGENT_COUNT", AGENT_COUNT)
env.newPropertyFloat("ENV_WIDTH", ENV_WIDTH)
env.newPropertyFloat("repulse", 0.05)

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

# translate the agent functions from Python to C++
output_func_translated = pyflamegpu.codegen.translate(output_message)
input_func_translated = pyflamegpu.codegen.translate(input_message)
# Setup the two agent functions
out_fn = student_agent.newRTCFunction("output_message", output_func_translated)
out_fn.setMessageOutput("location")
in_fn = student_agent.newRTCFunction("input_message", input_func_translated)
in_fn.setMessageInput("location")

# Message input depends on output
in_fn.dependsOn(out_fn)

# 添加学生代理类型
# 基于data/output/flamegpu_init_code.py的学生代理初始化


# Dependency specification
# Output is the root of our graph
model.addExecutionRoot(out_fn)
model.generateLayers()


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

WIDTH=500

# Only run this block if pyflamegpu was built with visualisation support
if pyflamegpu.VISUALISATION:
    # Create visualisation
    m_vis = cuda_model.getVisualisation()
    # Set the initial camera location and speed
    INIT_CAM = WIDTH / 2
    m_vis.setInitialCameraTarget(270, 205, 0)
    m_vis.setInitialCameraLocation(400, 400, 100)
    m_vis.setCameraSpeed(0.01)
    m_vis.setSimulationSpeed(25)
    # Add "point" agents to the visualisation

    
    # Add "student_agent" agents to the visualisation
    student_agt = m_vis.addAgent("student_agent")
    student_agt.setModel(pyflamegpu.ICOSPHERE);
    student_agt.setModelScale(1/1.0);
    # Mark the environment bounds.

    
    pen = m_vis.newPolylineSketch(1, 1, 1, 0.2)
    pen.addVertex(157, 123, 0) #左下
    pen.addVertex(157, 287, 0)  #左上
    pen.addVertex(384, 287, 0) #右上
    pen.addVertex(384, 123, 0) #右下
    pen.addVertex(157, 123, 0) #左下
    # Open the visualiser window 
    m_vis.activate()

# Run the simulation
cuda_model.simulate()

if pyflamegpu.VISUALISATION:
    # Keep the visualisation window active after the simulation has completed
    m_vis.join()