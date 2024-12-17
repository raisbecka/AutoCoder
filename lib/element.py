import json
from textwrap import dedent
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

# Generic Base class for Products 
class Element(BaseModel):

    # Generates Pydantic elements and does validation all in one
    @staticmethod
    def create_elements(elem_list):
        for elem in elem_list:
            Element.model_validate(elem)

        # Generates a valid XML representation of the model using the aliases and _element attribute
    @classmethod
    def generate_xml_schema(cls, targ_elem=None, lvl=1):
        targ_elem = targ_elem if targ_elem else cls
        xml_str = "\n" + ("\t" * (lvl - 1)) + f"<{targ_elem._element.default}>" 
        for _, field in targ_elem.model_fields.items():
            if field.alias:
                if isinstance(field.default, Element):
                    targ_elem.generate_xml_schema(targ_elem=field.default, lvl=lvl+1)
                else:
                    xml_str += "\n" + ("\t" * (lvl)) + f"<{field.alias}></{field.alias}>"
        xml_str += "\n" + ("\t" * (lvl - 1)) + f"</{targ_elem._element.default}>"
        return xml_str        

    # Generates example XML string for formatting hints to the agent(s)
    @classmethod
    def generate_xml_formatting_rules(cls):
        formatting_rules = f"\n...Where: " \
            + ", ".join(
                [
                    f"\n - <{field.alias}>: contains "
                    + f"{field.description[0].lower()}" 
                    + f"{field.description[1:].lower()}"
                    for _, field in cls.model_fields.items() \
                    if field.alias 
                ]
            )  
        return formatting_rules
    
    # Generates example XML string for formatting hints to the agent(s)
    @classmethod
    def print_element_instructions(cls):
        inst += f"Use the below XML structure {cls._purpose.default}:\n"
        inst += cls.generate_xml_schema()
        inst += cls.generate_xml_formatting_rules()
        return inst

    # Customize if required
    def __init__(self, **data) -> None:
        self.json_string = json.dumps(data, indent=4)
        super().__init__(**data)   
      

    # Control the exact string representation for convenience
    def __str__(self):
        return self.json_string
    
## DEFINE ELEMENT TYPES ##
class DataElem(Element):
    TYPE: str = 'DATA'

class ToolElem(Element):
    TYPE: str = 'TOOL'
        


