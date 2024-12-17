from textwrap import dedent
import os
import sys
import shellingham
import platform
from pathlib import Path
from lib.config import config

class Env:

    # Variables for subbing in env data to the system prompt
    FULL_PATH_CWD = os.path.dirname(os.path.realpath(__file__))
    CWD = os.getcwd()
    OS_NAME = platform.system()
    OS_RELEASE = platform.release()
    OS_TYPE = os.name
    HOME_DIR = Path.home()

    # Try detect shell name - if fails, use system-based defaults as guesses
    try:
        SHELL_NAME = shellingham.detect_shell()
    except shellingham.ShellDetectionFailure:
        if OS_NAME == 'Linux':
            SHELL_NAME = 'sh'
        elif OS_NAME == 'Darwin':
            SHELL_NAME = 'zsh'
        else:
            SHELL_NAME = 'cmd'

    # Prints a summary of the current working environment for the LLM
    @staticmethod
    def summary():
        return dedent(f""" 
        <environment_info>
            Operating System: {Env.OS_NAME} - {Env.OS_RELEASE} ({Env.OS_TYPE})
            Default Shell: {Env.SHELL_NAME}
            Home Directory: {Env.HOME_DIR}
            Current Working Directory: {Env.CWD}
            Project Sub-Directory: {config.project_root}
        </environment_info>
    """)