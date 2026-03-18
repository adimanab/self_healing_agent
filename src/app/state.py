# Shared state
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], "add_messages"]
    error_message: str
    dom_string: str