import os
import sys

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.app.graph import graph_init

def run_healing_agent(test_name: str, selector: str, error: str, page) -> None:
    dom_context = page.content()
    
    """
    Heuristic: is this DOM from a React/Vue/Angular app?
    Checks for framework fingerprints in the parsed HTML.
    """
    soup = BeautifulSoup(dom_context, 'html.parser')
    html_str = str(soup)
    signals = [
        'data-reactroot',
        'data-react-',
        '__vue__',
        'ng-version',
        '_nuxt',
        'data-v-',             # Vue scoped styles
        '__NEXT_DATA__',       # Next.js
        'gatsby-',
    ]
    # Also flag if >30% of IDs look auto-generated (hash-like)
    all_ids = [tag.get('id', '') for tag in soup.find_all(id=True)]
    hash_like = [i for i in all_ids if len(i) > 6 and not i.replace('-','').replace('_','').isalpha()]
    hash_ratio = len(hash_like) / max(len(all_ids), 1)
    is_dynamic = any(s in html_str for s in signals) or hash_ratio > 0.3

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
        "approved":    False,
        "file_path":   None,
        "line_number": None,
        "is_dynamic":       is_dynamic,
        "xpath_candidates": [],
        "ranked_selectors": [],
    }

    # Step 1 — LangGraph runs on current thread (inside Playwright's event loop)
    graph  = graph_init()
    graph.invoke(state)