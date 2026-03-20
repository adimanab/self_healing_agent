import re
from bs4 import BeautifulSoup
from src.app.state import AgentState
from difflib import get_close_matches


# ── Public node ────────────────────────────────────────────────────────────────

def dom_extractor(state: AgentState) -> dict:
    selector    = state["selector"]
    error       = state["error"]
    dom_context = state["dom_context"]

    soup = BeautifulSoup(dom_context, 'html.parser')

    # Try both resolution strategies; prefer the more specific result
    node = _resolve_playwright_selector(soup, selector)
    if node is None:
        node = _resolve_from_error(soup, error)

    if node:
        container = _climb_to_container(node, max_levels=4)
        focused_dom = _safe_serialize(container, char_limit=5000)
    else:
        focused_dom = _safe_serialize(soup.body, char_limit=3000)

    hints = _build_selector_hints(soup, selector)
    return {
        "dom_context": focused_dom + hints
    }


# ── Selector hints ─────────────────────────────────────────────────────────────

def _build_selector_hints(soup, selector: str) -> str:
    """
    Extract rich selector hints regardless of selector type.
    Fuzzy-matches against classes, IDs, data-testids, aria-labels, and text.
    """
    # Collect candidate strings by attribute type
    all_classes     = set()
    all_ids         = set()
    all_testids     = set()
    all_aria_labels = set()
    all_names       = set()

    for el in soup.find_all(True):
        for cls in (el.get('class') or []):
            all_classes.add(cls)
        if el.get('id'):
            all_ids.add(el['id'])
        if el.get('data-testid'):
            all_testids.add(el['data-testid'])
        if el.get('aria-label'):
            all_aria_labels.add(el['aria-label'])
        if el.get('name'):
            all_names.add(el['name'])

    # Extract the "needle" from the selector
    needle = _extract_needle(selector)
    if not needle:
        return ""

    lines = ["\n\n=== SELECTOR HINTS ==="]
    lines.append(f"Failed selector: {selector}")

    def fuzzy(pool, label):
        matches = get_close_matches(needle, list(pool), n=5, cutoff=0.55)
        if matches:
            lines.append(f"Similar {label}: {matches}")

    fuzzy(all_classes,     "classes")
    fuzzy(all_ids,         "IDs")
    fuzzy(all_testids,     "data-testids")
    fuzzy(all_aria_labels, "aria-labels")
    fuzzy(all_names,       "name attrs")

    # Always list all data-testids — they're the most actionable for Playwright
    if all_testids:
        lines.append(f"All data-testids: {sorted(all_testids)}")

    return "\n".join(lines)


def _extract_needle(selector: str) -> str:
    """Pull the meaningful token out of any selector type."""
    if selector.startswith('.'):
        return selector[1:]
    if selector.startswith('#'):
        return selector[1:]
    if selector.startswith('text='):
        return selector.removeprefix('text=').strip('"\'')
    if selector.startswith('role='):
        m = re.search(r'name=["\']?(.*?)["\']?\]', selector)
        return m.group(1) if m else ""
    # data-testid, aria-label, etc. — pull value from [attr="value"]
    m = re.search(r'\[[\w-]+=["\'](.*?)["\']\]', selector)
    if m:
        return m.group(1)
    # Bare CSS class in compound selectors: div.foo → foo
    m = re.search(r'\.([a-zA-Z][\w-]*)', selector)
    if m:
        return m.group(1)
    return selector  # fallback: treat whole thing as needle


# ── Playwright selector resolution ─────────────────────────────────────────────

def _resolve_playwright_selector(soup, selector: str):
    if selector.startswith('#'):
        return soup.find(id=selector[1:])
    if selector.startswith('role='):
        return _by_role(soup, selector)
    if selector.startswith('text=') or re.fullmatch(r'".*"', selector):
        text = selector.removeprefix('text=').strip('"')
        return _by_text(soup, text, exact=True) or _by_text(soup, text, exact=False)
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
    # Match single quotes, double quotes, and backticks
    clues = re.findall(r"['\"](.*?)['\"]", error)
    # Filter out noise words that Playwright injects
    noise = {'strict mode', 'timeout', 'expected', 'visible', 'hidden', 'enabled', 'disabled'}
    for clue in clues:
        if len(clue) < 3 or clue.lower() in noise:
            continue
        if clue.startswith('#'):
            el = soup.find(id=clue[1:])
        elif clue.startswith('.'):
            el = soup.find(class_=clue[1:])
        elif '=' in clue:
            # skip Playwright meta-syntax like role=button
            continue
        else:
            node = soup.find(string=re.compile(re.escape(clue), re.I))
            el = node.parent if node else None
        if el:
            return el
    return None


# ── DOM helpers ────────────────────────────────────────────────────────────────

def _climb_to_container(node, max_levels: int = 4):
    """
    Walk up to a meaningful structural container, but stop after max_levels
    to avoid over-climbing to <body> and losing context.
    """
    structural = {'form', 'main', 'section', 'article', 'header', 'nav', 'ul', 'table'}
    # Also stop at a div/body that has multiple children — it's a real container
    for _ in range(max_levels):
        if node.parent is None:
            break
        parent = node.parent
        if parent.name in structural:
            return parent
        if parent.name in ('div', 'body') and len(parent.find_all(recursive=False)) > 2:
            return parent
        node = parent
    return node


def _safe_serialize(node, char_limit: int) -> str:
    """
    Serialize a BS4 node without mid-tag truncation.
    Renders children one by one and stops before exceeding char_limit.
    """
    if node is None:
        return ""
    children = list(node.children)
    if not children:
        return str(node)[:char_limit]

    # Try full prettify first
    full = node.prettify()
    if len(full) <= char_limit:
        return full

    # Otherwise, add children until we're near the limit
    parts = [f"<{node.name}"]
    for attr, val in (node.attrs or {}).items():
        val_str = ' '.join(val) if isinstance(val, list) else val
        parts[0] += f' {attr}="{val_str}"'
    parts[0] += ">"

    budget = char_limit - len(parts[0]) - 20  # room for closing tag
    accumulated = 0
    for child in children:
        chunk = str(child)
        if accumulated + len(chunk) > budget:
            parts.append(f"<!-- truncated {len(children)} total children -->")
            break
        parts.append(chunk)
        accumulated += len(chunk)

    parts.append(f"</{node.name}>")
    return "".join(parts)
