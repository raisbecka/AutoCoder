import logging
import subprocess
import os
import sys
import shlex

class Repo:

    def __init__(self, name, path):
        """Initialize a new git repository with the given name"""
        logging.debug(f"Initializing Repo instance with name: {name}, path: {path}")
        self.name = name
        self.path = path
        self.pending_main_branch = True
        
        # Blow away existing git repo and start fresh
        try:
            os.remove('src/.git')
        except OSError:
            pass
        logging.debug(f"Repo instance initialized")

    def init(self):
        logging.debug("Initializing git repo")
        # Initialize git repo
        self.run_command(f"git -C {self.path} init")
        logging.debug("Git repo initialized")
    
    def run_command(self, command):
        """Utility method to run git commands"""
        logging.debug(f"Running git command: {command}")
        command = command.replace('\\', '/')

        try:
            process = subprocess.Popen(
                shlex.split(command),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            output, error = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Command failed: {error.decode()}")
            process.terminate()
            logging.debug(f"Git command completed: {command}, output: {output}")    
            return output.decode()
        except Exception as e:
            logging.error(f"Error running command '{command}': {str(e)}")
            raise Exception(f"Error running command '{command}': {str(e)}")
    
    def add(self, filename=None):
        """Add files to git staging area"""
        logging.debug(f"Adding files to git staging area, filename: {filename}")
        if filename:
            self.run_command(f"git -C {self.path} add {filename}")
        else:
            self.run_command(f"git -C {self.path} add .")
        logging.debug(f"Files added to git staging area, filename: {filename}")
    
    def commit(self, message):
        """Commit staged files with the provided message"""
        logging.debug(f"Commiting staged files with message: {message}")
        self.run_command(f'git -C {self.path} commit -am "{message}"')
        
        # Rename default branch from master to main after 1st commit
        if self.pending_main_branch:
            logging.debug("Renaming default branch from master to main")
            self.run_command(f"git -C {self.path} branch -M main")
            self.pending_main_branch = False
        logging.debug(f"Staged files commited with message: {message}")

    # Convenience method that adds and commits all with the specified message
    def quick_add(self, phase, message=None):
        logging.debug(f"Quick add with phase: {phase}, message: {message}")
        self.add()
        if not message:
            message = f"Commiting changes in {phase} phase."
        self.commit(message)
        logging.debug(f"Quick add completed with phase: {phase}, message: {message}")
    
    def push(self, branch="main"):
        """Push commits to the remote repository"""
        logging.debug(f"Pushing commits to remote repository, branch: {branch}")
        self.run_command(f"git -C {self.path} push origin {branch}")
        logging.debug(f"Commits pushed to remote repository, branch: {branch}")
    
    def create_branch(self, branch_name):
        """Create and switch to a new branch"""
        logging.debug(f"Creating and switching to new branch: {branch_name}")
        self.run_command(f"git -C {self.path} checkout -b {branch_name}")
        logging.debug(f"Created and switched to new branch: {branch_name}")
    
    def switch_branch(self, branch_name):
        """Switch to an existing branch"""
        logging.debug(f"Switching to existing branch: {branch_name}")
        self.run_command(f"git -C {self.path} checkout {branch_name}")
        logging.debug(f"Switched to existing branch: {branch_name}")
    
    def merge(self, target_branch, source_branch, drop_branch=False):
        """
        Merge source_branch into target_branch following best practices
        Optionally drop the source branch after successful merge
        """
        logging.debug(f"Merging source branch: {source_branch} into target branch: {target_branch}, drop_branch: {drop_branch}")
        # First switch to target branch
        self.switch_branch(target_branch)
        
        # Merge the source branch into target
        self.run_command(f"git -C {self.path} merge {source_branch}")
        
        # If drop_branch is True, delete the source branch
        if drop_branch:
            self.drop(source_branch)
        logging.debug(f"Merged source branch: {source_branch} into target branch: {target_branch}, drop_branch: {drop_branch}")
    
    def drop(self, branch_name):
        """Delete the specified branch"""
        logging.debug(f"Dropping branch: {branch_name}")
        # Ensure we're not on the branch we're trying to delete
        current_branch = self.run_command(f"git -C {self.path} branch --show-current").strip()
        if current_branch == branch_name:
            self.switch_branch("main")
        
        # Delete the branch
        self.run_command(f"git -C {self.path} branch -D {branch_name}")
        logging.debug(f"Dropped branch: {branch_name}")
