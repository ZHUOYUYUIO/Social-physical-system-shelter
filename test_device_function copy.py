from pyflamegpu import *
import pyflamegpu.codegen
import sys
import math

# Define an host function called write_env_hostfn
class write_env_hostfn(pyflamegpu.HostFunction):
  
  def __init__(self):
    super().__init__()  
  
  def run(self,FLAMEGPU):
    FLAMEGPU.environment.importMacroProperty("map_3d", "obstacle1.json");


    # Python does not allow the increment operator to be overridden

model = pyflamegpu.ModelDescription("F_MAP_tutorial")


env = model.Environment()
env.newMacroPropertyInt("obstacle1", 4, 2)  



# Define an agent named point
agent = model.newAgent("point")
# Assign the agent some variables (ID is implicit to agents, so we don't define it ourselves)
agent.newVariableFloat("x")
agent.newVariableFloat("y")
agent.newVariableFloat("test_value")
agent.newVariableFloat("test_value1")
agent.newVariableFloat("drift", 0)

def mult(a,b):
  return a*b

@pyflamegpu.device_function
def mult(a: float, b: float) -> float :
  return abs(a+b)

@pyflamegpu.device_function
def dist(x: float, y: float) -> float:
  return math.sqrtf(x*x+y*y)

@pyflamegpu.device_function
def min(a: float, b: float) -> float:
  return a if a < b else b

@pyflamegpu.device_function
def max(a: float, b: float) -> float:
  return a if a > b else b


@pyflamegpu.agent_function
def map_get(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageNone):


    obstacle1 = pyflamegpu.environment.getMacroPropertyInt("obstacle1", 4, 2)

    inside = 0
    a=obstacle1[3][1]




    pyflamegpu.setVariableFloat("test_value", inside)
    pyflamegpu.setVariableFloat("test_value1", a)
    return pyflamegpu.ALIVE
   
map_get_translated = pyflamegpu.codegen.translate(map_get)
map_get_fn = agent.newRTCFunction("map_get",map_get_translated)

model.addInitFunction(write_env_hostfn())
model.addExecutionRoot(map_get_fn)
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

AGENT_COUNT=3
ENV_WIDTH=2
AgentPopulation = pyflamegpu.AgentVector(model.Agent("point"), AGENT_COUNT)
for i in range(AGENT_COUNT):
    agent = AgentPopulation[i]
    agent.setVariableFloat("x", random.uniform(0, ENV_WIDTH))
    agent.setVariableFloat("y", random.uniform(0, ENV_WIDTH))

cuda_model.setPopulationData(AgentPopulation)

cuda_model.initialise(sys.argv)

# Attach the logging config
cuda_model.setStepLog(step_log_cfg)

# Run the simulation
cuda_model.simulate()

out_pop = pyflamegpu.AgentVector(model.Agent("point"))
cuda_model.getPopulationData(out_pop)
for agent in out_pop:
    print("value: %f"%(agent.getVariableFloat("test_value1")))


# python test_familiarity_map.py -s 10