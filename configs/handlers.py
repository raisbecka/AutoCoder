import json
from typing import Dict, Any, Optional, List
from lib import Handler, Shell
from configs.project import config
import sys
import os
import logging

# Data element handler
class DataHandler(Handler):

    def __init__(
            self,
            title: str,
            file_name: str,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.title = title,
        self.file_name = file_name
        logging.debug(f"DataHandler initialized with title: {self.title}, file_name: {self.file_name}")

    # Write element items to file using handler
    def process(self, items):
        logging.info(f"Processing data with DataHandler: {self.title}")
        try:
            items = self.element.create_elements(items)
            logging.debug(f"Created elements: {items}")
            return_val = {self.title: str(items)}
            file_path = f"{config.project_root}/{self.file_name}"
            with open(file_path, 'w', encoding="utf-8") as f:
                f.write(json.dumps(return_val, indent=4))
            logging.info(f"Data written to file: {file_path}")
            return return_val
        except Exception as e:
            logging.error(f"Error processing data with DataHandler: {e}")
            raise


# File (tool) element handler
class FileHandler(Handler):

    def __init__(
            self,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        logging.debug(f"FileHandler initialized")

    def process(self, items):
        logging.info(f"Processing files with FileHandler")
        try:
            items = self.element.create_elements(items)
            logging.debug(f"Created file elements: {items}")
            return_val = {
                'files': items
            }
            for idx in range(len(items)):
                data = self.items[idx]
                file_name = data['file_name']
                file_content = data['file_content']
                with open(f"{config.project_root}/{config.src_dir}/{file_name}", "w") as fout:
                    fout.write(file_content)
                logging.info(f"File written: {file_name}")
            return return_val
        except Exception as e:
            logging.error(f"Error processing files with FileHandler: {e}")
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
        logging.debug(f"CommandHandler initialized")

    def init_shell(self):
        if not CommandHandler.venv:
            logging.info("Initializing shell for CommandHandler")
            CommandHandler.venv = Shell(
                venv_path=f"{config.project_root}/{config.src_dir}/", 
                python=config.python_version
            )
            logging.debug(f"Shell initialized with venv_path: {config.project_root}/{config.src_dir}/, python: {config.python_version}")

    # Clean up commands a little and ensure using target python version
    def clean_command(self, cmd):
        logging.debug(f"Cleaning command: {cmd}")
        if "python" in cmd:
            cleaned_cmd = config.python_version + cmd[cmd.find('python')+6:]
            logging.debug(f"Cleaned command: {cleaned_cmd}")
            return cleaned_cmd
        elif "pip" in cmd:
            cleaned_cmd = f"{config.python_version} -m pip" + cmd[cmd.find('pip')+3:]
            logging.debug(f"Cleaned command: {cleaned_cmd}")
            return cleaned_cmd
        logging.debug(f"Command does not need cleaning: {cmd}")
        return cmd

    def process(self, items):
        logging.info(f"Processing commands with CommandHandler")
        try:
            self.init_shell()
            items = self.element.create_elements(items)
            logging.debug(f"Created command elements: {items}")
            return_val = {
                'commands': items
            }
            for i in range(len(self.items)):
                logging.debug(f"Running command: {self.items[i].value}")
                self.items[i].output = CommandHandler.venv.run_shell_command(
                    self.clean_command(self.items[i].value)
                )
                logging.debug(f"Command output: {self.items[i].output}")
            return return_val
        except Exception as e:
            logging.error(f"Error processing commands with CommandHandler: {e}")
            raise
