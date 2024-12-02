from ollama import Client
from .base import Model, Response

class Ollama(Model):
    def __init__(self, model_name: str = "qwen2.5-coder:32b-instruct-q4_K_M"):
        super().__init__()
        self.client = Client(host='http://192.168.50.13:11434')
        self.model_name = model_name
        
        # Set API costs - Ollama is typically free/local so setting to 0
        self.api_costs = {
            'prompt_tokens': 0.0,
            'completion_tokens': 0.0
        }
    
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
        stream = self.client.chat(
            model=self.model_name,
            messages=messages,
            stream=True
        )

        for chunk in stream:
            if chunk['message']['content'] is not None:
                print(f"{chunk} ", end="")
                full_response += chunk['message']['content']

        return Response(full_response)


