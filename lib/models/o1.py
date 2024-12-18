import logging
from .gpt import GPT

class O1(GPT):
    def __init__(self, model_name: str = "o1-preview"):
        logging.debug(f"Initializing O1 model with model_name: {model_name}")
        super().__init__(model_name)
        
        # Set API costs for O1 models
        if model_name == "o1-preview":
            self.api_costs = {
                'prompt_tokens': 0.000015,  # $15 per mil
                'completion_tokens': 0.000060  # $60 per mil
            }
            logging.debug(f"Set API costs for o1-preview: {self.api_costs}")
        elif model_name == "o1-mini":
            self.api_costs = {
                'prompt_tokens': 0.000003,  # $3.00 per mil
                'completion_tokens': 0.000012  # $12.00 per mil
            }
            logging.debug(f"Set API costs for o1-mini: {self.api_costs}")
        logging.debug(f"O1 model initialized with model_name: {model_name}, api_costs: {self.api_costs}")
