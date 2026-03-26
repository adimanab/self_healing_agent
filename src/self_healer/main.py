from bs4 import BeautifulSoup

from .graph import graph_init


def run_healing_agent(test_name: str, selector: str, error: str, page) -> None:
    dom_context = page.content()
    
    def determine_if_dynamic(sel: str, err: str) -> bool:
        sel_lower = sel.lower().strip()
        err_lower = err.lower()
        #xpath checking - pattern finding like '/' or '//'
        is_xpath_format = (
            sel_lower.startswith('/') or 
            sel_lower.startswith('//') or 
            sel_lower.startswith('xpath=') or
            '[' in sel_lower and ('@' in sel_lower or 'text()' in sel_lower)
        )
        
        # 2. Error Message Keywords
        # Check if the error explicitly mentions XPath issues (like 'unable to locate xpath')
        # vs CSS/Selector issues.
        mentions_xpath = 'xpath' in err_lower
        mentions_css = 'selector' in err_lower or 'css' in err_lower

        # Logic: If it's an XPath or the error specifically flags XPath, treat as Dynamic
        if is_xpath_format or (mentions_xpath and not mentions_css):
            return True
        
        # Default to False in case of Static
        return False

    is_dynamic = determine_if_dynamic(selector, error)

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