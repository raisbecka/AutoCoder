from anthropic import Anthropic
import os
from .base import Model, Response

class Claude(Model):
    def __init__(self, model_name: str = "claude-3-sonnet-20240229"):
        super().__init__()
        self.client = Anthropic()
        self.model_name = model_name
        
        # Set API costs based on model
        if "claude-3" in model_name:
            self.api_costs = {
                'prompt_tokens': 0.000003,  # $3 per mil
                'completion_tokens': 0.000015  # $15 per mil
            }
    
    def prompt(self, prompt_text: str, use_json_schema: bool = False) -> str:
        """Send a prompt to Claude and return the response."""
        messages = []
        
        # Add system prompt if set
        if self.system_prompt:
            prompt_text = f"{self.system_prompt}\n\n{prompt_text}"
        
        # Add JSON schema if requested
        if use_json_schema and self.json_schema:
            prompt_text = f"{prompt_text}\n\nPlease format your response according to this JSON schema:\n{self.json_schema.schema_json()}"
        
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt_text}]
        )
        
        # Calculate costs if usage information is available
        if hasattr(response, 'usage'):
            usage = response.usage
            self.calculate_usage_costs(usage.input_tokens, usage.output_tokens)
        
        return Response(response.content[0].text)
