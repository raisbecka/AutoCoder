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
def handle_sigint(signum, frame):
    print("Ctrl+C detected. Performing cleanup...")
    config.handlers['cmd'].venv.kill_shell()


# Parse command-line args and setup & return context/state config
def init_project(ctx):
    
    # Handle ctrl+c nicely
    signal.signal(signal.SIGINT, handle_sigint)
    
    parser = argparse.ArgumentParser(description='Run the script starting from a specific phase.')
    parser.add_argument('--phase', type=str, default='not_specified',
                      help='Phase to start from (Planning, Developing, Testing)')
    parser.add_argument('--name', type=str, required=True,
                      help='Project name - used for creating project subfolder')

    args = parser.parse_args()

    # Update project name config
    config.project_name = args.name
    config.project_root = f"projects/{config.project_name}"

    # Create projects directory
    proj_dir = os.path(config.project_root)
    if not proj_dir.exists():
        os.makedirs(proj_dir, exist_ok=False)

    # Create project subdirectories
    src_dir = os.path.join(config.project_root, config.src_dir)
    if not src_dir.exists():
        os.makedirs(src_dir, exist_ok=False)

    test_file_dir = os.path.join(config.project_root, config.test_file_dir)
    if not test_file_dir.exists():
        os.makedirs(test_file_dir, exist_ok=False)

    # Initialize repo for project
    repo = Repo('proj', path=f"{config.project_root}/{config.src_dir}")
    repo.init()

    # Add commit action to post-task callback on all Agents
    Agent.on_task_complete = repo.quick_add


if __name__=='__main__':

    # Initialize rich Console
    console = Console()

    # Handle command-line args and init project
    init_project()

    # Read in user specs
    with open("user_specs_example.txt", 'r') as f:
        user_specs = f.read()

    try:

        # Start planning
        if not planning_phase.is_complete:
            data = planning_phase.run({'specs': user_specs})
        
        # Start development

    except Exception as e:
        error_msg = traceback.format_exc()
        logging.error(f"An unexpected error occurred: {error_msg}")
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {error_msg}")
        print("Killing shell...")
        config.handlers['cmd'].venv.kill_shell()
        sys.exit(-1)