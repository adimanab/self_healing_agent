from ..state import AgentState
from ..tools.open_file_at_position import file_locator_tool

def file_locator(state: AgentState) -> dict:


    test_name = state["test_name"]
    selector = state["selector"]
    
    if not selector:
        return state
        
    try:
        # file_locator_tool natively handles calling open_in_editor and finding the path
        result = file_locator_tool.invoke({
            "test_name": test_name.split("::")[-1],
            "failing_selector":selector
        })
    
        
        
        if result and "error" not in result:
            return {
                "file_path": result.get("file_path"),
                "line_number": result.get("line_number")
            }
        else:
            print(f"\n[agent error] Could not locate selector file: {result.get('error')}")
    except Exception as e:
        print(f"\n[agent error] Failed to execute file locator tool: {e}")
        
    return state
