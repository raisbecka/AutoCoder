from typing import List, Dict, Any, Optional, Callable
from lib import Task, Env, config
from lib.models import Model

class Agent:

    # Global callback - triggered when a task is completed for all Agents
    on_task_complete: Callable | None = None

    def __init__(
            self, 
            model: Model, 
            role: str, 
            system_prompt: str
    ):
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
        task_elems = set(task.get_expected_elements())
        resp_elems = set(objs)
        return resp_elems <= task_elems

    def perform_task(
            self, 
            task: Task, 
            inputs: Dict[str, any],
            max_attempts: int = 3
    ):
        self.current_task = task
        prompt_text = task.get_prompt(**inputs)
        return_val = None
        for i in range(max_attempts):
            resp = self.model.prompt(Env.summary() + prompt_text)
            try:
                data = self._process_elements(resp.props)
                if data:
                    return_val = data
                else:
                    return_val = resp.raw_text
                break            
            # If an error occurs, try again until max_retries exceeded
            except Exception:
                continue
        
        # Run optional callback if set on task completion
        if Agent.on_task_complete:
            Agent.on_task_complete()

        return return_val

    def _process_elements(
            self, 
            elements
    ):
        # Used to return values back from the agent
        data = {}
        
        # If response contains elements
        if len(elements.keys()) > 0:
            for key in list(elements.keys()):
                items = elements[key]
                handler = config.handlers[key]
                if self.validate_task_elements(handler.validate(items)):
                    data = data | handler.process(items) # Merge returned data with existing
        
        # If response is text-only
        else:
            return None

