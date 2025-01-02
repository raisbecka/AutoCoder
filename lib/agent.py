import logging
import requests
logger = logging.getLogger(__name__)
logger.propagate = True
from typing import List, Dict, Any, Optional, Callable, Union
from lib.task import Task, TaskValidationError
from lib.element import Element
from lib.environment import Env
from lib.config import config
from lib.models import Model, Response
import pydantic_core
import traceback

class Agent:

    # Global callback - triggered when a task is completed for all Agents
    on_task_complete: Union[Callable, None] = None

    def __init__(
            self, 
            model: Model, 
            role: str, 
            system_prompt: str
    ):
        logger.debug(f"Initializing Agent with model: {model}, role: {role}")
        self.model = model
        self.role = role
        self.system_prompt = system_prompt
        self.conversation_list: List[Dict[str, Any]] = []
        self.current_task = None

    def perform_task(
            self, 
            task: Task, 
            inputs: Dict[str, any],
            max_attempts: int = 3
    ):
        logger.info(f"Performing task: {task} with inputs: {inputs}")
        self.current_task = task
        prompt_text = task.get_prompt(**inputs)
        return_val = None
        for i in range(max_attempts):
            logger.debug(f"Attempt {i+1} of {max_attempts} for task: {task}")
            logger.debug(f"Prompting model with text: {prompt_text}")
            try:
                resp = self.model.prompt(Env.summary() + prompt_text)
                logger.debug(f"Model response: {resp}")
                if resp.props:
                    return_val = self._process_elements(task, resp)
                else:
                    logger.debug("No elements to process")
                    return_val = resp.raw_text
                break            
            
            # If an error occurs, try again until max_retries exceeded
            except Exception as e:
                if isinstance(e, requests.exceptions.RequestException):
                    error_str = "Network"
                elif isinstance(e, TaskValidationError):
                    error_str = "Task Validation"   
                elif isinstance(e, pydantic_core._pydantic_core.ValidationError):
                    error_str = "Element Validation"
                else:
                    raise e
                logger.error(f"{error_str}: {e}\n" + f"Retrying for attempt {i + 1}/{max_attempts}" \
                    if i + 1 <= max_attempts else f"{error_str}: Max attempts exceeded - shutting down...")
                logger.error(traceback.format_exc())
                
        
        # Run optional callback if set on task completion
        if Agent.on_task_complete and return_val:
            logger.debug(f"Running on_task_complete callback: {Agent.on_task_complete}")
            Agent.on_task_complete()
        
        return return_val

    def _process_elements(
            self, 
            task: Task,
            resp: Response
    ):
        
        # Used to return values back from the agent
        data = {}
        elements = list(resp.props.keys())
        
        # Ensure the right elements have been returned
        if set(task.get_expected_elements()) >= set(elements):

            logger.debug(f"Processing returned elements: {elements}")
            
            # If response contains elements
            data = {}
            for key in elements:
                items = resp.props[key]

                try:
                    handler = config.handlers[key]
                    logger.debug(f"Processing element with key: {key}, items: {len(items)}, handler: {handler}")
                    data = handler.process(items) | data
                except KeyError as e:
                    logger.debug("No handler configured/mapped for element \"key\"; storing data and proceeding...")
                    data = {key: items} | data
        
        else:
            logger.debug(f"Validation failed on returned elements: {elements}")
            raise TaskValidationError("Validation Error: Unexpected elements contained within LLM/model response")

        logger.debug(f"Returning processed elements: {list(data.keys())}")
        return data
        
