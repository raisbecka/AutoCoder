from textwrap import dedent
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from pydantic import BaseModel, Field

# Represents a discrete, high-level section of the agents workflow
class Phase(BaseModel):
    title: str = Field(description=dedent("""
            The title for this phase of the agents execution.
    """))
    description: str = Field(description=dedent("""
            The description for this phase of the agents execution.
    """))
    _start_time: datetime = Field(description=dedent("""
            The date/time that the agent started this phase.
    """))
    _end_time: datetime = Field(description=dedent("""
            The date/time that the agent ended this phase.
    """))
    _validation_status: datetime = Field(description=dedent("""
            The post-run validation status for this phase
    """))
    _data: datetime = Field(description=dedent("""
            The data that was generated in this phase
    """))
    phase_func: Callable = Field(description=dedent("""
            Pointer to the main function for the phase
    """))
    validation_func: Callable = Field(description=dedent("""
            Pointer to a validation function which checks if the phase has
            completed successfully or not. Can be used to skip the phase 
            when starting the script if it was previously completed.
    """))

    # Execute the phase
    def run(self, **kwargs):
        self._start_time = datetime.now()
        self._data = self.phase_func(**kwargs)
        self._validation_status = self.validation_func()
        self._end_time = datetime.now()
        return self._data
    
    # Validate whether this phase is completed or not
    def is_complete(self):
        return self.validation_func()