import logging
from typing import List, Dict, Any, Optional, Callable, Union
from lib.task import Task
from lib.environment import Env
from lib.config import config
from lib.models import Model

class Agent:

    # Global callback - triggered when a task is completed for all Agents
    on_task_complete: Union[Callable, None] = None

    def __init__(
            self, 
            model: Model, 
            role: str, 
            system_prompt: str
    ):
        logging.debug(f"Initializing Agent with model: {model}, role: {role}")
        self.model = model
        self.role = role
        self.system_prompt = system_prompt
        self.conversation_list: List[Dict[str, Any]] = []
        self.current_task = None

    def validate_task_elements(
            self, 
            task: Task, 
            objs
    ):
        logging.debug(f"Validating task elements for task: {task}, objs: {objs}")
        task_elems = set(task.get_expected_elements())
        resp_elems = set(objs)
        return resp_elems <= task_elems

    def perform_task(
            self, 
            task: Task, 
            inputs: Dict[str, any],
            max_attempts: int = 3
    ):
        logging.info(f"Performing task: {task} with inputs: {inputs}")
        self.current_task = task
        prompt_text = task.get_prompt(**inputs)
        return_val = None
        for i in range(max_attempts):
            logging.debug(f"Attempt {i+1} of {max_attempts} for task: {task}")
            logging.debug(f"Prompting model with text: {prompt_text}")
            try:
                resp = self.model.prompt(Env.summary() + prompt_text)
                logging.debug(f"Model response: {resp}")
                data = self._process_elements(resp.props)
                if data:
                    return_val = data
                else:
                    return_val = resp.raw_text
                break            
            # If an error occurs, try again until max_retries exceeded
            except Exception as e:
                logging.error(f"Error during task execution: {e}")
                continue
        
        # Run optional callback if set on task completion
        if Agent.on_task_complete:
            logging.debug(f"Running on_task_complete callback: {Agent.on_task_complete}")
            Agent.on_task_complete()
        logging.info(f"Task {task} completed with result: {return_val}")
        return return_val

    def _process_elements(
            self, 
            elements
    ):
        logging.debug(f"Processing elements: {elements}")
        # Used to return values back from the agent
        data = {}
        
        # If response contains elements
        if len(elements.keys()) > 0:
            for key in list(elements.keys()):
                items = elements[key]
                handler = config.handlers[key]
                logging.debug(f"Processing element with key: {key}, items: {items}, handler: {handler}")
                if self.validate_task_elements(handler.validate(items)):
                    data = data | handler.process(items) # Merge returned data with existing
                logging.debug(f"Processed element with key: {key}, result: {data}")
        
        # If response is text-only
        else:
            logging.debug("No elements to process")
            return None
        logging.debug(f"Returning processed elements: {data}")
        return data
