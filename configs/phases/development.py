from math import floor
import os
import sys
import re
from lib import Phase
from configs.handler_config import config
from configs.agents import *
from configs.tasks import *
from configs.processes import *
from difflib import ndiff
import string
import logging
logger = logging.getLogger(__name__)
logger.propagate = True


# Define development phase 
def run_development_phase(**data):
   
    # Generate code
    source_code = developer.perform_task(
        generate_code, 
        inputs={
            'specs': data['specs']
        }
    )

    # Segment and semantically index code for later
    data = index_code(source_code) | data
    if data:

        results = fetch_relevant_code(data, "The script must accept a name command line argument to greet the user", 1)
        print(results)

        # Validation loop
        while True:
            
            # Validate requirements
            data = validate_items(
                data=data, 
                validation_task=validate_code,
                input_data='requirements',
                validation_target='source_files',
                output_label='implementation',
                n=5
            ) | data

            # Check if all requirements have been implemented
            if len(data['code_validation']['fail']) == 0:
                break
            
            # Add/fix requirements that failed validation
            else:
                
                data = developer.perform_task(
                    add_missing_requirements, 
                    inputs={
                        'requirements': data['specs']
                    }
                ) | data

        # Validate requirements
        data = validate_items(
            data=data, 
            validation_task=validate_code,
            input_label='requirements',
            output_label='code_validation',
            n=5
        ) | data

        # Generate tests
        data = developer.perform_task(
            generate_tests, 
            inputs={
                'test_plan': data['tests']
            }
        ) | data

        return data
    
    else:
        
        logger.debug("Failed to properly segment code for semantic indexing; check tasks.py and update task as required. Terminating...")
        sys.exit(1)
     

   

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


# Load data from previously completed phase
def load_development_data(data):
    
    with open(f"{config.project_root}/requirements.json", 'r') as f:
        data = json.loads(f.read())
    
    with open(f"{config.project_root}/test_plan.json", 'r') as f:
        data = json.loads(f.read()) | data

    return data


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
