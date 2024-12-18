import logging
import sys
from openai import OpenAI
import os
from typing import AsyncGenerator
from .base import Model, Response

class VLLM(Model):
    def __init__(self, model_name: str = "Qwen/Qwen2.5-Coder-14B-Instruct-GPTQ-Int4"):
        logging.debug(f"Initializing VLLM model with model_name: {model_name}")
        super().__init__()
        self.client = OpenAI(base_url='http://192.168.50.13:11434/v1', api_key="sk-xxxxxxxxxxxxxxx")
        self.model_name = model_name
        logging.debug(f"VLLM model initialized with model_name: {model_name}")
    
    def prompt(self, prompt_text: str, use_json_schema: bool = False) -> str:
        """Send a prompt to Ollama and return the complete response."""
        logging.debug(f"Starting prompt with prompt_text: {prompt_text}, use_json_schema: {use_json_schema}")
        full_response = ""
        messages = []
        
        # Add system prompt if set
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
            logging.debug(f"Added system prompt: {self.system_prompt}")
        
        # Add JSON schema if requested
        if use_json_schema and self.json_schema:
            prompt_text = f"{prompt_text}\n\nPlease format your response according to this JSON schema:\n{self.json_schema.schema_json()}"
            logging.debug(f"Added JSON schema to prompt_text: {prompt_text}")
        
        messages.append({"role": "user", "content": prompt_text})
        logging.debug(f"Sending messages to VLLM: {messages}")
        
        # Stream the response from Ollama
        try:
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
            logging.debug(f"Finished prompt with full_response: {full_response}")
        except Exception as e:
            logging.error(f"Error during VLLM API call: {e}")
            raise

        return Response(full_response)
