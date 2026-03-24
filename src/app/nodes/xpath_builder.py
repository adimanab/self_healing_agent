from bs4 import BeautifulSoup, Tag
from src.app.state import AgentState
from typing import List, Optional

def xpath_builder(state: AgentState) -> dict:
    """
    Builds ranked XPath candidates from the focused DOM.
    Only runs meaningfully when is_dynamic=True, but is safe to run always.
    """
    if not state.get("is_dynamic"):
        return {"xpath_candidates": []}   # skip for static sites

    soup = BeautifulSoup(state["dom_context"], "html.parser")
    
    # Re-find the target node (dom_extractor already focused the DOM,
    # so the target element should be near the top of the focused chunk)
    target = _find_target(soup, state["selector"])
    
    if target is None:
        return {"xpath_candidates": []}

    candidates = _build_candidates(target)
    return {"xpath_candidates": candidates}


def _find_target(soup: BeautifulSoup, selector: str) -> Optional[Tag]:
    """Try to find the target element using multiple strategies."""
    # 1. CSS select on focused DOM
    try:
        node = soup.select_one(selector)
        if node:
            return node
    except Exception:
        pass
    
    # 2. First interactive element as fallback
    for tag in ['button', 'input', 'a', 'select', 'textarea']:
        node = soup.find(tag)
        if node:
            return node
    
    return None


def _build_candidates(node: Tag) -> List[str]:
    """
    Generate XPath candidates in stability order:
    data-testid > aria-label > text > placeholder > type+position
    """
    candidates = []

    # Tier 1: data-testid (most stable — set by devs intentionally)
    testid = node.get('data-testid') or node.get('data-test-id') or node.get('data-cy')
    if testid:
        candidates.append(f"//{node.name}[@data-testid='{testid}']")

    # Tier 2: aria-label (accessibility attr, very stable)
    aria = node.get('aria-label')
    if aria:
        candidates.append(f"//{node.name}[@aria-label='{aria}']")

    # Tier 3: visible text content (for buttons, links)
    text = node.get_text(strip=True)
    if text and len(text) < 50 and node.name in ('button', 'a', 'span', 'label'):
        candidates.append(f"//{node.name}[normalize-space()='{text}']")
        candidates.append(f"//{node.name}[contains(text(),'{text[:20]}')]")

    # Tier 4: placeholder (for inputs — very stable, UX-driven)
    placeholder = node.get('placeholder')
    if placeholder:
        candidates.append(f"//input[@placeholder='{placeholder}']")

    # Tier 5: label relationship (relational — survives class renames)
    label = _find_associated_label(node)
    if label:
        label_text = label.get_text(strip=True)
        if label_text:
            candidates.append(
                f"//label[normalize-space()='{label_text}']"
                f"/following-sibling::{node.name}"
            )
            candidates.append(
                f"//label[normalize-space()='{label_text}']"
                f"/parent::*//{node.name}"
            )

    # Tier 6: type attribute (functional, usually stable)
    type_attr = node.get('type')
    if type_attr and node.name == 'input':
        candidates.append(f"//input[@type='{type_attr}']")

    # Tier 7: name attribute
    name_attr = node.get('name')
    if name_attr:
        candidates.append(f"//{node.name}[@name='{name_attr}']")

    # Remove duplicates while preserving order
    seen = set()
    return [c for c in candidates if not (c in seen or seen.add(c))]


def _find_associated_label(node: Tag) -> Optional[Tag]:
    """Find the <label> element associated with this input."""
    # Method 1: label[for=id]
    node_id = node.get('id')
    if node_id and node.parent:
        root = node.parent
        while root.parent:
            root = root.parent
        label = root.find('label', {'for': node_id})
        if label:
            return label

    # Method 2: wrapping label
    parent = node.parent
    while parent:
        if parent.name == 'label':
            return parent
        parent = parent.parent

    # Method 3: preceding sibling label
    for sibling in node.previous_siblings:
        if hasattr(sibling, 'name') and sibling.name == 'label':
            return sibling

    return None