import os
import queue
import subprocess
import sys
import tempfile
import time
import shutil
import threading
from queue import Queue

# py -3.9 main.py --name "api_test" --phase "developing"

class ShellThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon=True
        self.input_queue = Queue()
        self.output_queue = Queue()
        self.finished = threading.Event()
        self.terminate = threading.Event()
        self.shell = subprocess.Popen(
            ['cmd.exe'], 
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, 
            text=True
        )

    def run(self):
        while not self.terminate.is_set():
            command = self.input_queue.get()
            if command is None:
                continue
            output = ""
            with tempfile.NamedTemporaryFile(suffix='.bat', delete=False) as bat:
                bat.write(b'@ECHO OFF\n')
                bat.write(bytes(command, encoding='utf-8'))
                bat.write(b'\necho __COMMAND_EXECUTION_COMPLETE__\n')
                bat.write(b'echo.')
                bat_path = bat.name
            self.shell.stdin.write(f"{bat_path}\n")
            self.shell.stdin.flush()
            while not self.terminate.is_set():
                line = self.shell.stdout.readline()
                output += line
                if "__COMMAND_EXECUTION_COMPLETE__" in line:
                    time.sleep(0.5)
                    output = output.replace("__COMMAND_EXECUTION_COMPLETE__", "")
                    os.remove(bat_path)
                    self.output_queue.put(output)
                    self.finished.set()
                    break
                time.sleep(0.2)
        self.shell.terminate()

class Shell:
    def __init__(self, venv_path, python):
        self.proj_src = venv_path
        self.venv_path = os.path.join(self.proj_src, "venv")
        self.interpreter = python
        self.shell_thread = None
        if os.path.exists(self.venv_path):
            shutil.rmtree(self.venv_path)
            print(f"Deleted existing virtual environment at {self.venv_path}")
        self._init_shell()
        self._update_gitignore()

    def _init_shell(self):
        self.shell_thread = ShellThread()
        self.shell_thread.start()
        self._create_venv()
        self._activate_venv()

    def _create_venv(self):
        if not os.path.exists(self.venv_path):
            self.run_shell_command(f"{self.interpreter} -m venv {self.venv_path}")
            print(f"Virtual environment created at {self.venv_path}")
        else:
            print(f"Virtual environment already exists at {self.venv_path}")

    def _update_gitignore(self):
        gitignore_path = self.proj_src + '/.gitignore'
        venv_name = 'venv'
        with open(gitignore_path, 'w') as file:
            file.write(f"{venv_name}\n")
            print(f"Created .gitignore and added {venv_name} to it")

    def _activate_venv(self):
        self.run_shell_command("venv/Scripts/activate.bat")
        print(f"Virtual environment activated at {self.venv_path}")

    def deactivate_venv(self):
        self.run_shell_command("deactivate")

    def kill_shell(self):
        self.shell_thread.terminate.set()
        self.shell_thread.input_queue.put("echo DIE MOFO!")
        self.shell_thread.join(timeout=5)

    def run_shell_command(self, command, timeout=20):
        self.shell_thread.finished.clear()
        self.shell_thread.input_queue.put(command)
        start_time = time.time()
        output = ""
        while not self.shell_thread.finished.is_set():
            if time.time() - start_time > timeout:
                self.shell_thread.terminate.set()
                output += f"\n USER: Command did not complete in under {timeout} seconds... " \
                          +"See output above for evidence."
                self.shell_thread.join(timeout=5)
                if self.shell_thread.is_alive():
                    self.shell_thread.shell.kill()
                    self.shell_thread.shell.wait()
                    output += "\n USER: Command was forcefully terminated after 5 seconds."
                else:
                    output += f"\n USER: Command terminated cleanly."
                break
            try:
                output += self.shell_thread.output_queue.get(timeout=0.2)
            except queue.Empty:
                continue

        return output

    def generate_requirements(self):
        requirements_file = 'requirements.txt'
        with open(requirements_file, 'w') as fout:
            fout.write(self.run_shell_command("venv/Scripts/pip freeze"))
        print(f"requirements file generated: {requirements_file}")
