import os
import sys

# ── path fix ──────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.app.graph import graph_init

def run_healing_agent(
    test_name: str,
    selector:  str,
    error:     str,
    page,
) -> None:
    """
    Single entry point for the healing agent.
    Receives 3 error fields + live page from conftest.
    Builds state and invokes the graph.
    """

    state = {
        "test_name":   test_name,
        "selector":    selector,
        "error":       error,
        "dom_context": "",
        "suggestion":  None,
        "confidence":  0.0,
        "reason":      None,
        "step_passed": False,
    }

    graph = graph_init()

    graph.invoke(
        state,
        config={"configurable": {"page": page}}
    )