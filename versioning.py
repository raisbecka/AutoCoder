import subprocess
import os
import sys

class Repo:
    def __init__(self, name, path):
        """Initialize a new git repository with the given name"""
        self.name = name
        self.path = path
        self.pending_main_branch = True
        
        # Blow away existing git repo and start fresh
        try:
            os.remove('src/.git')
        except OSError:
            pass

    def init(self):
        
        # Initialize git repo
        self.run_command(f"git -C {self.path} init")
        
    
    def run_command(self, command):
        """Utility method to run git commands"""
        try:
            process = subprocess.Popen(
                command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            output, error = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Command failed: {error.decode()}")
                
            return output.decode()
        except Exception as e:
            raise Exception(f"Error running command '{command}': {str(e)}")
    
    def add(self, filename=None):
        """Add files to git staging area"""
        if filename:
            self.run_command(f"git -C {self.path} add {filename}")
        else:
            self.run_command(f"git -C {self.path} add .")
    
    def commit(self, message):
        """Commit staged files with the provided message"""
        self.run_command(f'git -C {self.path} commit -m "{message}"')
        
        # Rename default branch from master to main after 1st commit
        if self.pending_main_branch:
            self.run_command(f"git -C {self.path} branch -M main")
            self.pending_main_branch = False

    # Convenience method that adds and commits all with the specified message
    def quick_add(self, phase, message=None):
        self.add()
        if not message:
            message = f"Commiting new/updated files in \"{phase}\" phase."
        self.commit(message)
    
    def push(self, branch="main"):
        """Push commits to the remote repository"""
        self.run_command(f"git -C {self.path} push origin {branch}")
    
    def create_branch(self, branch_name):
        """Create and switch to a new branch"""
        self.run_command(f"git -C {self.path} checkout -b {branch_name}")
    
    def switch_branch(self, branch_name):
        """Switch to an existing branch"""
        self.run_command(f"git -C {self.path} checkout {branch_name}")
    
    def merge(self, target_branch, source_branch, drop_branch=False):
        """
        Merge source_branch into target_branch following best practices
        Optionally drop the source branch after successful merge
        """
        # First switch to target branch
        self.switch_branch(target_branch)
        
        # Merge the source branch into target
        self.run_command(f"git -C {self.path} merge {source_branch}")
        
        # If drop_branch is True, delete the source branch
        if drop_branch:
            self.drop(source_branch)
    
    def drop(self, branch_name):
        """Delete the specified branch"""
        # Ensure we're not on the branch we're trying to delete
        current_branch = self.run_command(f"git -C {self.path} branch --show-current").strip()
        if current_branch == branch_name:
            self.switch_branch("main")
        
        # Delete the branch
        self.run_command(f"git -C {self.path} branch -D {branch_name}")
