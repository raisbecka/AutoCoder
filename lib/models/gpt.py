import logging
logger = logging.getLogger(__name__)
logger.propagate = True
from openai import OpenAI
import os
from typing import AsyncGenerator
from .base import Model, Response

class GPT(Model):
    def __init__(self, model_name: str = "gpt-4"):
        logger.debug(f"Initializing GPT model with model_name: {model_name}")
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
        logger.debug(f"GPT model initialized with model_name: {model_name}, api_costs: {self.api_costs}")
    
    async def prompt(self, prompt_text: str, use_json_schema: bool = False) -> str:
        """Send a prompt to GPT and return the complete response."""
        logger.debug(f"Starting prompt with prompt_text: {prompt_text}, use_json_schema: {use_json_schema}")
        full_response = ""
        async for chunk in self.stream_prompt(prompt_text, use_json_schema):
            full_response += chunk
        logger.debug(f"Finished prompt with full_response: {full_response}")
        return Response(full_response)

    async def stream_prompt(self, prompt_text: str, use_json_schema: bool = False) -> AsyncGenerator[str, None]:
        """Stream responses from GPT."""
        logger.debug(f"Starting stream_prompt with prompt_text: {prompt_text}, use_json_schema: {use_json_schema}")
        messages = []
        
        # Add system prompt if set
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
            logger.debug(f"Added system prompt: {self.system_prompt}")
        
        # Add JSON schema if requested
        if use_json_schema and self.json_schema:
            prompt_text = f"{prompt_text}\n\nPlease format your response according to this JSON schema:\n{self.json_schema.schema_json()}"
            logger.debug(f"Added JSON schema to prompt_text: {prompt_text}")
        
        messages.append({"role": "user", "content": prompt_text})
        logger.debug(f"Sending messages to GPT: {messages}")
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
            logger.debug("Finished streaming from GPT")
        except Exception as e:
            logger.error(f"Error during GPT API call: {e}")
            raise
        
        # Note: Usage information is not available in streaming mode
        # We might need to implement token counting separately if needed
