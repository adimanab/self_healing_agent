from typing import TypedDict, Optional, Annotated
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    test_name:   str
    selector:    str
    error:       str
    dom_context: str
    suggestion:  Optional[str]
    confidence:  float
    reason:      Optional[str]
    step_passed: bool
    messages:    Annotated[list[BaseMessage], operator.add]