import os
from lib import Phase
from configs.handler_mapping import config
from configs.agents import *
from configs.tasks import *

# Define test phase 
def run_test_phase(data):
   pass

# Define testing phase validation method
def validate_test_phase():
    
    # List required file paths
    test_file = os.path.join(config.project_name, 'test.py')
    
    # Check for existance of files
    tests = [
        os.path.exists(test_file)
    ]

    # Only return True if all file checks pass
    return all(tests)

testing_phase = Phase(
    title="Testing",
    description=dedent("""
            In this phase, the LLM must run the code that is 
            written in the prior development phase, 
            test it, and iteratively debug it until a working 
            solution is found that passes all the tests.
    """),
    phase_func=run_test_phase,
    validation_func=validate_test_phase,
    load_func=lambda data: None
)
