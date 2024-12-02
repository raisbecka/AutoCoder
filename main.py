import sys
from textwrap import dedent
from rich.console import Console
import json
import os
from dotenv import load_dotenv
import subprocess
import argparse
import traceback
import logging
from datetime import datetime
from versioning import Repo
import re
from models import Claude, Gemini, GPT, O1

# Load environment variables from .env file
load_dotenv()

# Set up logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    filename=f'logs/model_interactions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Global project name variable
PROJECT_NAME = None

# Constants
TARGET_PYTHON = "python3.11"
SCRIPT_PROMPTS_DIR = "script_prompts"
VALID_PHASES = ['planning', 'developing', 'testing']

# Will contain key project directories
SRC_DIR = None
TEST_FILES_DIR = None

# Model Configuration with provider information
MODEL_CONFIG = {
    'planning': {
        'company': 'openai',
        'model': 'gpt-4o'
    },
    'developing': {
        'company': 'anthropic',
        'model': 'claude-3-5-sonnet-latest'
    },
    'testing': {
        'company': 'anthropic',
        'model': 'claude-3-5-sonnet-latest'
    }
}

# Planning content
final_specs = None
requirements = None
test_plan = None

# Global dictionary to store source file contents
files = []
test_files = []

# Global dictionary to store command outputs
commands = []

# Initialize rich Console
console = Console()

# Initialize model instances for each phase
models = {}
for phase, config in MODEL_CONFIG.items():
    if config['company'] == 'google':
        models[phase] = Gemini(config['model'])
    elif config['company'] == 'openai':
        if 'o1' in config['model']:
            models[phase] = O1(config['model'])
        else:
            models[phase] = GPT(config['model'])
    elif config['company'] == 'anthropic': 
        models[phase] = Claude(config['model'])

# General rules for llm responses
rules = """
<RULES>
1.  File Creation and Editing: If a new file needs to be created, of if changes are required to an existing file, you must output the complete, updated file enclosed within 
    <file><test_file>TRUEORFALSE</test_file><file_name>FILE_NAME</file_name><file_content>FILE_CONTENT</file_content></file> - where test_file, file_name and file_content xml elements 
    are enclosed in a file element, TRUEORFALSE is replaced with True if the file is a test script or False otherwise, FILE_NAME is replaced with the name of the file, and 
    FILE_CONTENT is replaced with the contents of the file.
2.  Running Commands: Assume that the user is running Ubuntu with {TARGET_PYTHON} installed; If any python libraries or modules are used, they must be installed 
    prior to running any code. You must provide the commands necessary to install them enclosed within <cmd></cmd> xml element tags. Therefore, if the requests 
    library is required, you must provide the text <cmd>pip install requests</cmd>.
3.  Project Structure: All code files and resource files directly related to the project specifications the user provided (other than for testing) must be saved in subdirectory 
    "{PROJECT_NAME}/src". Any tests relating to this project must be saved in a file called "test.py" in the root of subdirectory "{PROJECT_NAME}". 
4.  Handling Test Files/Data: Any files required to run any of the tests should be saved in the subdirectory "{PROJECT_NAME}/test_files". Lastly, any code (interactive or not) that 
    must be run to generate test files (of whatever type required) should be saved in a file called "pretest.py" in the root of subdirectory "{PROJECT_NAME}". The pretest.py script is 
    an optional script; it is only required if no appropriate test files were available for a specific test.
</RULES>
"""

# System prompts for the models
system_prompts = {  
    'developing': f"""
        <
        You are an experienced full-stack software developer specializing in writing clean, well-documented Python code. 
        You will be asked to develop a solution spanning one or more source files that adheres to a provided project specification. 
        
        Ensure you adhere to the rules below:
        {rules}""",
    'testing': f"""You are an experienced full-stack software developer specializing in writing clean, well-documented Python code. 
        You will be provided code for a Python project - along with any errors or bugs that need to be resolved, or test cases that have failed.
        For any failing test case, you must determine why it failed, and provide updated code to resolve the issue.
        
        Ensure you adhere to the rules below:
        {rules}""",
}

task_prompts = {    
    'plan_specs': dedent("""Take the below rough specifications, clean them up, and write them as you would write professional specifications 
                             to be handed to a software developer. Take your time, and be as detailed as possible:

                        -- SPECS BELOW --

                        {specs}

                        """),

    'plan_requirements': dedent("""Take the below technical specifications, and write a detailed, numbered list of technical requirements as 
                                    you would for a software developer. Take your time, and be as detailed as possible. For any specific requirement,
                                    be as detailed as possible about how it should be implemented in Python - including any specific frameworks,
                                    protocols, principles, or approaches that are used. For each requirement, format it like below:
                                
                                    <req><req_id>ID</req_id><details>DETAILS</details></req> 
                                
                                    ...where ID cooresponds to the numbered ID of that requirement, and DETAILS cooresponds to the details of that requirement.

                        -- SPECS BELOW --

                        {specs}
                        """),

    'plan_tests': dedent("""Take the below technical requirements, and write a detailed, numbered list of test cases that cover all of the required 
                         functionality outlined in the technical requirements. You may write 1 or more tests for each requirement. Each test must include
                         the requirement that it maps to, the details of the test, and the expected result of the test. For each test, format it like below:

                         <test>
                            <test_id>TID</test_id>
                            <req_id>RID</req_id>
                            <test_details>DETAILS</test_details>
                            <test_file>
                                <file_name>FILENAME</file_name>
                                <file_description>FILE_DESCRIPTION</file_description>
                            </test_file>
                            <expected_result>RESULT</expected_result>
                         </test>

                         ... where TID cooresponds to the numbered ID of that test, ID cooresponds to the numbered ID of the related requirement,
                         DETAILS cooresponds to the details of that test, RESULT cooresponds to the expected result of that test. Also, zero or 
                         more test files can be used for each test as required to simulate user interactions or data flow. For each included test
                         file (if any), FILENAME should coorespond to the name of the test file, and FILE_DESCRIPTION should coorespond to a 
                         description of what that file is to be used for (what kind of data and/or interaction to simulate or test).

                        -- REQUIREMENTS BELOW --
                         
                        {reqs}
                        """),

    'generate_code': dedent("""Take the below list of technical requirements, and write Python code that satisfies all of them - ensuring that
                            the code follows best practises, is well documented, and a comment is left for each technical requirement in the code mapping
                            the requirement to the relevent code (using the requirement ID number). The source code can span multiple files if necessary:

                        -- REQUIREMENTS BELOW --
                        
                        {requirements}
                        """), 

    'generate_tests': dedent("""Create a file called test.py which leverages the pytest framework for running tests to ensure that all the specifications are working 
                             as expected. Adhere to the points below:
                             
                             - This file must contain EVERYTHING required to run the project and test it. Therefore, if seperate commands or processes need
                             to be run (such as starting a server) prior to the tests starting, this code MUST be included at the start of the script, and launched 
                             using subprocesses in Python. References to any subprocesses should be stored in variables for later. 

                             - The test cases in this script must cover all of the included tests in the plan below.

                             - There cannot be any interaction with the user while running the tests. Therefore, tests that require input from the user should instead 
                             use test files to simulate the user input while the tests are running.

                             - Once a test completes, or an error occurs during the processing of the test, a summary of that test, what it tests for, and the result of the 
                             test should be printed to stdout.
                             
                             - Once the tests have completed, or an error has occured, any commands or processes that are still running must be ended gracefully. 
                             
                             - If after 5 seconds a process or command is still running after attempting to end it gracefully, it should be killed forcefully. 
                             
                             - Therefore, when the test.py script is finished, anything that ran because of that script should no longer be running. 

                             See technical requirment and implementation details below:

                             -- TEST PLAN --

                             {test_plan}
                             """),

}

def send_prompt(prompt, phase):
    """Send prompt using the appropriate model instance."""
    logging.info(f"Sending prompt using {models[phase].model_name} in {phase} phase")
    logging.info(f"Prompt content: {prompt}")
    
    try:
        model = models[phase]
        
        # Set system prompt if available
        sys_prompt = system_prompts.get(phase)  # Fixed: Using renamed system_prompts
        if sys_prompt:
            model.set_system_prompt(sys_prompt)
            logging.info(f"Using system prompt: {sys_prompt}")
        
        # Send prompt and get response
        response_content = model.prompt(prompt)
        
        logging.info(f"Received response from {model.model_name}")
        logging.info(f"Response content: {response_content}")
        
        return response_content
        
    except Exception as e:
        error_msg = f"Error with API call: {str(e)}"
        logging.error(error_msg)
        raise Exception(error_msg)

def execute_command(command):
    """Extract and execute commands from <cmd> tags in the response."""
    global TARGET_PYTHON

    # Clean up commands a little and ensure using target python version
    if "python" in command:
        command = TARGET_PYTHON + command[command.find('python')+6:]
    elif "pip" in command:
        command = f"{TARGET_PYTHON} -m pip" + command[command.find('pip')+3:]
    
    logging.info(f"Executing command: {command}")
    try:
        process = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = process.stdout + process.stderr
        logging.info(f"Command output below --\n{output}\n")
        return output
    except Exception as e:
        error_msg = str(e)
        result = f"{output}\n\n{error_msg}"
        logging.error(f"Command execution failed - see below --\n{result}\n")
        return result

def planning_phase(repo):
    global final_specs, requirements, test_plan
    resp = None
    logging.info("Starting Planning Phase")
    with console.status(f"[bold blue]Planning phase... | Total API Cost: ${models['planning'].total_api_cost:.2f}[/bold blue]"):  # Fixed: Using correct model key
        with open("user_specs.prompt", 'r') as f:
            user_specs = f.read()
            logging.info("Read user specifications")

        # Generate clean specs from user specs
        prompt = task_prompts['plan_specs'].format(specs=user_specs)
        final_specs = send_prompt(prompt, "planning").raw_text

        # Create project directory and subdirectories, and write final_specs
        os.makedirs(PROJECT_NAME, exist_ok=True)
        final_specs_path = os.path.join(PROJECT_NAME, "final_specs.txt")
        with open(final_specs_path, 'w') as f:
            f.write(final_specs)
            logging.info(f"Wrote final specifications to {final_specs_path}")

        # Generate reqs from specs
        prompt = task_prompts['plan_requirements'].format(specs=final_specs)
        resp = send_prompt(prompt, "planning")
        requirements = {'technical_requirements': resp.props['req']}
        requirements_path = os.path.join(PROJECT_NAME, "technical_requirements.json")
        requirements = json.dumps(requirements, indent=4)
        with open(requirements_path, 'w') as f:
            f.write(json.dumps(requirements, indent=4))
            logging.info(f"Wrote requirements to {requirements_path}")

        # Plan tests
        prompt = task_prompts['plan_tests'].format(reqs=requirements)
        resp = send_prompt(prompt, "planning")
        test_plan = {'test_plan': resp.props['test']}
        test_plan_path = os.path.join(PROJECT_NAME, "test_plan.json")
        test_plan = json.dumps(test_plan, indent=4)
        with open(test_plan_path, 'w') as f:
            f.write(json.dumps(test_plan, indent=4))
            logging.info(f"Wrote test plan to {test_plan_path}")

        sys.exit(0)


def developing_phase(repo, max_retries=3):
    global files, test_files, commands, SRC_DIR
    resp = None
    logging.info("Starting Developing Phase")
    with console.status(f"[bold green]Developing phase... | Total API Cost: ${models['developing'].total_api_cost:.2f}[/bold green]"):
        final_specs_path = os.path.join(PROJECT_NAME, "final_specs.prompt")
        with open(final_specs_path, 'r') as f:
            final_specs = f.read()
            logging.info("Read final specifications")

        # Get prompt response
        attempts = 0
        resp = send_prompt(f"""Using the below specifications as your reference, and following the rules in the system prompt, 
            please provide the source code for the project:\n""" + final_specs, "developing")  # Fixed: Initialize resp before while loop
        
        while attempts < max_retries:  # Fixed: Changed condition to use attempts
            resp = send_prompt(f"""Using the below specifications as your reference, and following the rules in the system prompt, 
            please provide the source code for the project:\n""" + final_specs, "developing")

            # End loop if files are requested
            if len(resp.files) > 0:
                break

            attempts += 1

        files = files + resp.files

        # Execute commands
        for command in resp.commands:
            output = execute_command(command)
            commands.append({
                'command': command,
                'output': output
            })
        
        # Operate on files
        for file_data in resp.files:
            test_file = True if file_data['test_file'].lower() == 'true' else False
            file_name = file_data['file_name']
            file_path = os.path.join(SRC_DIR, file_name)
            file_content = file_data['file_content']
            with open(file_path, 'w') as f:
                f.write(file_content)
                if test_file:
                    test_files.append(file_data)
                else:
                    files.append(file_data)
                logging.info(f"Created/Updated file: {file_path}")

        repo.quick_add(phase="Developing")

def testing_phase(repo):
    global files, commands, SRC_DIR, TEST_FILES_DIR
    resp = None
    logging.info("Starting Testing Phase")
    with console.status(f"[bold yellow]Testing phase... | Total API Cost: ${models['testing'].total_api_cost:.2f}[/bold yellow]"):
        iteration = 1
        
        # Begin the testing and validation loop
        while models['testing'].total_api_cost < 5.00:  # Fixed: Using correct model key
            
            # Test the solution
            logging.info(f"Starting test iteration {iteration}")
            test_path = os.path.join(PROJECT_NAME, "test.py")
            process = subprocess.run([TARGET_PYTHON, test_path], capture_output=True, text=True)
            process_output = process.stdout + process.stderr
            logging.info(f"Test output: {process_output}")  # Fixed: Using process_output instead of output

            # IF ERROR DURING TEST PHASE:
            if process.returncode != 0:
                logging.error(f"Test execution failed with return code {process.returncode}")
                source_files_content = "\nCurrent project source files:\n"
                for file in files:
                    file_name, content = file['file_name'], file['file_content']
                    source_files_content += f"\n--- {file_name} ---\n{content}\n---\n"

                test_files_content = "\nCurrent project test scripts:\n"
                for file in test_files:
                    file_name, content = file['file_name'], file['file_content']
                    test_files_content += f"\n--- {file_name} ---\n{content}\n---\n"
                
                error_prompt = f"""An error occurred while running the test script:
                {process_output}
                {source_files_content}
                {test_files_content}
                Please fix the issue and provide updated source files following the rules in the system prompt."""
                resp = send_prompt(error_prompt, "testing")

                # Execute commands
                for command in resp.commands:
                    output = execute_command(command)
                    commands.append({
                        'command': command,
                        'output': output
                    })

                # Operate on files
                for file_data in resp.files:
                    file_name = file_data['file_name']
                    file_path = os.path.join(SRC_DIR, file_name)
                    file_content = file_data['file_content']
                    with open(file_path, 'w') as f:
                        f.write(file_content)
                        files.append(file_data)  # Fixed: Append file_data instead of files
                        logging.info(f"Created/Updated file: {file_path}")

            # IF NO ERRORS DURING TEST ITERATION; Assess test results...
            else:
                logging.error(f"Test script execution successful - analyzing results...")

                # Get test script content
                test_files_content = ""
                for file in test_files:
                    file_name, content = file['file_name'], file['file_content']
                    test_files_content += f"\n--- {file_name} ---\n{content}\n---\n"

                # Get source files content
                source_files_content = ""
                for file in files:
                    file_name, content = file['file_name'], file['file_content']
                    source_files_content += f"\n--- {file_name} ---\n{content}\n---\n"

                prompt = f"""The below test script(s) ran without error:
                {test_files_content}
                ---
                
                The results of running the test script(s) are below: 
                {process_output}
                ---
                
                Please review the results. If any tests failed, please debug the below code and provide 
                required updates following the rules in the system prompt:
                {source_files_content}
                ---
                
                If on the other hand all the tests passed, you MUST output <ALL_TESTS_PASSED>"""
                resp = send_prompt(prompt, "testing")

                # Make suggested changes and iterate on testing loop
                if '<ALL_TESTS_PASSED>' not in resp.raw_resp_text:  # Fixed: Corrected tag name

                    # Execute commands
                    for command in resp.commands:
                        output = execute_command(command)
                        commands.append({
                            'command': command,
                            'output': output
                        })

                    # Operate on files
                    for file_data in resp.files:
                        file_name = file_data['file_name']
                        file_path = os.path.join(SRC_DIR, file_name)
                        file_content = file_data['file_content']
                        with open(file_path, 'w') as f:
                            f.write(file_content)
                            files.append(file_data)  # Fixed: Append file_data instead of files
                            logging.info(f"Created/Updated file: {file_path}")

                # Code has run and all tests have passed - code's done!
                else:
                    logging.info("All tests passed successfully!")
                    console.print("[bold green]Code successfully generated and passing all required tests![/bold green]")
                    break

            iteration += 1
            repo.quick_add(phase="Testing", message=f"Testing Iteration #{str(iteration)}")

def main():
    global PROJECT_NAME
    
    parser = argparse.ArgumentParser(description='Run the script starting from a specific phase.')
    parser.add_argument('--phase', type=str, default='not_specified',
                      help='Phase to start from (Planning, Developing, Testing)')
    parser.add_argument('--name', type=str, required=True,
                      help='Project name - used for creating project subfolder')

    args = parser.parse_args()
    start_phase = args.phase.lower()
    PROJECT_NAME = args.name
    
    final_specs_path = os.path.join(PROJECT_NAME, "final_specs.prompt")
    dev_dir_path = os.path.join(PROJECT_NAME, "src")

    # Create project subdirectories
    SRC_DIR = os.path.join(PROJECT_NAME, "src")
    TEST_FILES_DIR = os.path.join(PROJECT_NAME, "test_files")
    os.makedirs(SRC_DIR, exist_ok=True)
    os.makedirs(TEST_FILES_DIR, exist_ok=True)

    # Format llm_rules with project-specific values
    formatted_llm_rules = llm_rules.format(TARGET_PYTHON=TARGET_PYTHON, PROJECT_NAME=PROJECT_NAME)
    
    # Update system prompts with formatted rules
    for phase in system_prompts:
        system_prompts[phase] = system_prompts[phase].format(llm_rules=formatted_llm_rules)
    
    if start_phase == "not_specified":
        if os.path.exists(dev_dir_path) and len(os.listdir(dev_dir_path)) > 1:
            console.print(f"[bold orange]**Skipping planning and development - src files exist, and no phase was specified by user...[/bold orange]")
            start_phase = 'testing'
        elif os.path.exists(final_specs_path):
            console.print(f"[bold orange]**Skipping planning - final specifications exist, and no phase was specified by user...[/bold orange]")
            start_phase = 'developing'
        else:
            console.print(f"[bold green]**Proceeding with initial planning - no phase was specified by user[/bold green]")
            start_phase = 'planning'

    if start_phase not in VALID_PHASES:
        error_msg = f"Invalid phase '{args.phase}'. Valid phases are: Planning, Developing, Testing"
        logging.error(error_msg)
        console.print(f"[bold red]Error: {error_msg}[/bold red]")
        return
    
    try:
        logging.info(f"Starting execution from {start_phase} phase")
        # Initialize repo in project directory
        repo_path = os.path.join(PROJECT_NAME, "src")
        r = Repo('proj', path=repo_path)
        r.init()

        if start_phase == 'planning':
            planning_phase(r)
            developing_phase(r)
            testing_phase(r)
        elif start_phase == 'developing':
            developing_phase(r)
            testing_phase(r)
        elif start_phase == 'testing':
            testing_phase(r)

    except Exception as e:
        error_msg = traceback.format_exc()
        logging.error(f"An unexpected error occurred: {error_msg}")
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {error_msg}")

if __name__ == "__main__":
    main()
