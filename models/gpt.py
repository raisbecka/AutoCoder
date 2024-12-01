from openai import OpenAI
import os
from .base import Model, Response

class GPT(Model):
    def __init__(self, model_name: str = "gpt-4"):
        super().__init__()
        self.client = OpenAI()
        self.model_name = model_name
        
        # Set API costs based on model
        if model_name == "gpt-4o":
            self.api_costs = {
                'prompt_tokens': 0.00000250,  # $2.50 per mil
                'completion_tokens': 0.000010  # $10.00 per mil
            }
        elif model_name == "gpt-4o-2024-11-20":
            self.api_costs = {
                'prompt_tokens': 0.00000250,  # $2.50 per mil
                'completion_tokens': 0.000010  # $10.00 per mil
            }
    
    def prompt(self, prompt_text: str, use_json_schema: bool = False) -> str:
        """Send a prompt to GPT and return the response."""
        messages = []
        
        # Add system prompt if set
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        # Add JSON schema if requested
        if use_json_schema and self.json_schema:
            prompt_text = f"{prompt_text}\n\nPlease format your response according to this JSON schema:\n{self.json_schema.schema_json()}"
        
        messages.append({"role": "user", "content": prompt_text})
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages
        )
        
        # Calculate costs
        usage = response.usage
        self.calculate_usage_costs(usage.prompt_tokens, usage.completion_tokens)
        
        return Response(response.choices[0].message.content)
