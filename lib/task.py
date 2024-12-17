from textwrap import dedent
from typing import List
from lib.element import Element

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
        return set([elem for elem in self.expected_elements])

    def get_prompt(self, **inputs):
        main_prompt = Task.env_info + "\n<task>\nPlease complete the following task - paying " \
                    + "as much attention to detail as possible: \n"
        main_prompt += self.details.format(**self.inputs)
        inst_prompt = dedent("""\n</task>\n<instructions>When completing the above task, please enclose your response within 
                      an XML tag structure - ensuring that each required value is included within the correct opening/closing
                      tag pair. For example, if you are including 3 different examples in your response, and you have a tag <ex> 
                      that can be used to include the title of an example, then you should return 3 <ex>EXAMPLE</ex> elements 
                      - where EXAMPLE is replaced with the details of each example.\n</instructions>.\n<valid_xml_tags>\nSee 
                      the below list of valid XML elements/tags that can be used in your response:\n""")
        for elem in self.expected_elements:
            inst_prompt += elem.print_element_instructions()
        main_prompt += inst_prompt
        main_prompt += "\n</valid_xml_tags>"
        return main_prompt
