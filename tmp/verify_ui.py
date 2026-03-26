import sys
import os
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.getcwd())

from src.app.nodes.human_approval import human_approval

def test_ui(is_dynamic=False):
    state = {
        "suggestion": "//button[@id='login']",
        "selector": "button.old-class",
        "confidence": 85.5,
        "reason": "The class name changed from 'old-class' to a more stable ID.",
        "test_name": "test_login::test_success",
        "error": "TimeoutError: element not found",
        "file_path": "src/automation/pages/login_page.py",
        "line_number": 42,
        "is_dynamic": is_dynamic,
        "xpath_suggestion": "//xpath/from/builder" if is_dynamic else None
    }

    print(f"\n--- Testing UI (is_dynamic={is_dynamic}) ---")
    
    # Mock msvcrt.getch to avoid blocking
    with patch("msvcrt.getch", return_value=b"a"), \
         patch("msvcrt.kbhit", return_value=False):
        
        result = human_approval(state)
        print(f"\nResult: {result}")
        
        # Check if any "CONFIDENCE" or "SUGGESTION" was printed twice or incorrectly
        # We can't easily check the content of mock_print calls without complex logic,
        # but we can look at what was passed to Panel or Table.
        # For now, let's just run it to make sure no exceptions.

if __name__ == "__main__":
    test_ui(is_dynamic=False)
    test_ui(is_dynamic=True)
