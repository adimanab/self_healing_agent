import os
from src.app.state import AgentState
from src.app.tools.file_editor_tool import file_editor_tool

def apply_fix(state: AgentState) -> dict:
    approved = state.get("approved", False)
    file_path = state.get("file_path")
    line_number = state.get("line_number")
    selector = state.get("selector")
    suggestion = state.get("suggestion")

    if not approved:
        print("\n[agent action] Fix was rejected. No changes made.")
        return state

    if not file_path or not line_number:
        print("\n[agent error] Cannot apply fix: File path or line number not found.")
        return state

    if not selector or not suggestion:
        print("\n[agent error] Cannot apply fix: Missing original selector or suggestion.")
        return state

    # Invoke the user's file editor tool directly
    try:
        result = file_editor_tool.invoke({
            "file_path": file_path,
            "line_number": line_number,
            "old_selector": selector,
            "new_selector": suggestion
        })
        
        if result.get("error"):
            print(f"\n[agent error] Tool failed: {result['error']}")
        else:
            print(f"\n[agent success] {result.get('message', 'File updated successfully')}")
            
    except Exception as e:
        print(f"\n[agent error] Failed to execute file editor tool: {e}")

    return state
