from typing import List, TypedDict, Optional, Annotated
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
      
    #tools
    approved:    bool
    file_path:   Optional[str]
    line_number: Optional[int]

    #xpath 
    is_dynamic:       bool                 # detected by dom_extractor
    xpath_candidates: Optional[List[str]]  # built by xpath_builder node
    ranked_selectors: Optional[List[dict]] # final output: [{selector, type, confidence, reason}]
