from abc import abstractmethod, ABC
import json
from lib.element import Element

# General class for element handlers 
class Handler(ABC):

    def __init__(
            self,
            element: Element,
    ):
        self.element = element

    @abstractmethod
    def process(data):
        pass

    # Convert data to Pydantic Element Objects and validate
    def validate(self, data) -> Element:
        return [type(obj) for obj in self.element.create_elements(data)]


