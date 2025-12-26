from pyflamegpu import *
import pyflamegpu.codegen
import sys
import math

# Define an host function called write_env_hostfn
class write_env_hostfn(pyflamegpu.HostFunction):
  
  def __init__(self):
    super().__init__()  
  
  def run(self,FLAMEGPU):

      # Retrieve the environment macro property bar of type int array[5][5]

      # Update some of the values
      # foo = 12.0; is not allowed
      FLAMEGPU.environment.importMacroProperty("map", "attraction_matrix_familiar_points.json");

      FLAMEGPU.environment.exportMacroProperty("map", "out1.json");
 
    # Python does not allow the increment operator to be overridden

model = pyflamegpu.ModelDescription("F_MAP_tutorial")




env = model.Environment()
env.newMacroPropertyFloat("map", 700, 700)


# Define an agent named point
agent = model.newAgent("point")
# Assign the agent some variables (ID is implicit to agents, so we don't define it ourselves)
agent.newVariableFloat("x")
agent.newVariableFloat("y")
agent.newVariableFloat("test_value")
agent.newVariableFloat("drift", 0)
 
@pyflamegpu.agent_function
def map_get(message_in: pyflamegpu.MessageNone, message_out: pyflamegpu.MessageNone):
  x1 = pyflamegpu.getVariableFloat("x")
  y1 = pyflamegpu.getVariableFloat("y")
  m=int(x1)
  n=int(y1)
  #获取我们env里的map值
  map = pyflamegpu.environment.getMacroPropertyFloat("map", 700,700)
  map_point = map[m][n] 


  dis_x = x1-0
  dis_y = y1-1
  separation = math.sqrtf(dis_x*dis_x + dis_y*dis_y)
  test_value = map_point/1
  pyflamegpu.setVariableFloat("test_value", test_value)
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
ENV_WIDTH=500
AgentPopulation = pyflamegpu.AgentVector(model.Agent("point"), AGENT_COUNT)
for i in range(AGENT_COUNT):
    agent = AgentPopulation[i]
    agent.setVariableFloat("x", 204)
    agent.setVariableFloat("y", 69)

cuda_model.setPopulationData(AgentPopulation)

cuda_model.initialise(sys.argv)

# Attach the logging config
cuda_model.setStepLog(step_log_cfg)

plan = pyflamegpu.RunPlan(model)
plan.setSteps(10)

# Run the simulation
cuda_model.simulate()

out_pop = pyflamegpu.AgentVector(model.Agent("point"))
cuda_model.getPopulationData(out_pop)
for agent in out_pop:
    print("value: %f"%(agent.getVariableFloat("test_value")))


# python test_familiarity_map.py -s 10