from textwrap import dedent
import signal
import sys
import argparse
import traceback
import os
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler
from dotenv import load_dotenv
from datetime import datetime
from lib import Agent, config
from configs.phases.planning import planning_phase
from configs.phases.development import development_phase
from configs.phases.testing import testing_phase
from lib import Repo
import logging
logger = logging.getLogger(__name__)
logger.propagate = True

console = Console()

# Load environment variables from .env file
load_dotenv()

# Terminate execution nicely
def terminate_and_cleanup(signum=None, frame=None):
    print("Ctrl+C detected. Performing cleanup...")
    if config.handlers['cmd'].venv:
        config.handlers['cmd'].venv.kill_shell()
    sys.exit(0)


def init_logging(args):
    global console, logger

    # Setup directory structure for logging
    os.makedirs('logs', exist_ok=True)
    for f in os.listdir('logs'):
        if f.endswith('.log'):
            os.remove(os.path.join('logs', f))
    
    # Log levels 
    log_level_map = {
        "info": logging.INFO,
        "error": logging.ERROR,
        "debug": logging.DEBUG,
        "warning": logging.WARNING
    }

    # Set up logging at specified level
    log_file_name = f'logs/model_interactions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    logging.basicConfig(
        filename=log_file_name,
        level=log_level_map[args.log_level.lower()],
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Enable rich console logger if requested
    if args.log_to_console:
        rich_handler = RichHandler(console=console, show_time=True, show_level=True, markup=True)
        logger.addHandler(rich_handler)
        logger.debug("Outputting log to console.")


# Parse command-line args and setup & return context/state config
def init_project():
    
    # Handle ctrl+c nicely
    signal.signal(signal.SIGINT, terminate_and_cleanup)
    
    parser = argparse.ArgumentParser(description='Run the script starting from a specific phase.')
    parser.add_argument('--phase', type=str, default='not_specified',
                      help='Phase to start from (Planning, Developing, Testing)')
    parser.add_argument('--name', type=str, required=True,
                      help='Project name - used for creating project subfolder')
    parser.add_argument('--log-to-console', action='store_true', default=False,
                      help='Output log to console in addition to log file')
    parser.add_argument('--log-level', type=str, required=False, default="INFO",
                      help='Used to set the logger level')    
    args = parser.parse_args()

    init_logging(args)

    logger.debug(f"Command-line arguments parsed: {args}")

    # Update project name config
    config.set_project_name(args.name)

    # Update starting phase config
    config.current_phase = args.phase.lower()

    # Create projects directory
    proj_dir = Path(config.project_root)
    if not proj_dir.exists():
        os.makedirs(proj_dir, exist_ok=False)
        logger.debug(f"Project directory created: {config.project_root}")

    # Create project subdirectories
    src_dir = Path(f"{config.project_root}/{config.src_dir}")
    if not src_dir.exists():
        os.makedirs(src_dir, exist_ok=False)
        logger.debug(f"Source directory created: {os.path.join(config.project_root, config.src_dir)}")

    test_file_dir = Path(f"{config.project_root}/{config.test_file_dir}")
    if not test_file_dir.exists():
        os.makedirs(test_file_dir, exist_ok=False)
        logger.debug(f"Test file directory created: {os.path.join(config.project_root, config.test_file_dir)}")

    # Initialize repo for project
    repo = Repo('proj', path=f"{config.project_root}/{config.src_dir}")
    repo.init()
    logger.debug(f"Repository initialized at: {config.project_root}/{config.src_dir}")

    # Add commit action to post-task callback on all Agents
    #Agent.on_task_complete = lambda : repo.quick_add(config.current_phase)


if __name__=='__main__':

    # Handle command-line args and init project
    init_project()

    # Holds the generated session/context data that the Agents pass back and forth
    data = {}

    try:
        
        # Read in user specs
        logger.debug("Reading user specs...")
        with open("user_specs_test.txt", 'r') as f:
            user_specs = f.read()
        data['specs'] = user_specs

        logger.debug(f"User specs read. See below --- \n{user_specs}")

        # Start Planning
        if config.current_phase in ['plan', 'planning']:
            if not planning_phase.is_complete():
                logger.info("Starting planning phase...")
                data = planning_phase.run(**data)
            else:
                logger.info("Planning phase already completed; loading data...")
                data = planning_phase.load_data(data) | data
            config.current_phase = 'development'

        # Start Developing
        if config.current_phase in ['development', 'developing']:
            if not development_phase.is_complete():
                logger.info("Starting development phase...")
                data = development_phase.run(**data) | data
            else:
                logger.info("Development phase already completed; loading data...")
                data = development_phase.load_data(data) | data
            config.current_phase = 'testing'
        
        # Start Testing
        if config.current_phase in ['test', 'testing']:
            if not testing_phase.is_complete():
                logger.info("Starting testing phase...")
                print(data)
                data = testing_phase.run(**data) | data
            config.current_phase = 'complete'

    except Exception as e:
        error_msg = traceback.format_exc()
        logger.error(f"An unexpected error occurred: {error_msg}")
        terminate_and_cleanup()

    logger.info("Script execution finished.")
