from textwrap import dedent
import signal
import sys
import argparse
import traceback
import os
import logging
from rich.console import Console
from dotenv import load_dotenv
from datetime import datetime
from lib import Agent, config
from lib.models import VLLM
from configs.phases.planning import planning_phase
from lib import Repo

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


# Terminate execution nicely
def terminate_and_cleanup(signum=None, frame=None):
    print("Ctrl+C detected. Performing cleanup...")
    if config.handlers['cmd'].venv:
        config.handlers['cmd'].venv.kill_shell()


# Parse command-line args and setup & return context/state config
def init_project():
    
    # Handle ctrl+c nicely
    signal.signal(signal.SIGINT, terminate_and_cleanup)
    
    parser = argparse.ArgumentParser(description='Run the script starting from a specific phase.')
    parser.add_argument('--phase', type=str, default='not_specified',
                      help='Phase to start from (Planning, Developing, Testing)')
    parser.add_argument('--name', type=str, required=True,
                      help='Project name - used for creating project subfolder')

    args = parser.parse_args()
    logging.debug(f"Command-line arguments parsed: {args}")

    # Update project name config
    config.project_name = args.name
    config.project_root = f"projects/{config.project_name}"

    # Create projects directory
    proj_dir = os.path(config.project_root)
    if not proj_dir.exists():
        os.makedirs(proj_dir, exist_ok=False)
        logging.debug(f"Project directory created: {config.project_root}")

    # Create project subdirectories
    src_dir = os.path.join(config.project_root, config.src_dir)
    if not src_dir.exists():
        os.makedirs(src_dir, exist_ok=False)
        logging.debug(f"Source directory created: {os.path.join(config.project_root, config.src_dir)}")

    test_file_dir = os.path.join(config.project_root, config.test_file_dir)
    if not test_file_dir.exists():
        os.makedirs(test_file_dir, exist_ok=False)
        logging.debug(f"Test file directory created: {os.path.join(config.project_root, config.test_file_dir)}")

    # Initialize repo for project
    repo = Repo('proj', path=f"{config.project_root}/{config.src_dir}")
    repo.init()
    logging.debug(f"Repository initialized at: {config.project_root}/{config.src_dir}")

    # Add commit action to post-task callback on all Agents
    Agent.on_task_complete = repo.quick_add


if __name__=='__main__':

    # Initialize rich Console
    console = Console()
    logging.info("Script execution started.")

    try:
        # Handle command-line args and init project
        init_project()

        # Read in user specs
        logging.debug("Reading user specs...")
        with open("user_specs_example.txt", 'r') as f:
            user_specs = f.read()
        logging.debug(f"User specs read. See below --- \n{user_specs}")

        # Start planning
        if not planning_phase.is_complete:
            logging.info("Starting planning phase...")
            data = planning_phase.run({'specs': user_specs})
            logging.info("Planning phase completed.")
        
        # Start development
        pass

    except Exception as e:
        error_msg = traceback.format_exc()
        logging.error(f"An unexpected error occurred: {error_msg}")
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {error_msg}")
        terminate_and_cleanup()
    logging.info("Script execution finished.")
