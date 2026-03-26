
import sys
import os
from pathlib import Path

# Add the project root to sys.path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from src.app.nodes.human_approval import human_approval
from src.app.state import AgentState

def test_ui():
    state: AgentState = {
        "selector": "//button[@id='old-id']",
        "suggestion": "//button[@id='new-id']",
        "confidence": 85.5,
        "reason": "The ID attribute has changed from 'old-id' to 'new-id', but the element's position and text remain identical.",
        "test_name": "tests/test_login.py::test_successful_login",
        "error": "selenium.common.exceptions.NoSuchElementException: Message: no such element: Unable to locate element: {\"method\":\"xpath\",\"selector\":\"//button[@id='old-id']\"}",
        "file_path": str(root_dir / "tests" / "test_login.py"),
        "line_number": 42,
        "is_dynamic": False,
        "xpath_suggestion": "//button[@id='new-id']",
        "intent": "Click the login button",
        "dom_context": "<html><body><button id='new-id'>Login</button></body></html>"
    }

    print("Checking Rich UI...")
    result = human_approval(state)
    print(f"Result: {result}")

if __name__ == "__main__":
    test_ui()
