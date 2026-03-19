import re
from bs4 import BeautifulSoup
from src.app.state import AgentState


def dom_extractor(state: AgentState) -> dict:
    """
    LangGraph node. Reads selector, error, dom_context from state.
    Resolves the most relevant DOM subtree (mirroring Playwright's selector resolution)
    and writes the focused subtree back to dom_context.
    """
    selector    = state["selector"]
    error       = state["error"]
    dom_context = state["dom_context"]

    print("ye ayya hain: ", dom_context)

    soup = BeautifulSoup(dom_context, 'html.parser')

    node = (
        _resolve_playwright_selector(soup, selector)
        or _resolve_from_error(soup, error)
    )

    if node:
        container = _climb_to_container(node)
        focused_dom = container.prettify()[:4000]
    else:
        focused_dom = str(soup.body)[:3000]

    return {
        "dom_context": focused_dom   # overwrites full DOM with focused subtree
    }


# ── Playwright selector resolution ────────────────────────────────────────────

def _resolve_playwright_selector(soup, selector: str):
    """Mirror Playwright's internal selector resolution order."""

    # 1. ID:  #login-btn
    if selector.startswith('#'):
        return soup.find(id=selector[1:])

    # 2. ARIA role:  role=button[name="Submit"]
    if selector.startswith('role='):
        return _by_role(soup, selector)

    # 3. Text:  text=Sign In  |  "Sign In"
    if selector.startswith('text=') or re.fullmatch(r'".*"', selector):
        text = selector.removeprefix('text=').strip('"')
        return _by_text(soup, text, exact=True) or _by_text(soup, text, exact=False)

    # 4. Named attribute selectors
    for prefix, attr in [
        ('placeholder=', 'placeholder'),
        ('alt=',         'alt'),
        ('title=',       'title'),
    ]:
        if selector.startswith(prefix):
            val = selector.removeprefix(prefix)
            return soup.find(attrs={attr: re.compile(re.escape(val), re.I)})

    if selector.startswith('label='):
        return _by_label(soup, selector.removeprefix('label='))

    # 5. CSS selector catch-all
    try:
        results = soup.select(selector)
        return results[0] if results else None
    except Exception:
        return None


def _by_role(soup, selector: str):
    m = re.match(r'role=(\w+)(?:\[name=["\']?(.*?)["\']?\])?', selector)
    if not m:
        return None
    role, name = m.group(1), m.group(2)
    for el in soup.find_all(attrs={"role": role}):
        if not name:
            return el
        accessible_name = el.get("aria-label", "") + el.get_text(strip=True)
        if re.search(re.escape(name), accessible_name, re.I):
            return el
    return None


def _by_text(soup, text: str, exact: bool):
    if exact:
        node = soup.find(string=lambda s: s and s.strip() == text)
    else:
        node = soup.find(string=re.compile(re.escape(text), re.I))
    return node.parent if node else None


def _by_label(soup, label_text: str):
    label = soup.find(string=re.compile(re.escape(label_text), re.I))
    if not label:
        return None
    label_tag = label.parent
    for_id = label_tag.get("for")
    if for_id:
        return soup.find(id=for_id)
    return label_tag.find(["input", "select", "textarea"])


# ── Error clue fallback ────────────────────────────────────────────────────────

def _resolve_from_error(soup, error: str):
    for clue in re.findall(r"'(.*?)'", error):
        if len(clue) < 3:
            continue
        if clue.startswith('#'):
            el = soup.find(id=clue[1:])
        elif clue.startswith('.'):
            el = soup.find(class_=clue[1:])
        else:
            node = soup.find(string=re.compile(re.escape(clue), re.I))
            el = node.parent if node else None
        if el:
            return el
    return None


# ── DOM helpers ────────────────────────────────────────────────────────────────

def _climb_to_container(node):
    structural = {'form', 'main', 'section', 'article', 'div', 'body', 'header', 'nav', 'ul', 'table'}
    while node and node.name not in structural and node.parent:
        node = node.parent
    return node