import os
import time
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

class PromptConsole:
    def __init__(self, prompt_title: str = 'PROMPT: Prompt goes here...'):
        self.console = Console()
        self.height = 20
        self.lines = []
        self.current_line = 0
        self.title = prompt_title
        
    def create_panel(self) -> Panel:
        """Creates a panel with current content"""
        # Join lines with newlines and ensure consistent spacing
        content = "\n".join(line.ljust(self.console.width - 4) for line in self.lines)
        return Panel(
            content,
            title=self.title,
            subtitle=f"Lines: {len(self.lines)}/{self.height-2}",
            border_style="blue",
            height=self.height,
            padding=(0, 1)
        )

    def box_print(self, text: str) -> None:
        """Prints text in box, handling scrolling when full"""
        if len(self.lines) >= self.height - 2:
            # Box full, scroll up
            self.lines = self.lines[1:] + [text]
        else:
            # Box not full yet, add new line
            self.lines.append(text)
            self.current_line = len(self.lines)

    def box_clear(self):
        """Clears box and resets state"""
        self.lines = []
        self.current_line = 0
        self.console.clear()

# Example usage
if __name__ == "__main__":

    prompt_console = PromptConsole("Interactive Console")
    with Live(prompt_console.create_panel(), refresh_per_second=4, screen=True) as live:
        time.sleep(5)
        for i in range(15):
            prompt_console.box_print(f"Line {i}")
            live.update(prompt_console.create_panel())
            time.sleep(0.2)
        
        time.sleep(2)
        prompt_console.box_clear()
