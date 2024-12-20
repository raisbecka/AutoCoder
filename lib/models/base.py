import logging
from abc import ABC, abstractmethod
import re
from typing import AsyncGenerator
from pydantic import BaseModel

class Model(ABC):
    # Class variable to track total API costs across all instances
    total_api_cost = 0.0
    
    def __init__(self):
        self.system_prompt = None
        self.json_schema = None
        self.api_costs = {
            'prompt_tokens': 0.0,
            'completion_tokens': 0.0
        }
        logging.debug(f"Model instance initialized with api_costs: {self.api_costs}")
    
    def set_system_prompt(self, prompt: str):
        """Set the system prompt for the model."""
        logging.debug(f"Setting system prompt: {prompt}")
        self.system_prompt = prompt
        logging.debug(f"System prompt set: {self.system_prompt}")
    
    def set_json_schema(self, schema_class: type[BaseModel]):
        """Set the JSON schema class for structured output."""
        logging.debug(f"Setting json schema: {schema_class}")
        self.json_schema = schema_class
        logging.debug(f"Json schema set: {self.json_schema}")
    
    @abstractmethod
    async def prompt(self, prompt_text: str, use_json_schema: bool = False) -> str:
        """Send a prompt to the model and return the response."""
        pass
    
    def calculate_usage_costs(self, prompt_tokens: int, completion_tokens: int):
        """Calculate and track API usage costs."""
        logging.debug(f"Calculating usage costs with prompt_tokens: {prompt_tokens}, completion_tokens: {completion_tokens}")
        prompt_cost = prompt_tokens * self.api_costs['prompt_tokens']
        completion_cost = completion_tokens * self.api_costs['completion_tokens']
        total_cost = prompt_cost + completion_cost
        
        # Add to the class-level total
        Model.total_api_cost += total_cost
        logging.debug(f"Calculated usage costs: {total_cost}, total_api_cost: {Model.total_api_cost}")
        return total_cost
    

# Class for storing and parsing LLM responses    
class Response:
    logging.debug("Initializing Response class")
    def __init__(self, resp):
        logging.debug(f"Initializing Response instance with resp: {resp}")
        self.raw_text = resp

        # Extract properties from 
        self.props = Response._extract_tagged_content(resp)
        logging.debug(f"Response instance initialized with props: {self.props}")

    def get_returned_elements(self):
        logging.debug(f"Getting returned elements: {self.props.keys()}")
        return set(self.props.keys())

    def _extract_tagged_content(content, top_level=True):
        """
        Extract content from XML-style tags, optionally returning attributes if present.
        Finds all occurrences of the specified tag in the content.
        """
        logging.debug(f"Extracting tagged content with content: {content}, top_level: {top_level}")
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
            logging.debug(f"Extracted tagged content: {results if top_level else result}")
            return results if top_level else result

        # Reached end of recursive document parsing
        else:
            logging.debug(f"No tagged content found, returning content: {content}")
            return content
