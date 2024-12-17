import json
from typing import Dict, Any, Optional, List
from lib import Handler, Shell
from configs.project import config
import sys
import os

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

    # Write element items to file using handler
    def process(self, items):
        items = self.element.create_elements(items)
        file_path = os.path.join(config.project_name, self.file_name)
        return_val = {self.title: str(items)}
        with open(f"{config.project_root}/{file_path}", 'w', encoding="utf-8") as f:
            f.write(json.dumps(return_val, indent=4))
        return return_val


# File (tool) element handler
class FileHandler(Handler):

    def __init__(
            self,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)

    def process(self, items):
        items = self.element.create_elements(items)
        return_val = {
            'files': items
        }
        for idx in range(len(items)):
            data = self.items[idx]
            file_name = data['file_name']
            file_content = data['file_content']
            with open(f"{config.project_root}/{config.src_dir}/{file_name}", "w") as fout:
                fout.write(file_content)
        return return_val
        


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

    def init_shell(self):
        if not CommandHandler.venv:
            CommandHandler.venv = Shell(
                venv_path=f"{config.project_root}/{config.src_dir}/", 
                python=config.python_version
            )

    # Clean up commands a little and ensure using target python version
    def clean_command(self, cmd): 
        if "python" in cmd:
            return config.python_version + cmd[cmd.find('python')+6:]
        elif "pip" in cmd:
            return f"{config.python_version} -m pip" + cmd[cmd.find('pip')+3:]

    def process(self, items):
        self.init_shell()
        items = self.element.create_elements(items)
        return_val = {
            'commands': items
        }
        for i in range(len(self.items)):
            self.items[i].output = CommandHandler.venv.run_shell_command(
                self.clean_command(self.items[i].value)
            )
        return return_val
        
