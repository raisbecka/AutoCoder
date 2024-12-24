import os
import ctypes
import sys

# Enable ANSI escape sequences on Windows
if os.name == 'nt':
    kernel32 = ctypes.windll.kernel32
    # Get the current console mode
    handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
    mode = ctypes.c_ulong()
    kernel32.GetConsoleMode(handle, ctypes.byref(mode))
    # Enable ENABLE_VIRTUAL_TERMINAL_PROCESSING
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    mode.value |= ENABLE_VIRTUAL_TERMINAL_PROCESSING
    kernel32.SetConsoleMode(handle, mode)

from prompt_toolkit import Application
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout import ScrollablePane
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from typing import List

class Interface:
    def __init__(self):
        self.log_text: List[str] = []
        self.prompt_text: List[str] = []
        self.title = "Console Interface"
        self.status = "Ready"

        self.title_window = Window(FormattedTextControl(
            lambda: HTML(f"<style bg='blue' fg='white'>= {self.title} =</style>")
        ), height=1)
        self.status_window = Window(FormattedTextControl(
            lambda: HTML(f"<style bg='white' fg='black'> Status: {self.status} </style>")
        ), height=1)
        self.log_window = ScrollablePane(Window(FormattedTextControl(
            lambda: HTML('\n'.join(self.log_text))
        ), height=10))
        self.prompt_window = ScrollablePane(Window(FormattedTextControl(
            lambda: HTML('\n'.join(self.prompt_text))
        ), height=10))

        self.container = HSplit([
            self.title_window,
            self.status_window,
            HSplit([
                self.log_window,
                self.prompt_window
            ])
        ])

        self.layout = Layout(self.container)
        self.style = Style.from_dict({
            'title': '#ffffff bg:#0000ff',
            'status': '#000000 bg:#ffffff',
        })
        self.application = Application(layout=self.layout, full_screen=True, style=self.style, mouse_support=True)

    def set_title(self, title: str):
        self.title = title
        self._update_title()

    def set_status(self, status: str):
        self.status = status
        self._update_status()

    def add_log(self, text: str):
        self.log_text.append(text)
        self._update_log()

    def add_prompt(self, text: str):
        self.prompt_text.append(text)
        self._update_prompt()

    def _update_title(self):
        self.title_window.content = FormattedTextControl(
            HTML(f"<style bg='blue' fg='white'>= {self.title} =</style>")
        )

    def _update_status(self):
        self.status_window.content = FormattedTextControl(
            HTML(f"<style bg='white' fg='black'> Status: {self.status} </style>")
        )

    def _update_log(self):
        self.log_window.content = FormattedTextControl(
            HTML('\n'.join(self.log_text))
        )

    def _update_prompt(self):
        self.prompt_window.content = FormattedTextControl(
            HTML('\n'.join(self.prompt_text))
        )

    def handle_resize(self):
        # prompt_toolkit handles resize events automatically
        pass

    def shutdown(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def run(self):
        self.application.run()

if __name__ == '__main__':
    interface = Interface()
    interface.set_title("Example Title")
    interface.set_status("Running...")
    interface.add_log("This is a log message.")
    interface.add_prompt("This is a prompt message.")
    interface.run()
