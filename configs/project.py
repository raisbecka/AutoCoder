from lib import config
from configs.elements import *
from configs.handlers import *

# Associate handlers and pydantic models with the XML tags in responses
config.handlers = {
    'req': DataHandler(
        element=Requirement,
        title="requirements",
        file_name="requirements.json"
    ),
    'test': DataHandler(
        element=FunctionalityTest,
        title="tests",
        file_name="tests.json"
    ),
    'imp': DataHandler(
        element=Implementation,
        title="implementation",
        file_name="implementation.json"
    ),
    'file': FileHandler(
        element=File
    ),
    'cmd': CommandHandler(
        element=Command
    )
}
