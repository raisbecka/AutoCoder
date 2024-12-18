import logging
from anthropic import Anthropic
import os
from typing import AsyncGenerator
from .base import Model, Response

logging.debug("Loading lib/models/claude.py")

class Claude(Model):
    logging.debug("Initializing Claude class")
    def __init__(self, model_name: str = "claude-3-sonnet-20240229"):
        logging.debug(f"Initializing Claude instance with model_name: {model_name}")
        super().__init__()
        self.client = Anthropic()
        self.model_name = model_name
        
        # Set API costs based on model
        if "claude-3" in model_name:
            self.api_costs = {
                'prompt_tokens': 0.000003,  # $3 per mil
                'completion_tokens': 0.000015  # $15 per mil
            }
        logging.debug(f"Claude instance initialized with api_costs: {self.api_costs}")
    
    async def prompt(self, prompt_text: str, use_json_schema: bool = False, ) -> str:
        """Send a prompt to Claude and return the complete response."""
        logging.debug(f"Prompting Claude with text: {prompt_text}, use_json_schema: {use_json_schema}")
        full_response = ""
        async for chunk in self.stream_prompt(prompt_text, use_json_schema):
            print(f"{chunk} ", end="")
            full_response += chunk
        logging.debug(f"Claude response: {full_response}")
        return Response(full_response)

    async def stream_prompt(self, prompt_text: str, use_json_schema: bool = False) -> AsyncGenerator[str, None]:
        """Stream responses from Claude."""
        logging.debug(f"Streaming prompt to Claude with text: {prompt_text}, use_json_schema: {use_json_schema}")
        # Add system prompt if set
        if self.system_prompt:
            prompt_text = f"{self.system_prompt}\n\n{prompt_text}"
        
        # Add JSON schema if requested
        if use_json_schema and self.json_schema:
            prompt_text = f"{prompt_text}\n\nPlease format your response according to this JSON schema:\n{self.json_schema.schema_json()}"
        
        stream = await self.client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt_text}],
            stream=True
        )
        logging.debug(f"Claude stream created: {stream}")
        
        async for chunk in stream:
            if chunk.content:
                yield chunk.content[0].text
        logging.debug(f"Claude stream completed")

        # Note: Usage information is not available in streaming mode
        # We might need to implement token counting separately if needed
