from bs4 import BeautifulSoup
from src.app.state import AgentState
from src.app.utils.dom.dom_utils import build_selector_hints, climb_to_container, safe_serialize
from src.app.utils.dom.fingerprints import find_by_fingerprint, infer_fingerprint_from_selector
from src.app.utils.dom.selector_resolver import resolve_from_error, resolve_playwright_selector

def _detect_dynamic(soup: BeautifulSoup) -> bool:
    """
    Heuristic: is this DOM from a React/Vue/Angular app?
    Checks for framework fingerprints in the parsed HTML.
    """
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

    return any(s in html_str for s in signals) or hash_ratio > 0.3


def dom_extractor(state: AgentState) -> dict:
    selector    = state["selector"]
    error       = state["error"]
    dom_context = state["dom_context"]

    soup = BeautifulSoup(dom_context, 'html.parser')

    node = resolve_playwright_selector(soup, selector)
    if node is None:
        node = resolve_from_error(soup, error)
    if node is None:
        fingerprint = infer_fingerprint_from_selector(selector)
        node = find_by_fingerprint(soup, fingerprint)

    if node:
        container = climb_to_container(node, max_levels=4)
        focused_dom = safe_serialize(container, char_limit=5000)
    else:
        focused_dom = safe_serialize(soup.body, char_limit=3000)

    hints = build_selector_hints(soup, selector)
    is_dynamic = _detect_dynamic(soup)
    return {
        "dom_context": focused_dom + hints,
        "is_dynamic": is_dynamic
        }