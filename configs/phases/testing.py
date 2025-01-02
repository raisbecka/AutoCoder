import os
from lib import Phase
from configs.handler_config import config
from configs.agents import *
from configs.tasks import *

# Runs a command directly using the command handler
def run_tests():
    data = config.handlers['cmd'].process(
        [
            {
                'command': f"{config.python_version} -m unittest test.py",
            }
        ]
    )

    # Return output of the single command run
    return data['commands'][0]['output']

# Define test phase 
def run_test_phase(**data):

    # Set to True when all tests pass
    tests_complete = True

    # Main testing loop
    while not tests_complete:
        result = run_tests()

        #TODO: Create Single and Many Review tasks
        review_result = developer.perform_task(
            analyze_test_run,
            inputs={
                'test_output': result
            }
        )

        # Script ran successfully
        if 'success' in review_result.lower():
            
            data = developer.perform_task(
                examine_test_output, 
                inputs={
                    'test_output': result
                }
            ) | data

            #TODO::::::: ADD CODE LINKING UNIT TESTS DIRECTLY TO TEST OBJECTS SO THAT EXPECTED RESULTS CAN BE COMPARED AS WELL
            for test in data['tests']:
                if test['status'] != 'pass':
                    tests_complete = False
                    break

        # Test script failed
        else:
            
            data = developer.perform_task(
                analyze_test_error, 
                inputs={
                    'error_message': result
                }
            ) | data
            

    # Run test.py file to execute project code tests
    config.run_command
   
    # Generate code
    data = product_owner.perform_task(
        generate_code, 
        inputs={
            'specs': data['specs']
        }
    ) | data

    # Validate requirements
    validate_requirements(data, n=5)

    # Generate tests
    data = product_owner.perform_task(
        generate_tests, 
        inputs={
            'test_plan': data['tests']
        }
    ) | data

    return data

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
