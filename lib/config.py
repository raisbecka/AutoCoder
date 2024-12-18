from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from lib.handler import Handler
from lib.element import Element

@dataclass
class Config:

    # Project Settings 
    project_name: str = 'untitled_project'
    project_root: str = f'projects/{{project_name}}'
    python_version: str = 'python'
    test_file_dir: str = 'test_files'
    src_dir: str = 'src'

    start_phase: str = 'planning'

    # Element handler assignments
    handlers: Dict[str, Handler] = None

config = Config()
