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
import asyncio
from models import Claude, Gemini, GPT, O1, Ollama, VLLM

# Load environment variables from .env file
load_dotenv()

# Set up logging
os.makedirs('logs', exist_ok=True)
for f in os.listdir('logs'):
    if f.endswith('.log'):
        os.remove(os.path.join('logs', f))
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
        'company': 'vllm',#'ollama',#'openai',
        'model': 'Qwen/Qwen2.5-Coder-32B-Instruct'#'qwen2.5-coder:32b-instruct-q4_K_M'#'gpt-4o'
    },
    'developing': {
        'company': 'vllm',#'ollama',#'openai',
        'model': 'Qwen/Qwen2.5-Coder-32B-Instruct'#'qwen2.5-coder:32b-instruct-q4_K_M'#'gpt-4o'
    },
    'testing': {
        'company': 'ollama',#'anthropic',
        'model': 'qwen2.5-coder:32b-instruct-q4_K_M'#'claude-3-5-sonnet-latest'
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
    elif config['company'] == 'ollama': 
        models[phase] = Ollama(config['model'])
    elif config['company'] == 'vllm': 
        models[phase] = VLLM(config['model'])

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
    'developing': """
        You are an experienced full-stack software developer specializing in writing clean, well-documented Python code. 
        You will be asked to develop a solution spanning one or more source files that adheres to a provided project specification. 
        
        Ensure you adhere to the rules below:
        {rules}""",
    'testing': """You are an experienced full-stack software developer specializing in writing clean, well-documented Python code. 
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

    'plan_requirements': dedent("""Take the below technical specifications, and write a numbered list of clear, concise technical requirements as 
                                    you would for a software developer. Take your time, and be as detailed as possible. For each requirement, 
                                    format it like below:
                                
                                    <req><req_id>ID</req_id><details>DETAILS</details></req> 
                                
                                    ...where ID cooresponds to the numbered ID of that requirement (just an integer - no alpha characters), and 
                                    DETAILS cooresponds to the details of that requirement.

                                    It is absolutely essential that each requirement maps directly to the below text, and no requirements are missed.
                                    Following this set of requirements should result in exactly what is described below - nothing more, nothing less.
                                    -- SPECS BELOW --

                                    {specs}
                                    """),

    'expand_requirements': dedent("""For the high-level technical requirments below, expand on each - including as much details as possible. This should
                                    include an inplementation example detailing how the code could be written to handle this requirement. The expanded,
                                    detailed requirements should include everything that a junior software developer would need to know to implement
                                    the requirement. Take your time, and be as detailed as possible - including any specific frameworks, protocols, 
                                    principles, or approaches that are used. For each requirement, format it like below:
                                
                                    <req><req_id>ID</req_id><details>DETAILS</details><implementation_details>IMP_EX</implementation_details></req> 
                                
                                    ...where ID cooresponds to the numbered ID of that requirement (just an integer - no alpha characters), DETAILS 
                                    cooresponds to the details of that requirement, and IMP_EX cooresponds to the implementation example code for 
                                    the requirement.
                                  
                                    For each detailed, expanded requirement, the ID MUST match the previous ID of the associated, below high-level 
                                    requirement.                                

                                    -- SPECS BELOW --

                                    {requirements}
                                    """),

    'plan_tests': dedent("""Take the below technical requirements, and write a detailed, numbered list of test cases that cover all of the different
                         types of user interaction that may occur - ensuring that the outcome in each case conforms to the technical requirements.
                         You may write 1 or more tests for each requirement. Each test must include the requirement that it maps to, the details of 
                         the test, and the expected result of the test. For each test, format it like below:

                         <test>
                            <test_id>TID</test_id>
                            <req_id>RID</req_id>
                            <test_details>DETAILS</test_details>
                            <test_data>
                                <file_name>FILENAME</file_name>
                                <file_description>FILE_DESCRIPTION</file_description>
                            </test_data>
                            <expected_result>RESULT</expected_result>
                         </test>

                         ... where TID cooresponds to the numbered ID of that test, ID cooresponds to the numbered ID of the related requirement,
                         DETAILS cooresponds to the details of that test, RESULT cooresponds to the expected result of that test. Also, zero or 
                         more test files can be used for each test as required to simulate user interactions or data flow. 
                         
                         For the test_data elements, these are files that are meant to be used to simulate data flow or user interaction for the 
                         test case ONLY IF the data cannot be programmatically generated during the test. For example, if a specific video file is 
                         required in order to run a test. Some tests may not require test data (for example, pinging a server), and in this case a 
                         test file is obviously not required. Also, if the test data can be generated by the test case/script, then a test data file
                         is not required also. 
                         
                         If a test data file is needed though, FILENAME should coorespond to the name of the test data file, and FILE_DESCRIPTION 
                         should coorespond to a description of what that file is to be used for (what kind of data and/or interaction to simulate or 
                         test).

                         If no test data files are required, do NOT include this element along with the rest of the elements.

                        -- REQUIREMENTS BELOW --
                         
                        {reqs}
                        """),

    'generate_code': dedent("""Take the below technical specifications, and write Python code that satisfies all of them - ensuring that
                            the code follows best practises, is well documented, and a comment is left for each technical requirement in the code mapping
                            the requirement to the relevent code (using the requirement ID). The source code can span multiple files if necessary:

                        -- SPECIFICATIONS BELOW --
                        
                        {specs}
                        """), 

    'validate_requirements': dedent("""Provided the below technical requirements, your task is to ensure that the requirements are properly addressed,
                                    and implemented in one or more source code files. You must adhere to the following format with your response:

                                    <req><req_id>ID</req_id><implementation_details>DETAILS</implementation_details><requirement_satisfied>YESORNO</requirement_satisfied></req>

                                    ...where ID cooresponds to the numbered ID of that requirement (just an integer - no alpha characters), DETAILS 
                                    cooresponds to a short description (2 or 3 sentences max) of how the requirement was implemented, and YESORNO is either
                                    TRUE if the requirement is satisfied in the code, or FALSE if it is not.

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
        sys_prompt = system_prompts.get(phase)
        if sys_prompt:
            model.set_system_prompt(sys_prompt)
            logging.info(f"Using system prompt: {sys_prompt}")
        
        # Send prompt and get response
        response_content = model.prompt(prompt)
        
        logging.info(f"Received response from {model.model_name}")
        logging.info(f"Response content: {response_content.raw_text}")
        
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
    
def update_step(text):
    logging.info(text)
    console.print(f"[bold cyan]{text}[/bold cyan]")

def planning_phase(repo, detailed=False):
    global final_specs, requirements, test_plan
    resp = None
    
    # Initiate planning phase
    update_step("Starting Planning Phase")

    # Read in user specs
    with open("user_specs.prompt", 'r') as f:
        user_specs = f.read()
        update_step("Read user specifications")

    # Create project directory
    os.makedirs(PROJECT_NAME, exist_ok=True)

    # Check for existing final specs
    final_specs_path = os.path.join(PROJECT_NAME, "final_specs.txt")
    if os.path.exists(final_specs_path):
        with open(final_specs_path, 'r', encoding="utf-8") as f:
            final_specs = f.read()
            update_step(f"Read existing final specifications from {final_specs_path}")
    else:
        # Generate clean specs from user specs
        prompt = task_prompts['plan_specs'].format(specs=user_specs)
        final_specs = send_prompt(prompt, "planning").raw_text
        
        # Write final specs
        with open(final_specs_path, 'w', encoding="utf-8") as f:
            f.write(final_specs)
            update_step(f"Wrote final specifications to {final_specs_path}")

    # Check for existing requirements
    requirements_path = os.path.join(PROJECT_NAME, "technical_requirements.json")
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding="utf-8") as f:
            requirements = f.read()
            update_step(f"Read existing requirements from {requirements_path}")
    else:
        
        # Generate high-level reqs from specs
        prompt = task_prompts['plan_requirements'].format(specs=final_specs)
        resp = send_prompt(prompt, "planning")
        requirements = {'technical_requirements': resp.props['req']}

        # Expand on requirements 4 at a time to get greater details for whole list
        expanded_requirements = []
        req_chunk_size = 4
        requirements = resp.props['req']

        if detailed:
            for i in range(0, len(requirements), req_chunk_size):
                try:
                    requirement_chunk = {'requirements': json.dumps(requirements[i:i+4], indent=4)}
                except:
                    requirement_chunk = {'requirements': json.dumps(requirements[i:], indent=4)}

                # Generate low-level reqs from specs
                prompt = task_prompts['expand_requirements'].format(requirements=requirement_chunk)
                resp = send_prompt(prompt, "planning")
                requirements = expanded_requirements + resp.props['req']

        # Write detailed requirements to file
        requirements = {'requirements': requirements}
        with open(requirements_path, 'w', encoding="utf-8") as f:
            f.write(json.dumps(requirements, indent=4))
            update_step(f"Wrote requirements to {requirements_path}")

    # Check for existing test plan
    test_plan_path = os.path.join(PROJECT_NAME, "test_plan.json")
    if os.path.exists(test_plan_path):
        with open(test_plan_path, 'r', encoding="utf-8") as f:
            test_plan = f.read()
            update_step(f"Read existing test plan from {test_plan_path}")
    else:
        # Plan tests
        prompt = task_prompts['plan_tests'].format(reqs=requirements)
        resp = send_prompt(prompt, "planning")
        test_plan = {'test_plan': resp.props['test']}
        test_plan = json.dumps(test_plan, indent=4)
        with open(test_plan_path, 'w', encoding="utf-8") as f:
            f.write(test_plan)
            update_step(f"Wrote test plan to {test_plan_path}")


def developing_phase(repo, max_retries=3):
    global final_specs, requirements, test_plan
    resp = None
    
    # Initiate planning phase
    update_step("Starting Developing Phase")

    # Read in final specs
    final_specs_path = os.path.join(PROJECT_NAME, "final_specs.txt")
    if os.path.exists(final_specs_path):
        with open(final_specs_path, 'r', encoding="utf-8") as f:
            final_specs = f.read()
            update_step(f"Read existing final specifications from {final_specs_path}")

    # Read in requirements 
    requirements_path = os.path.join(PROJECT_NAME, "technical_requirements.json")
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding="utf-8") as f:
            requirements = f.read()
            update_step(f"Read existing requirements from {requirements_path}")

    # Generate high-level reqs from specs
    prompt = task_prompts['generate_code'].format(specs=final_specs)
    resp = send_prompt(prompt, "developing")
    
    # Execute commands
    for command in resp.props['cmd']:
        output = execute_command(command)
        commands.append({
            'command': command,
            'output': output
        })
        #TODO: Maybe add validation prompt here? Dunno.

    # Operate on files
    for file_data in resp.props['file']:
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

    # Commit changes to repo
    repo.quick_add(phase="Developing")

    # Now, go through requirements list x items at once, and vaidate they are implemented
    missing = []
    analyzed = []
    req_chunk_size = 5
    for i in range(0, len(requirements), req_chunk_size):
        try:
            requirement_chunk = {'requirements': json.dumps(requirements[i:i+req_chunk_size], indent=4)}
        except:
            requirement_chunk = {'requirements': json.dumps(requirements[i:], indent=4)}

        # Generate low-level reqs from specs
        prompt = task_prompts['validate_requirements'].format(requirements=requirement_chunk)
        resp = send_prompt(prompt, "planning")
        for req in resp.props['req']:
            status = req['requirement_satisfied'].upper()
            if 'YES' in status or 'TRUE' in status:
                analyzed.append(req)
            else:
                missing.append(req)

    if len(missing) > 0:
        print("FUCK NUGGETS!")

    imp_details_path = os.path.join(PROJECT_NAME, "implementation_details.json")
    imp_details = {'implementation_details': resp.props['req']}
    imp_details = json.dumps(imp_details, indent=4)
    with open(imp_details_path, 'w', encoding="utf-8") as f:
        f.write(imp_details)
        update_step(f"Wrote test plan to {imp_details_path}")

    sys.exit(0)

    #TODO: Add code for writing tests in test.py...

async def testing_phase(repo):
    global files, commands, SRC_DIR, TEST_FILES_DIR
    resp = None
    logging.info("Starting Testing Phase")
    with console.status(f"[bold yellow]Testing phase... | Total API Cost: ${models['testing'].total_api_cost:.2f}[/bold yellow]"):
        iteration = 1
        
        # Begin the testing and validation loop
        while models['testing'].total_api_cost < 5.00:
            
            # Test the solution
            logging.info(f"Starting test iteration {iteration}")
            test_path = os.path.join(PROJECT_NAME, "test.py")
            process = subprocess.run([TARGET_PYTHON, test_path], capture_output=True, text=True)
            process_output = process.stdout + process.stderr
            logging.info(f"Test output: {process_output}")

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
                resp = await send_prompt(error_prompt, "testing")

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
                        files.append(file_data)
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
                resp = await send_prompt(prompt, "testing")

                # Make suggested changes and iterate on testing loop
                if '<ALL_TESTS_PASSED>' not in resp.raw_text:

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
                            files.append(file_data)
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
    
    test_plan_path = os.path.join(PROJECT_NAME, "test_plan.json")
    dev_dir_path = os.path.join(PROJECT_NAME, "src")

    # Create project subdirectories
    SRC_DIR = os.path.join(PROJECT_NAME, "src")
    TEST_FILES_DIR = os.path.join(PROJECT_NAME, "test_files")
    os.makedirs(SRC_DIR, exist_ok=True)
    os.makedirs(TEST_FILES_DIR, exist_ok=True)

    # Format llm_rules with project-specific values
    formatted_llm_rules = rules.format(TARGET_PYTHON=TARGET_PYTHON, PROJECT_NAME=PROJECT_NAME)
    
    # Update system prompts with formatted rules
    for phase in list(system_prompts.keys()):
        prompt = system_prompts[phase].format(rules=formatted_llm_rules)
        system_prompts[phase] = prompt
    
    if start_phase == "not_specified":
        if os.path.exists(dev_dir_path) and len(os.listdir(dev_dir_path)) > 1:
            console.print(f"[bold orange]**Skipping planning and development - src files exist, and no phase was specified by user...[/bold orange]")
            start_phase = 'testing'
        elif os.path.exists(test_plan_path):
            console.print(f"[bold yellow]**Skipping planning - test cases exist, and no phase was specified by user...[/bold yellow]")
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
