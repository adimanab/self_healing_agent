import os
import sys
import asyncio
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.app.graph import graph_init
from src.app.nodes.log_reporter import print_healing_report  # ← keep your existing path


def run_healing_agent(test_name: str, selector: str, error: str, page) -> None:
    dom_context = page.content()

    state = {
        "test_name":   test_name,
        "selector":    selector,
        "error":       error,
        "dom_context": dom_context,
        "suggestion":  None,
        "confidence":  0.0,
        "reason":      None,
        "step_passed": False,
        "messages":    [],
    }

    # Step 1 — LangGraph runs on current thread (inside Playwright's event loop)
    graph  = graph_init()
    result = graph.invoke(state)

    # Step 2 — Textual gets its own isolated thread + event loop
    def _launch_ui():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            print_healing_report(result)
        finally:
            loop.close()

    t = threading.Thread(target=_launch_ui, daemon=False)
    t.start()
    t.join()