import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.app.graph import graph_init

def run_healing_agent(
    test_name: str,
    selector:  str,
    error:     str,
    page,
) -> None:
    # fetch DOM from live sync Playwright page right here
    dom_context = page.content()

    state = {
        "test_name":   test_name,
        "selector":    selector,
        "error":       error,
        "dom_context": dom_context,  # ← full page HTML, dom_extractor node will focus it
        "suggestion":  None,
        "confidence":  0.0,
        "reason":      None,
        "step_passed": False,
        "messages":    [],           # ← required by AgentState
    }

    graph = graph_init()
    result = graph.invoke(state)

    # print so you can see agent output in pytest -s
    print(f"\n[agent] suggestion : {result.get('suggestion')}")
    print(f"[agent] reason     : {result.get('reason')}")
    print(f"[agent] confidence : {result.get('confidence')}")