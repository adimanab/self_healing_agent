import os
import subprocess
import shutil


def open_in_editor(file_path: str, line: int, column: int = 1):
    """
    Opens file at exact line + column in supported editors.
    """

    file_path = os.path.abspath(file_path)

    editors = [
        # VS Code (supports line:column)
        ("code", ["code", "--reuse-window", "--goto", f"{file_path}:{line}:{column}"]),

        # PyCharm (line works, column support limited)
        ("pycharm", ["pycharm", f"{file_path}:{line}"]),

        # IntelliJ
        ("idea", ["idea", f"{file_path}:{line}"]),

        # Sublime Text (supports line:column)
        ("subl", ["subl", f"{file_path}:{line}:{column}"]),
    ]

    for name, command in editors:
            if shutil.which(name):
                try:
                    subprocess.run(command)
                    return
                except Exception as e:
                    print(f"Failed with {name}: {e}")

    print("No supported editor CLI found.")
    print(f"Open manually: {file_path}:{line}:{column}")