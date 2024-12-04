import sys
from openai import OpenAI
import os
from typing import AsyncGenerator
from .base import Model, Response

class VLLM(Model):
    def __init__(self, model_name: str = "Qwen/Qwen2.5-Coder-14B-Instruct-GPTQ-Int4"):
        super().__init__()
        self.client = OpenAI(base_url='http://192.168.50.13:11434/v1')
        self.model_name = model_name
    
    def prompt(self, prompt_text: str, use_json_schema: bool = False) -> str:
        """Send a prompt to Ollama and return the complete response."""
        full_response = ""
        messages = []
        
        # Add system prompt if set
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        # Add JSON schema if requested
        if use_json_schema and self.json_schema:
            prompt_text = f"{prompt_text}\n\nPlease format your response according to this JSON schema:\n{self.json_schema.schema_json()}"
        
        messages.append({"role": "user", "content": prompt_text})
        
        # Stream the response from Ollama
        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=5000,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                text = chunk.choices[0].delta.content
                print(text, end="")
                full_response += text

        return Response(full_response)

