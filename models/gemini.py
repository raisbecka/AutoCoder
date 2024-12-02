import google.generativeai as genai
import os
from typing import AsyncGenerator
from .base import Model, Response

class Gemini(Model):
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        super().__init__()
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        
        # Set API costs (note: these are placeholder values as Gemini's pricing structure differs)
        self.api_costs = {
            'prompt_tokens': 0.0,  # Gemini doesn't charge per token
            'completion_tokens': 0.0
        }
    
    async def prompt(self, prompt_text: str, use_json_schema: bool = False) -> str:
        """Send a prompt to Gemini and return the complete response."""
        full_response = ""
        async for chunk in self.stream_prompt(prompt_text, use_json_schema):
            full_response += chunk
        return Response(full_response)

    async def stream_prompt(self, prompt_text: str, use_json_schema: bool = False) -> AsyncGenerator[str, None]:
        """Stream responses from Gemini."""
        # Add system prompt if set
        if self.system_prompt:
            prompt_text = f"{self.system_prompt}\n\n{prompt_text}"
        
        # Add JSON schema if requested
        if use_json_schema and self.json_schema:
            prompt_text = f"{prompt_text}\n\nPlease format your response according to this JSON schema:\n{self.json_schema.schema_json()}"
        
        response = await self.model.generate_content(
            prompt_text,
            stream=True
        )

        async for chunk in response:
            if chunk.text:
                yield chunk.text
