import os
from langchain_core.tools import tool

from src.app.lib.open_file_position import open_in_editor

@tool
def file_editor_tool(file_path: str, line_number: int, old_selector: str, new_selector: str) -> dict:
    """
    Works to edit the file and apply the suggestion given by the agent.
    Args:
        file_path (str): The absolute or relative path to the test file.
        line_number (int): The 1-indexed line number identified by the locator.
        old_selector (str): The original failing selector string.
        new_selector (str): The new correct selector string suggested by the agent.
    Returns:
        dict: A dictionary containing 'success' and 'message' or 'error'.
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        idx = line_number - 1
        if idx < 0 or idx >= len(lines):
            return {"error": f"Line number {line_number} is out of bounds for {file_path}"}
            
        target_line = lines[idx]
        
        if old_selector not in target_line:
            return {"error": f"Old selector '{old_selector}' not found on line {line_number} in {file_path}. Line contents: '{target_line.strip()}'"}
            
        # Replace only the exact match of the old selector with the new selector
        new_line = target_line.replace(old_selector, new_selector, 1)
        lines[idx] = new_line

        # Find new cursor position (end of replaced selector)
        col_position = new_line.find(new_selector) + len(new_selector) + 1
        
        # write file with correct data
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
            f.flush()
            os.fsync(f.fileno())

        # try editor separately
        try:
            open_in_editor(file_path, line_number, col_position)
        except Exception as e:
            return {
                "success": True,
                "message": f"Selector updated, but failed to open editor: {str(e)}"
            }


        return {
            "success": True,
            "message": f"Updated '{old_selector}' to '{new_selector}'",
        }

    except Exception as e:
        return {"error": f"Failed to modify file: {str(e)}"}
