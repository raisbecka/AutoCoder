from lib import config
from configs.elements import *
from configs.handlers import *

# Associate handlers and pydantic models with the XML tags in responses
config.handlers = {
    'req': DataHandler(
        title="requirements",
        file_name="requirements.json",
        element=Requirement
    ),
    'code_segment': DataHandler(
        title="code_segments",
        file_name="code_segments.json",
        dir="llm_data",
        element=CodeSegment
    ),
    'test': DataHandler(
        title="tests",
        file_name="test_plan.json",
        element=FunctionalityTest
    ),
    'imp': DataHandler(
        title="implementation",
        file_name="implementation.json",
        element=Implementation
    ),
    'file': FileHandler(
        element=File
    ),
    'cmd': CommandHandler(
        element=Command
    )
}

