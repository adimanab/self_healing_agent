import os
from langchain_core.tools import tool

from src.app.lib.open_file_position import open_in_editor

@tool
def file_locator_tool(test_name: str, failing_selector: str) -> dict:
    """
    Locates the exact file, line, and column of a failing selector.

    Args:
        test_name (str): The name of the test function (e.g., 'test_checkout_flow').
        failing_selector (str): The exact failing Playwright selector string.

    Returns:
        dict: {
            'file_path': str,
            'line_number': int,
            'column_number': int,
            'code_snippet': str,
            'function_name': str
        }
        OR {'error': str}
    """

    base_dir = os.getcwd()
    matches = []

    for root, dirs, files in os.walk(base_dir):
        # Skip irrelevant directories to speed up the search
        dirs[:] = [
            d for d in dirs
            if d not in [
                '.git', '.venv', 'venv', 'env',
                'node_modules', '__pycache__', '.pytest_cache'
            ]
        ]

        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for i, line in enumerate(f):
                            if failing_selector in line:
                                column_index = line.find(failing_selector)

                                matches.append({
                                    "file_path": os.path.abspath(file_path),
                                    "line_number": i + 1,
                                    "column_number": column_index + 1,  # 1-based
                                    "code_snippet": line.strip(),
                                    "function_name": test_name
                                })

                except Exception:
                    # Ignore unreadable files
                    continue

    # ---- Match resolution ----

    if len(matches) == 1:
        match = matches[0]
        try:
            open_in_editor(
                match["file_path"],
                match["line_number"],
                match["column_number"]
            )
        except Exception:
            pass
        return match

    elif len(matches) > 1:
        selected_match = None

        for match in matches:
            normalized_path = match["file_path"].replace("\\", "/")

            if any(key in normalized_path for key in ["/pages/", "/tests/", "/specs/"]):
                selected_match = match
                break

        if not selected_match:
            selected_match = matches[0]

        try:
            open_in_editor(
                selected_match["file_path"],
                selected_match["line_number"],
                selected_match["column_number"]
            )
        except Exception:
            pass

        return selected_match

    # ---- No match found ----

    return {
        "error": f"Selector '{failing_selector}' not found anywhere in the project."
    }