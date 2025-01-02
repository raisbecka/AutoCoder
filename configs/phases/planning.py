import os
from lib import Phase
from configs.handler_config import config
from configs.agents import *
from configs.tasks import *

# Define planning phase 
def run_planning_phase(**data):

    # Generate requirements 
    data = product_owner.perform_task(
        generate_requirements, 
        inputs={
            'specs': data['specs']
        }
    ) | data

    # Generate functional tests
    data = product_owner.perform_task(
        generate_functional_tests,
        inputs={
            'requirements': data['requirements']
        }
    ) | data

    return data


# Define planning phase validation method
def validate_planning_phase():
    
    # List required file paths
    requirements_path = os.path.join(config.project_root, 'requirements.json')
    tests_path = os.path.join(config.project_root, 'test_plan.json')

    # Check for existance of files
    tests = [
        os.path.exists(requirements_path),
        os.path.exists(tests_path)
    ]

    # Only return True if all file checks pass
    return all(tests)


# Load data from previously completed phase
def load_planning_data(data):
    
    with open(f"{config.project_root}/requirements.json", 'r') as f:
        data = json.loads(f.read())
    
    with open(f"{config.project_root}/test_plan.json", 'r') as f:
        data = json.loads(f.read()) | data

    return data


# Define the planning phase, and link the above methods/functions
planning_phase = Phase(
    title="Planning",
    description=dedent("""
            In this phase, the LLM must plan out the work that
            needs to be completed in order to complete the development
            task.
    """),
    phase_func=run_planning_phase,
    validation_func=validate_planning_phase,
    load_func=load_planning_data
)


    