import logging
import os
import sys
import time
logger = logging.getLogger(__name__)
logger.propagate = True
from abc import ABC, abstractmethod
import re
from rich.console import Console
from rich.segment import ControlType
from rich.control import Control
from typing import AsyncGenerator, Generator, Iterator
from pydantic import BaseModel
from rich.syntax import Syntax

# Class for storing and parsing LLM responses    
class Response:

    def __init__(self, resp):
        self.raw_text = resp

        # Extract properties from 
        self.props = Response._extract_tagged_content(resp)
        if self.props:
            logger.debug(f"Response instance initialized with props: {list(self.props.keys())}")
        else:
            logger.debug(f"No tagged content found in LLM/model response; returning None...")

    def get_returned_elements(self):
        logger.debug(f"Getting returned elements: {self.props.keys()}")
        return set(self.props.keys())

    def _extract_tagged_content(content, top_level=True):
        """
        Extract content from XML-style tags, optionally returning attributes if present.
        Finds all occurrences of the specified tag in the content.
        """
        results = {}
        result = {}

        # Search for specific tags 
        pattern = r'<([\w]+)>(.*?)<\/(\1)>'
        matches = list(re.finditer(pattern, content, re.DOTALL))
        
        if len(matches) > 0:
            for match in matches:
                
                # Get properties of match
                tag_name = match.group(1).lower().strip()
                tag_content = match.group(2)
                
                # Recursively call method and store results in nested struct
                if top_level:
                    if tag_name not in results:
                        results[tag_name] = []
                    results[tag_name].append(Response._extract_tagged_content(tag_content, top_level=False))
                else:
                    result[tag_name] = Response._extract_tagged_content(tag_content, top_level=False)
                
            # Return list of all matching elements
            return results if top_level else result

        # Reached end of recursive document parsing
        else:
            if top_level:
                return None
            else:
                return content


class Model(ABC):
    
    console = Console()
    
    # Class variable to track total API costs across all instances
    total_api_cost = 0.0    
    
    def __init__(self):
        self.system_prompt = None
        self.json_schema = None
        self.api_costs = {
            'prompt_tokens': 0.0,
            'completion_tokens': 0.0
        }
        logger.debug(f"Model instance initialized with api_costs: {self.api_costs}")
    
    def set_system_prompt(self, prompt: str):
        """Set the system prompt for the model."""
        logger.debug(f"Setting system prompt: {prompt}")
        self.system_prompt = prompt
        logger.debug(f"System prompt set: {self.system_prompt}")
    
    def set_json_schema(self, schema_class: type[BaseModel]):
        """Set the JSON schema class for structured output."""
        logger.debug(f"Setting json schema: {schema_class}")
        self.json_schema = schema_class
        logger.debug(f"Json schema set: {self.json_schema}")
    
    def prompt(self, prompt_text: str, console_overlay: bool=False) -> Response:
        if console_overlay:
            print("\033[?1049h\033[22;0;0t\033[0;0H", end="")

        full_response = ""
        max_lines = 1
        Model.console.print("[bold green]=== [Agent]: [/bold green]", end="")
        for text in self.sync_prompt(prompt_text):
            full_response += text
            lines = full_response.split("\n")
            line_count = len(lines)
            if line_count > max_lines:
                syntax = Syntax(lines[-2], "xml")
                Model.console.print(syntax)
                max_lines = line_count
        syntax = Syntax(lines[-1], "xml")
        Model.console.print(syntax)


        if console_overlay:
            print("\033[?1049l\033[23;0;0t", end="")
        else:
            with Model.console.status("[bold green]Prompt Response Complete! Processing...[/bold green]", spinner="dots"):
                time.sleep(1)
            for i in range(max_lines):
                Model.console.control(
                    Control(
                        (ControlType.CURSOR_UP, 1),
                        (ControlType.ERASE_IN_LINE, 2)
                    )
                )
                time.sleep(0.02)

        logger.debug(f"Prompt response complete: {full_response}")

        return Response(full_response)
    
    def prompt_sync(self, prompt_text: str) -> Iterator[str]:
        """Send a prompt to the model and return the complete response. Overridden by model-specific child class."""
        yield "This method should be overridden by a model-specific child class!"
    
    def calculate_usage_costs(self, prompt_tokens: int, completion_tokens: int):
        """Calculate and track API usage costs."""
        logger.debug(f"Calculating usage costs with prompt_tokens: {prompt_tokens}, completion_tokens: {completion_tokens}")
        prompt_cost = prompt_tokens * self.api_costs['prompt_tokens']
        completion_cost = completion_tokens * self.api_costs['completion_tokens']
        total_cost = prompt_cost + completion_cost
        
        # Add to the class-level total
        Model.total_api_cost += total_cost
        logger.debug(f"Calculated usage costs: {total_cost}, total_api_cost: {Model.total_api_cost}")
        return total_cost
    