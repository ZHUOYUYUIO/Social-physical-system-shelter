import os
import yaml
config_path = os.path.join(os.path.dirname(__file__), '../config/env.yaml')

with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
base_population = config.get('base_population', 50) 

print(base_population) 