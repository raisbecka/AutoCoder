import os
from lib import Phase
from configs.project import config
from configs.agents import *
from configs.tasks import *

# Define development phase 
def run_development_phase(data):

   pass

# Define planning phase validation method
def validate_development_phase():
    
    # List required file paths
    test_file = os.path.join(config.project_name, 'test.py')
    
    # Check for existance of files
    tests = [
        os.path.exists(test_file)
    ]

    # Only return True if all file checks pass
    return all(tests)

planning_phase = Phase(
    title="Planning",
    description=dedent("""
            In this phase, the LLM must plan out the work that
            needs to be completed in order to complete the development
            task.
    """),
    phase_func=run_development_phase,
    validation_func=validate_development_phase
)


    