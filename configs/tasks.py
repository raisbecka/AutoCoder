from textwrap import dedent
from configs.handler_config import config
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
        following ACID design principles, but keep all the code in a very minimal number of source files. All operations should
        be carried out within methods/functions, and each method/function should have a singular, clear purpose. For each method/
        function or class, you must include a docstring that explains what the code does in great detail, what it's purpose is, 
        what it's parameters are, and what it returns (Even if it returns None). If code is not within a method/function or class,
        document each similar section of code as if it was a method/function (that is - provide a docstring for it).

        Similarly, at the top of each file, include a docstring that explains the overall purpose of that source code file, 
        and any params/arguments it takes (with an example of using them). For the params or arguments, analyze the code and try to 
        determine what the purpose of the params/args are, and note this in the description for the file.
        
        Also, remember that no Python modules are installed. Therefore, if any are used, ensure that they are installed by issuing the 
        necessary command(s). 
                   
        See specifications below:
        """ + """
        {specs}
        """),
    expected_elements=[File, Command]
)

# Define code generation task
generate_documentation = Task(
    details=dedent(f"""
        Ensure that doxy
                   
        See specifications below:
        """ + """
        {specs}
        """),
    expected_elements=[File, Command]
)

# Define task that validates written code against requirements to assess completion
validate_code = Task(
    details=dedent("""
        Provided the below technical requirements, your task is to ensure that the requirements are properly addressed
        and implemented in one or more of the segments of code that have been included. 
                   
        See requirements below:

        {requirements}
                   
        ...and below is the relevant code that may or may not satisfy one or more of the requirements:
                   
        {source_files}
        """),
    expected_elements=[File, Command]
)

# Define task that adds requirements that were previously missed when writing code in the development phase
add_missing_requirements = Task(
    details=dedent("""
        Provided the below list of missed requirements, your task is to ensure that these requirements are fully and properly
        implemented in the code below; you will need to add or fix the code below as necessary to meet these missing or failed
        requirements, but you must do so without impacting the existing code in such a way that other requirements no longer 
        pass. Keep in mind this code represents an MVP solution, so you should only add the minimum amount of code necessary
        to meet the requirements.
                   
        See the missing requirements below:

        {requirements}
                   
        ...and below is the code that was written to satisfy the requirements:
                   
        {source_files}
                   
        In your response, for any source files that need to be updated, ensure that the complete, updated source code is included
        in the response. Also include any commands that need to be run in order to run the source code (such as installing required
        packages, etc.).
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

        - The test cases in this script must cover all of the included tests in the plan below. At the top of the test.py script, 
        you MUST create a dictionary called "test_plan" where the keys match the test ID's exactly, and the values are the test functions 
        that will be run. At the bottom of the file, in a "if __name__ == '__main__':" block, you MUST ALSO run the tests one-by-one - 
        iterating through the test ID's in alphabetical ascending order.

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

############## TESTING TASKS ################

# Define task for determining result of running test.py
analyze_test_run = Task(
    details=dedent("""
        The script \"test.py\" has been run, and it's output is included below. Analyze the output to determine if the test.py file 
        ran successfully, or if an error was encountered while running the file. Note that failing tests (or errors produced by running 
        another source file FROM test.py) do not count as errors in the test.py file itself. An error has occured ONLY if the error was 
        produced by code in the test.py file itself.
                   
        If an error has occured, respond ONLY with the word ERROR. If the script ran successfully, respond with the word SUCCESS.
                   
        test.py script output:

        {test_output}            
        """)
)

# Define task for analyzing test errors and producing a fixed test.py file
analyze_test_error = Task(
    details=dedent("""
        The script test.py failed with the below error message. Analyze the error and produce a fixed test.py file.
                   
        Error message:

        {error_message}
        """),
    expected_elements=[File, Command]
)

# Define task for examining successful test output and updating source code if necessary
examine_test_output = Task(
    details=dedent("""
        The script test.py ran successfully. Examine the output below, and respond with each test ID, a status of "pass" or "fail" 
        for each test, and - if the test failed - the necessary commands or code revisions required to fix the code so that the 
        test passes on the next iteration. 
                   
        For any code changes, ensure that the complete, updated source code is included in the response. Also include any commands
        that need to be run in order to resolve issues (such as missing packages, etc.) - but ONLY if required.
                   
        test.py script output:

        {test_output}
        """),
    expected_elements=[File, Command]
)

# Define task for breaking down code into segments with detailed descriptions
index_code_semantically = Task(
    details=dedent("""
        Take the provided source code files and break them down into semantically similar segments. Each segment should consist of:
        
        - A unique method or function in the code - which should already be ATOMIC in nature.
        - An entire class definition if the code is under 100 lines or so.
        - A block of code that is highly related in function and written sequentially in the source code - not appearing inside a 
        class or method/function.
        
        The segments should be ordered in the same order as they appear in the source code file they come from, and segments should be 
        grouped by file. Each segment should include details regarding the functionality of the code, it's purpose, and any other 
        important implementation details or information relating to context.
        
        For each file, the contents of each segment concatenated together should equal the contents of the original source
        code file - ignoring formatting. Even comments should be preserved in the segment. NO modifications should be made at all
        to the code stored for each segment - including escape strings. Do not use any URL encodings either. The code segment
        string must be exactly the same as the original source file.
        Also, do NOT enclose code in ``` or anything else like that. Only enclose the code in <segment_content></segment_content>.
        
        The output should include:
        - The file name for each segment.
        - A detailed description of the segment's functionality. This should be an extremely detailed description - which describes EVERYTHING
        that the section of code does. All variable names should be referenced, as well as all operations performed. At the end of this detailed 
        description, ensure that the overall purpose of the section is described to finish it off.
        - The source code contained within the segment
        
        Source code file:
                   
        {source_files}
        """),
    expected_elements=[CodeSegment]
)
