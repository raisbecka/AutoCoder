import logging
logger = logging.getLogger(__name__)
logger.propagate = True
from ollama import Client
from .base import Model, Response

class Ollama(Model):
    def __init__(self, model_name: str = "qwen2.5-coder:32b-instruct-q4_K_M"):
        logger.debug(f"Initializing Ollama model with model_name: {model_name}")
        super().__init__()
        self.client = Client(host='http://10.243.243.236:11434')
        self.model_name = model_name
        
        # Set API costs - Ollama is typically free/local so setting to 0
        self.api_costs = {
            'prompt_tokens': 0.0,
            'completion_tokens': 0.0
        }
        logger.debug(f"Ollama model initialized with model_name: {model_name}, api_costs: {self.api_costs}")
    
    def prompt(self, prompt_text: str, use_json_schema: bool = False) -> str:
        """Send a prompt to Ollama and return the complete response."""
        logger.debug(f"Starting prompt with prompt_text: {prompt_text}, use_json_schema: {use_json_schema}")
        full_response = ""
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
        logger.debug(f"Sending messages to Ollama: {messages}")
        
        # Stream the response from Ollama
        try:
            stream = self.client.chat(
                model=self.model_name,
                messages=messages,
                stream=True
            )

            for chunk in stream:
                if chunk['message']['content'] is not None:
                    text = chunk['message']['content']
                    print(text, end="")
                    full_response += text
            logger.debug(f"Finished prompt with full_response: {full_response}")
        except Exception as e:
            logger.error(f"Error during Ollama API call: {e}")
            raise

        return Response(full_response)
