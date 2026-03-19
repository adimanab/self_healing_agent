from typing import TypedDict, Optional

class AgentState(TypedDict):
    test_name:    str
    selector:     str
    error:        str
    dom_context:  str
    suggestion:   Optional[str]
    confidence:   float
    reason:       Optional[str]
    step_passed:  bool