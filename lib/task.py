import logging
logger = logging.getLogger(__name__)
logger.propagate = True
from textwrap import dedent
from typing import List
from lib.element import Element
from lib.environment import Env


class Task:

    def __init__(
            self, 
            details: str,
            expected_elements: List[Element] = []
    ):
        self.details = details
        self.expected_elements = expected_elements
        self.result: str = None

    def get_expected_elements(self):
        logger.debug(f"Getting expected elements: {self.expected_elements}")
        return set([elem.get_tag() for elem in self.expected_elements])

    def get_prompt(self, **inputs):
        logger.debug(f"Getting prompt with inputs: {inputs}")
        main_prompt = "\n<task>\nPlease complete the following task - paying " \
                    + "as much attention to detail as possible: \n"
        main_prompt += self.details.format(**inputs)
        main_prompt += "\n</task>"
        if len(self.expected_elements) > 0:
            inst_prompt = dedent("""
                        <instructions>
                        When completing the above task, if any of the below listed XML elements apply to data you are trying to return, 
                        tools you are trying to call, or actions you are trying to take, use them to return the applicable items - 
                        ensuring you include the data intended for each element or sub-element. For example, if you are including 3 
                        different examples in your response, and you have a tag <ex> that can be used to include the title of an 
                        example, then you should return 3 <ex>EXAMPLE</ex> elements - where EXAMPLE is replaced with the details of 
                        each example. DO NOT use any tags what-so-ever that are not listed below - including an enclosing parent tag. 
                        For instance, from the previous example, you would  NOT enclose the <ex></ex> elements inside of an <examples> 
                        parent tag.
                        </instructions>
                        <valid_xml_tags>
                        See the below list of valid XML elements/tags that can be used in your response:
                        """)
            for elem in self.expected_elements:
                inst_prompt += elem.print_element_instructions()
            main_prompt += inst_prompt
            main_prompt += dedent("""
            </valid_xml_tags>"
            """)
        return main_prompt
    

# Custom exception for TaskValidationError
class TaskValidationError(Exception):
    """Exception raised when the elements in the LLM/Model response differ from the expected elements of the task."""
    def __init__(self, message="Elements in the LLM/Model response differ from the expected elements of the task."):
        self.message = message
        super().__init__(self.message)
