from math import floor
import os
from lib import Phase
from configs.handler_mapping import config
from configs.agents import *
from configs.tasks import *

# Validate the requirements in chunks of N
def validate_requirements(data, n=5):
    imp_data = {}
    number_of_requirements = len(data['requirements'])
    if number_of_requirements <= n:
        i_max = 0
    else:
        i_partition = floor(number_of_requirements / n)
        i_max = i_partition * n
        for i in range(0, i_partition, n):
            requirement_slice = data['requirements'][i:i+n]
            imp_data = product_owner.perform_task(
                validate_code, 
                inputs={
                    'requirements': requirement_slice
                }
            ) | imp_data

    # Validate remaining requirements
    requirement_slice = data['requirements'][i_max:]
    data['implementation'] = product_owner.perform_task(
        validate_code, 
        inputs={
            'requirements': requirement_slice
        }
    ) | imp_data

# Define development phase 
def run_development_phase(**data):
   
    # Generate code
    data = product_owner.perform_task(
        generate_code, 
        inputs={
            'specs': data['specs']
        }
    ) | data

    # Validate requirements
    validate_requirements(data, n=5)
   

# Define planning phase validation method
def validate_development_phase():
    
    # List required files
    src_folder = os.path.join(config.project_root, config.src_dir)
    imp_file = os.path.join(config.project_root, 'implementation.json')
    
    # Check for existance of files
    tests = [
        len(os.listdir(src_folder)) > 0,
        os.path.exists(imp_file)
    ]

    # Only return True if all file checks pass
    return all(tests)

development_phase = Phase(
    title="Development",
    description=dedent("""
            In this phase, the LLM must write the code that is 
            outlined and defined in the prior planning phase, and 
            write the associated testing code in order to proceed to 
            the final "testing" phase.
    """),
    phase_func=run_development_phase,
    validation_func=validate_development_phase,
    load_func=lambda data: None
)
