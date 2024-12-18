import os
from lib import Phase
from configs.project import config
from configs.agents import *
from configs.tasks import *

# Define planning phase 
def run_planning_phase(**data):

    # Generate cleaned specs
    data = product_owner.perform_task(
        generate_specs,
        inputs={
            'specs': data['specs']
        }
    ) | data

    # Generate requirements 
    data = product_owner.perform_task(
        generate_requirements, 
        inputs={
            'specs': data['text']
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
    final_specs_path = os.path.join(config.project_name, 'final_specs.txt')
    requirements_path = os.path.join(config.project_name, 'requirements.json')
    tests_path = os.path.join(config.project_name, 'test_plan.json')

    # Check for existance of files
    tests = [
        os.path.exists(final_specs_path),
        os.path.exists(requirements_path),
        os.path.exists(tests_path)
    ]

    # Only return True if all file checks pass
    return all(tests)

# Define the planning phase, and link the above methods/functions
planning_phase = Phase(
    title="Planning",
    description=dedent("""
            In this phase, the LLM must plan out the work that
            needs to be completed in order to complete the development
            task.
    """),
    phase_func=run_planning_phase,
    validation_func=validate_planning_phase
)


    