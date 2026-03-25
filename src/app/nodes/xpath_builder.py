import re
from bs4 import BeautifulSoup, Tag
from src.app.state import AgentState
from typing import List, Optional, Tuple

def xpath_builder(state: AgentState) -> dict:
    if not state.get("is_dynamic"):
        return {"xpath_candidates": []}

    soup = BeautifulSoup(state["dom_context"], "html.parser")
    error_msg = state.get("error", "").lower()
    
    # 1. Enhanced Intent Extraction (Splits camelCase/snake_case)
    intent_keywords = _extract_intent_keywords(state["selector"])
    
    # 2. Semantic + Proximity Search
    semantic_targets = _find_semantic_targets(soup, intent_keywords, error_msg)
    
    all_candidates = []
    for target in semantic_targets:
        all_candidates.extend(_build_candidates(target))

    seen = set()
    return {"xpath_candidates": [c for c in all_candidates if not (c in seen or seen.add(c))]}

def _extract_intent_keywords(selector: str) -> List[str]:
    """Extracts clues from the broken selector to define the 'intent'."""
    # Split by symbols, camelCase, and snake_case
    words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)|[0-9]+', selector)
    ignore = {'xpath', 'button', 'input', 'div', 'span', 'true', 'false', 'id', 'data', 'test', 'selector'}
    return [w.lower() for w in words if w.lower() not in ignore and len(w) > 2]

def _find_semantic_targets(soup: BeautifulSoup, keywords: List[str], error: str) -> List[Tag]:
    """Scores elements based on internal content AND surrounding context (Proximity)."""
    candidates = []
    target_tags = ['button', 'a', 'input', 'select', 'textarea']
    elements = soup.find_all(target_tags)

    for element in elements:
        score = 0
        
        # --- A. Internal Scoring (What the element is) ---
        element_str = str(element).lower()
        text_content = element.get_text().lower()
        
        for word in keywords:
            if word in element_str: score += 1  # Keyword in attributes/HTML
            if word in text_content: score += 3 # Keyword in visible text (Strong Intent)

        # --- B. Proximity Scoring (Where the element is) ---
        # Look at parents/ancestors up to 3 levels up
        parent = element.parent
        depth = 0
        while parent and depth < 3:
            parent_str = str(parent.attrs).lower()
            parent_text = "".join(parent.find_all(string=True, recursive=False)).lower()
            
            for word in keywords:
                if word in parent_str: score += 1 # Parent attribute match
                if word in parent_text: score += 2 # Parent heading/text match
            
            parent = parent.parent
            depth += 1

        if score > 0:
            candidates.append((score, element))

    # Sort by highest score; return top 3 most likely "intent" matches
    candidates.sort(key=lambda x: x[0], reverse=True)
    return [c[1] for c in candidates[:3]]

def _build_candidates(node: Tag) -> List[str]:
    """Generates stable XPaths based on the Stability Tier ranking."""
    candidates = []
    # Tier 1: Test IDs (highest stability)
    testid = node.get('data-testid') or node.get('data-test-id') or node.get('data-cy')
    if testid: candidates.append(f"//{node.name}[@data-testid='{testid}']")

    # Tier 2: ARIA Labels (accessibility)
    aria = node.get('aria-label')
    if aria: candidates.append(f"//{node.name}[@aria-label='{aria}']")

    # Tier 3: Text Content (normalize-space for dynamic whitespace)
    text = node.get_text(strip=True)
    if text and len(text) < 50:
        candidates.append(f"//{node.name}[normalize-space()='{text}']")

    # Tier 4: Functional Attributes (type/name)
    if node.get('name'): candidates.append(f"//{node.name}[@name='{node.get('name')}']")
    
    return candidates