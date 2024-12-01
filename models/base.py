from abc import ABC, abstractmethod
import re
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
    
    def set_system_prompt(self, prompt: str):
        """Set the system prompt for the model."""
        self.system_prompt = prompt
    
    def set_json_schema(self, schema_class: type[BaseModel]):
        """Set the JSON schema class for structured output."""
        self.json_schema = schema_class
    
    @abstractmethod
    def prompt(self, prompt_text: str, use_json_schema: bool = False) -> str:
        """Send a prompt to the model and return the response."""
        pass
    
    def calculate_usage_costs(self, prompt_tokens: int, completion_tokens: int):
        """Calculate and track API usage costs."""
        prompt_cost = prompt_tokens * self.api_costs['prompt_tokens']
        completion_cost = completion_tokens * self.api_costs['completion_tokens']
        total_cost = prompt_cost + completion_cost
        
        # Add to the class-level total
        Model.total_api_cost += total_cost
        
        return total_cost
    

# Class for storing and parsing LLM responses    
class Response:

    tag_types = [
        'file',
        'test_file',
        'file_name',
        'file_content',
        'commamd'
    ]

    def __init__(self, resp):
        self.raw_resp = resp
        self.files = []
        self.commands = []

        # Extract commands first
        for tag, val in Response._extract_tagged_content(resp):
            if tag == 'command':
                self.commands.append(val)
            elif tag == 'file':
                self.files.append(val)


    def _extract_tagged_content(content, top_level=True):
        """
        Extract content from XML-style tags, optionally returning attributes if present.
        Finds all occurrences of the specified tag in the content.
        """
        results = []
        result = {}
        tag_types_str = "|".join(Response.tag_types)

        # Search for specific tags 
        pattern = f'<({tag_types_str})>(.*?)</(\1))>'
        matches = list(re.finditer(pattern, content, re.DOTALL))
        
        if len(matches) > 0:
            for match in matches:
                
                # Get properties of match
                tag_name = match.group(1).lower().strip()
                tag_content = match.group(2)
                
                # Recursively call method and store results in nested struct
                if top_level:
                    elem = {
                        tag_name: Response._extract_tagged_content(tag_content, top_level=False)
                    }
                    results.append(elem)
                else:
                    result[tag_name] = Response._extract_tagged_content(tag_content, top_level=False)
                
            # Return list of all matching elements
            return results if top_level else result

        # Reached end of recursive document parsing
        else:
            return content    
