import json
from typing import Dict, Any, Optional, List
from lib import Handler, Shell
from lib import config
from pydantic import ValidationError
import sys
import os
import logging
logger = logging.getLogger(__name__)
logger.propagate = True

# Data element handler
class DataHandler(Handler):

    def __init__(
            self,
            title: str,
            file_name: str,
            dir: str = None,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.title = title
        self.file_name = file_name
        self.dir = dir
        logger.debug(f"DataHandler initialized with title: {self.title}, file_name: {self.file_name}")

    # Write element items to file using handler
    def process(self, items):
        try:
            # Validate all items first
            for item in items:
                self.element.model_validate(item)

            logger.info(f"Processing data with DataHandler: {self.title}")
            if self.dir:
                file_path = f"{config.project_root}/{self.dir}/{self.file_name}"
            else:
                file_path = f"{config.project_root}/{self.file_name}"
            data = {self.title: items}
            with open(file_path, 'w', encoding="utf-8") as f:
                output = json.dumps(data, indent=4)
                f.write(output)
            logger.info(f"Data written to file: {file_path}")
            return {self.title: items}
        except ValidationError as e:
            logger.error(f"Error processing data with DataHandler: {e}")
            raise


# File (tool) element handler
class FileHandler(Handler):

    def __init__(
            self,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        logger.debug(f"FileHandler initialized")

    def process(self, items):
        logger.info(f"Processing files with FileHandler")
        try:
            # Validate all items first
            for item in items:
                self.element.model_validate(item)

            logger.debug(f"Validated file elements")
            return_val = {
                'files': items
            }
            for item in items:
                file_name = item['file_name']
                file_content = item['file_content']
                print(config.project_root, config.project_name)
                with open(f"{config.project_root}/{config.src_dir}/{file_name}", "w") as fout:
                    fout.write(file_content)
                logger.info(f"File written: {file_name}")
            return return_val
        except Exception as e:
            logger.error(f"Error processing files with FileHandler: {e}")
            raise


# Command (tool) element handler
class CommandHandler(Handler):

    # Only hold a single terminal open for the entire execution
    venv: Shell = None

    def __init__(
            self,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        logger.debug(f"CommandHandler initialized")

    def init_shell(self):
        if not CommandHandler.venv:
            logger.info("Initializing shell for CommandHandler")
            CommandHandler.venv = Shell(
                venv_path=f"{config.project_root}/{config.src_dir}/", 
                python=config.python_version
            )
            logger.debug(f"Shell initialized with venv_path: {config.project_root}/{config.src_dir}/, python: {config.python_version}")

    # Clean up commands a little and ensure using target python version
    def clean_command(self, cmd):
        logger.debug(f"Cleaning command: {cmd}")
        if "python" in cmd:
            cleaned_cmd = config.python_version + cmd[cmd.find('python')+6:]
            logger.debug(f"Cleaned command: {cleaned_cmd}")
            return cleaned_cmd
        elif "pip" in cmd:
            cleaned_cmd = f"{config.python_version} -m pip" + cmd[cmd.find('pip')+3:]
            logger.debug(f"Cleaned command: {cleaned_cmd}")
            return cleaned_cmd
        logger.debug(f"Command does not need cleaning: {cmd}")
        return cmd

    def process(self, items):

        #TODO: PUT THIS BACK!
        return_val = {
            'commands': items
        }
        return return_val
        '''
        logger.info(f"Processing commands with CommandHandler")
        try:
            self.init_shell()
            # Validate all items first
            for item in items:
                self.element.model_validate(item)
            logger.debug(f"Validated console command elements")
            for item in items:
                logger.debug(f"Running command: {item['command']}")
                item['output'] = CommandHandler.venv.run_shell_command(
                    self.clean_command(item['command'])
                )
                logger.debug(f"Command output: {item['output']}")
            return_val = {
                'commands': items
            }
            return return_val
        except Exception as e:
            logger.error(f"Error processing commands with CommandHandler: {e}")
            raise
        '''
