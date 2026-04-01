from bs4 import BeautifulSoup, Tag
from lxml import etree
import re

# Only tags that matter for XPath healing — cuts token usage drastically
INTERACTIVE_TAGS = {
    "a", "button", "input", "select", "textarea",
    "form", "label", "nav", "header", "main", "section"
}

_MAX_ELEMENTS = 60
_MAX_ATTR_VALUE_LEN = 50

# Step 1 — Priority attributes only, in order of LLM usefulness
PRIORITY_ATTRS = [
    "data-testid", "data-cy", "aria-label", "id",
    "name", "type", "role", "placeholder", "href", "class"
]

def _summarise_dom(raw_html: str, failed_selector: str = "") -> str:
    """
    Produces a compact DOM summary anchored to the failure site.

    Strategy (in order of preference):
      1. Parse the failed XPath, walk up its axes to find the deepest
         resolvable ancestor in the live DOM — use that subtree.
      2. Extract section-level keywords from the selector (e.g. 'login',
         'checkout') and find the nearest landmark region by id/class/role.
      3. Fall back to global scan (original behaviour) only as last resort.
    """
    try:
        parser = etree.HTMLParser()
        tree = etree.fromstring(raw_html.encode(), parser)
    except Exception:
        return "<empty/>"

    root = _find_anchor_node(tree, failed_selector)

    # Serialise the anchor subtree into the flat summary format
    lines: list[str] = []
    for el in root.iter():
        if el.tag not in INTERACTIVE_TAGS:
            continue
        if len(lines) >= _MAX_ELEMENTS:
            lines.append(f"... truncated after {_MAX_ELEMENTS} elements ...")
            break
        lines.append(_format_element_lxml(el))

    return "\n".join(lines) if lines else "<empty/>"


def _find_anchor_node(tree, failed_selector: str):
    """
    Returns the tightest DOM node that still contains the failure site.

    1. Try progressively-stripped versions of the XPath until one resolves.
    2. If nothing resolves, search for semantic keywords from the selector.
    3. Fall back to document body.
    """
    body = tree.find(".//body") or tree

    if not failed_selector:
        return body

    # --- Strategy 1: walk up the XPath axes ---
    ancestor = _resolve_closest_ancestor(tree, failed_selector)
    if ancestor is not None:
        return ancestor

    # --- Strategy 2: keyword heuristic ---
    keywords = _extract_keywords(failed_selector)
    if keywords:
        landmark = _find_landmark(tree, keywords)
        if landmark is not None:
            return landmark

    return body


def _resolve_closest_ancestor(tree, xpath: str):
    """
    Strips the rightmost XPath step one-by-one until the expression
    resolves to at least one node, then returns that node.

    //form[@id='checkout']//button[@type='submit']
      → try full               → None (element gone)
      → try //form[@id='checkout']  → found → return <form>
    """
    # Split on // or / but keep the delimiters so we can reassemble
    parts = re.split(r'(?=//|/(?!/))', xpath)
    parts = [p for p in parts if p]  # drop empty strings

    for end in range(len(parts), 0, -1):
        candidate = "".join(parts[:end])
        # Skip trivially short fragments like just '//' or '/'
        if len(candidate.strip("/")) < 2:
            continue
        try:
            results = tree.xpath(candidate)
            if results:
                return results[0]
        except etree.XPathEvalError:
            continue
    return None


def _extract_keywords(selector: str) -> list[str]:
    """Pull meaningful words from an XPath for landmark searching."""
    # Grab values inside quotes: @id='login-form' → ['login-form', 'login', 'form']
    quoted = re.findall(r"['\"]([^'\"]+)['\"]", selector)
    words: list[str] = []
    for q in quoted:
        words.append(q)
        words.extend(re.split(r"[-_\s]+", q))
    # Also grab tag names: //form//button → ['form', 'button']
    words += re.findall(r'/(\w+)', selector)
    return [w.lower() for w in words if len(w) > 2]


def _find_landmark(tree, keywords: list[str]):
    """
    Find the nearest container whose id, class, or role matches any keyword.
    Prefers the deepest (most specific) match.
    """
    LANDMARK_TAGS = {"form", "section", "main", "nav", "header", "div", "article"}
    best: tuple[int, any] | None = None  # (depth, node)

    for el in tree.iter():
        if el.tag not in LANDMARK_TAGS:
            continue
        attrs = " ".join([
            el.get("id", ""),
            " ".join(el.get("class", "").split()),
            el.get("role", ""),
            el.get("aria-label", ""),
        ]).lower()
        if any(kw in attrs for kw in keywords):
            depth = sum(1 for _ in el.iterancestors())
            if best is None or depth > best[0]:
                best = (depth, el)

    return best[1] if best else None


def _format_element_lxml(el) -> str:
    """lxml-native equivalent of the BeautifulSoup _format_attrs + text."""
    parts = []
    seen: set[str] = set()
    for attr in PRIORITY_ATTRS + list(el.attrib.keys()):
        if attr in seen:
            continue
        seen.add(attr)
        val = el.get(attr)
        if val is None:
            continue
        val_str = val.replace("\n", " ").strip()
        if len(val_str) > _MAX_ATTR_VALUE_LEN:
            val_str = val_str[:_MAX_ATTR_VALUE_LEN] + "..."
        parts.append(f'{attr}="{val_str}"')
    attrs_str = (" " + " ".join(parts)) if parts else ""

    direct_text = (el.text or "").strip()[:60]
    tag = el.tag

    if direct_text:
        return f"<{tag}{attrs_str}>{direct_text}</{tag}>"
    return f"<{tag}{attrs_str} />"


#classify the failure type
def _classify_failure(error_msg: str) -> str:
    if any(k in error_msg.lower() for k in ["timeout", "not found", "stale"]):
        return "timing"
    if any(k in error_msg.lower() for k in ["no such element", "unable to locate"]):
        return "structure_changed"
    return "unstable_attr"  # default