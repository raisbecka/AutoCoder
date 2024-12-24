import json
from textwrap import dedent
from typing import Dict, Any, Optional, List, get_type_hints
from typing import get_args, get_origin, Optional, List, Union
import typing
from pydantic import BaseModel
import logging
logger = logging.getLogger(__name__)
logger.propagate = True

# Custom type for optional items that can be added at discretion of model, and more than one can be included
T = typing.TypeVar('T')
ManyOptional = Optional[Union[List[T], T, None]]

# Generic Base class for Products 
class Element(BaseModel):

    # Private attribute - will include the JSON string of the model
    _json_schema: str = ""

    # Generates Pydantic elements and does validation all in one
    @staticmethod
    def create_elements(elem_list):
        obj_list = []
        for elem in elem_list:
            obj_list.append(Element.model_validate(elem))
        logger.info(f"Successfully created Pydantic elements from list of Dicts.")
        return obj_list
    
    # Used to check if a field in the model maps to another pydantic model
    @classmethod
    def is_subclass_of_element(cls, type_):
        if get_origin(type_) in {Union, Optional, List, list}:
            for arg in get_args(type_):
                result = Element.is_subclass_of_element(arg)
                if result:
                    return result
        if isinstance(type_, type) and issubclass(type_, cls):
            return type_

        # Generates a valid XML representation of the model using the aliases and _element attribute
    @classmethod
    def generate_xml_schema(cls, xml_str="", lvl=1):
        logger.debug(f"Generating XML schema for {cls} at level {lvl}")
        field_types = get_type_hints(cls)
        xml_str += "\n" + ("\t" * (lvl - 1)) + f"<{cls._element.default}>" 
        for field_name, field in cls.model_fields.items():
            if field.alias:
                field_type = field_types[field_name]
                child_elem = Element.is_subclass_of_element(field_type)
                if child_elem:
                    xml_str = child_elem.generate_xml_schema(xml_str=xml_str, lvl=lvl+1)
                else:
                    xml_str += "\n" + ("\t" * (lvl)) + f"<{field.alias}></{field.alias}>"
        xml_str += "\n" + ("\t" * (lvl - 1)) + f"</{cls._element.default}>"
        return xml_str        

    # Generates example XML string for formatting hints to the agent(s)
    @classmethod
    def generate_xml_formatting_hints(cls, formatting_rules="", lvl=1):
        logger.debug(f"Generating XML formatting rules for {cls}")
        field_types = get_type_hints(cls)
        for field_name, field in cls.model_fields.items():
            if field.alias:
                formatting_rules += "\n" + ('\t' * (lvl-1)) + f"- <{field.alias}>: "
                field_type = field_types[field_name]
                child_elem = Element.is_subclass_of_element(field_type)
                if child_elem:
                    formatting_rules += "is composed of the following child elements:"
                    formatting_rules = child_elem.generate_xml_formatting_hints(
                        formatting_rules=formatting_rules, 
                        lvl=lvl+1
                    )
                else:
                    formatting_rules += "contains " \
                    + f"{field.description[0].lower()}" \
                    + f"{field.description[1:]}"
 
        return formatting_rules
    
    # Generates example XML string for formatting hints to the agent(s)
    @classmethod
    def print_element_instructions(cls):
        logger.debug(f"Generating element instructions for {cls}")
        inst = f"Use the below XML structure {cls._purpose.default}:\n"
        inst += cls.generate_xml_schema()
        inst += "\n\nWhere the XML elements are populated with the following data:"
        inst += cls.generate_xml_formatting_hints()
        return inst
    
    @classmethod
    def get_tag(cls):
        return cls._element.default 

    # Customize if required
    def __init__(self, **data) -> None:
        Element._json_string = json.dumps(data, indent=4)
        super().__init__(**data)  
      

    # Control the exact string representation for convenience
    def __str__(self):
        return Element._json_string
    
## DEFINE ELEMENT TYPES ##
class DataElem(Element):
    TYPE: str = 'DATA'

class ToolElem(Element):
    TYPE: str = 'TOOL'
