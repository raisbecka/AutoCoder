from textwrap import dedent
from configs.handler_mapping import config
from configs.elements import *
from lib import Task

############## PLANNING TASKS ################

# Define user specification cleanup task
generate_specs = Task(
    details=dedent("""
        Take the below rough specifications, clean them up, and write them as you would write professional specifications 
        to be handed to a software developer. Take your time, and be as detailed as possible. 
                   
        See specifications below:

        {specs}

        """)
)

# Define high-level requirements generation task
generate_requirements = Task(
    details=dedent("""
        Take the below technical specifications, and write a numbered list of clear, concise functional requirements that
        must be met by the software. Each requirement should map directly to a function or feature of the software. Requirements
        should be written in a way that is easy to understand by a non-technical person, and should not reference any specific
        technology or implementation details; they should only describe at a high-level what the software should do.
                   
        See specifications below: 

        {specs}
        """),
    expected_elements=[Requirement]
)

# Define functional test case generation task
generate_functional_tests = Task(
    details=dedent("""
        Take the below technical requirements, and write a detailed, numbered list of test cases that cover all of the different
        types of user interaction that may occur - ensuring that the outcome in each case conforms to the technical requirements.
        You may write 1 or more tests for each requirement. Each test must include the requirement that it maps to, the details of 
        the test, and the expected result of the test.  
                   
        See requirements below: 
                        
        {requirements}
        """),
    expected_elements=[FunctionalityTest]
)


############## DEVELOPMENT TASKS ################

# Define code generation task
generate_code = Task(
    details=dedent(f"""
        Take the below technical specifications, and write Python code that satisfies all of them - ensuring that the code 
        follows best practises, and is well documented. Assume you are already in the root source code directory, so any 
        file names should be relative to the current/root directory. Organize the code into classes and methods as appropriate - 
        following ACID design principles, but keep all the code in a very minimal number of source files.
        
        Also, remember that no Python modules are installed. Therefore, if any are used, ensure that they are installed by issuing the 
        necessary command(s). 
                   
        See specifications below:
        """ + """
        {specs}
        """),
    expected_elements=[File, Command]
)

# Define task that validates written code against requirements to assess completion
validate_code = Task(
    details=dedent("""
        Provided the below technical requirements, your task is to ensure that the requirements are properly addressed,
        and implemented in one or more source code files. 
                   
        See requirements below:

        {requirements}
        """),
    expected_elements=[File, Command]
)

# Define functional test code generation task
generate_tests = Task(
    details=dedent(f"""Create a file called test.py (assume you are already in the corrent directory) which leverages the pytest framework
        for running tests to ensure that all the FUNCTIONAL requirements are working are met, and the code is working as 
        expected. Adhere to the points below:
                             
        - This file must contain EVERYTHING required to run the project and test it. Therefore, if seperate commands or processes 
        need to be run (such as starting a server) prior to the tests starting, this code MUST be included at the start of the 
        script, and it must also be cleaned up properly after the tests are finished (or an error occurs and the script stops).

        - The test cases in this script must cover all of the included tests in the plan below.

        - There cannot be any interaction with the user while running the tests. Therefore, tests that require input from the 
        user should instead use test files to simulate the user input while the tests are running.
                   
        - Only create tests for FUNCTIONAL requirements. For example, the requirement "The script should stop if the user presses 
        the X key" would have an associated test, but the requirement "The API must use FastAPI" is not functionality-based, and 
        does not need a test.

        - Once a test completes, or an error occurs during the processing of the test, a summary of that test, what it tests for, 
        and the result of the test should be printed to stdout.
        
        == Test Files/Data == 
        
        Any files required to run any of the tests should be saved in the subdirectory "{config.project_root}/{config.test_file_dir}". 
        Lastly, any code (interactive or not) that must be run to generate test files (of whatever type required) should be saved 
        in a file called "pretest.py" in the root of subdirectory "{config.project_root}". The pretest.py script is an optional 
        script; it is only required if no appropriate test files were available for a specific test.

        See technical requirment and implementation details below:
        """ + """
        {test_plan}
        """),
    expected_elements=[File, Command]
)