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
message = model.newMessageSpatial2D("location")
# Configure the message list
message.setMin(0, 0)
message.setMax(ENV_WIDTH, ENV_WIDTH)
message.setRadius(2)
# Add extra variables to the message
# X Y (Z) are implicit for spatial messages
message.newVariableID("id")

# Define an agent named point
agent = model.newAgent("point")
# Assign the agent some variables (ID is implicit to agents, so we don't define it ourselves)
agent.newVariableFloat("x")
agent.newVariableFloat("y")
agent.newVariableFloat("drift", 0) #这个会被随机分配到新created or newly birthed agents

# Define environment properties
env = model.Environment()
env.newPropertyUInt("AGENT_COUNT", AGENT_COUNT)
env.newPropertyFloat("ENV_WIDTH", ENV_WIDTH)
env.newPropertyFloat("repulse", 0.05)

@pyflamegpu.agent_function
def output_message(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageSpatial2D):
    message_out.setVariableUInt("id", pyflamegpu.getID())
    message_out.setLocation(
        pyflamegpu.getVariableFloat("x"),
        pyflamegpu.getVariableFloat("y"))
    return pyflamegpu.ALIVE

@pyflamegpu.agent_function
def input_message(message_in: pyflamegpu.MessageSpatial2D, message_out: pyflamegpu.MessageNone):
    ID = pyflamegpu.getID()
    REPULSE_FACTOR = pyflamegpu.environment.getPropertyFloat("repulse")
    RADIUS = message_in.radius()
    fx = 0.0
    fy = 0.0
    x1 = pyflamegpu.getVariableFloat("x")
    y1 = pyflamegpu.getVariableFloat("y")
    count = 0
    for message in message_in(x1, y1):
        if message.getVariableUInt("id") != ID :
            x2 = message.getVariableFloat("x")
            y2 = message.getVariableFloat("y")
            x21 = x2 - x1
            y21 = y2 - y1
            separation = math.sqrtf(x21*x21 + y21*y21)
            if separation < RADIUS and separation > 0 :
                k = math.sinf((separation / RADIUS)*3.141*-2)*REPULSE_FACTOR
                # Normalise without recalculating separation
                x21 /= separation
                y21 /= separation
                fx += k * x21
                fy += k * y21
                count += 1
    fx /= count if count > 0 else 1
    fy /= count if count > 0 else 1
    pyflamegpu.setVariableFloat("x", x1 + fx)
    pyflamegpu.setVariableFloat("y", y1 + fy)
    pyflamegpu.setVariableFloat("drift", math.sqrtf(fx*fx + fy*fy))
    return pyflamegpu.ALIVE

# translate the agent functions from Python to C++
output_func_translated = pyflamegpu.codegen.translate(output_message)
input_func_translated = pyflamegpu.codegen.translate(input_message)
# Setup the two agent functions
out_fn = agent.newRTCFunction("output_message", output_func_translated)
out_fn.setMessageOutput("location")
in_fn = agent.newRTCFunction("input_message", input_func_translated)
in_fn.setMessageInput("location")

# Message input depends on output
in_fn.dependsOn(out_fn)
# Dependency specification
# Output is the root of our graph
model.addExecutionRoot(out_fn)
model.generateLayers()

class create_agents(pyflamegpu.HostFunction):
    def run(self, FLAMEGPU):
        # Fetch the desired agent count and environment width
        AGENT_COUNT = FLAMEGPU.environment.getPropertyUInt("AGENT_COUNT")
        ENV_WIDTH = FLAMEGPU.environment.getPropertyFloat("ENV_WIDTH")
        # Create agents
        t_pop = FLAMEGPU.agent("point")
        for i in range(AGENT_COUNT):
            t = t_pop.newAgent()
            t.setVariableFloat("x", FLAMEGPU.random.uniformFloat() * ENV_WIDTH)
            t.setVariableFloat("y", FLAMEGPU.random.uniformFloat() * ENV_WIDTH)

model.addInitFunction(create_agents()) 

# Specify the desired StepLoggingConfig
step_log_cfg = pyflamegpu.StepLoggingConfig(model)
# Log every step
step_log_cfg.setFrequency(1)
# Include the mean of the "point" agent population's variable 'drift'
step_log_cfg.agent("point").logMeanFloat("drift")

# Create and init the simulation
cuda_model = pyflamegpu.CUDASimulation(model)
cuda_model.initialise(sys.argv)

# Attach the logging config
cuda_model.setStepLog(step_log_cfg)

# Only run this block if pyflamegpu was built with visualisation support
if pyflamegpu.VISUALISATION:
    # Create visualisation
    m_vis = cuda_model.getVisualisation()
    # Set the initial camera location and speed
    INIT_CAM = ENV_WIDTH / 2
    m_vis.setInitialCameraTarget(INIT_CAM, INIT_CAM, 0)
    m_vis.setInitialCameraLocation(INIT_CAM, INIT_CAM, ENV_WIDTH)
    m_vis.setCameraSpeed(0.01)
    m_vis.setSimulationSpeed(25)
    # Add "point" agents to the visualisation
    point_agt = m_vis.addAgent("point")
    # Location variables have names "x" and "y" so will be used by default
    point_agt.setModel(pyflamegpu.ICOSPHERE);
    point_agt.setModelScale(1/10.0);
    # Mark the environment bounds
    pen = m_vis.newPolylineSketch(1, 1, 1, 0.2)
    pen.addVertex(0, 0, 0)
    pen.addVertex(0, ENV_WIDTH, 0)
    pen.addVertex(ENV_WIDTH, ENV_WIDTH, 0)
    pen.addVertex(ENV_WIDTH, 0, 0)
    pen.addVertex(0, 0, 0)
    # Open the visualiser window
    m_vis.activate()

# Run the simulation
cuda_model.simulate()

if pyflamegpu.VISUALISATION:
    # Keep the visualisation window active after the simulation has completed
    m_vis.join()