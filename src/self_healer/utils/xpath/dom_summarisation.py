from bs4 import BeautifulSoup, Tag
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

def _format_attrs(tag: Tag) -> str:
    """Step 2 — Formats only meaningful attributes, truncated cleanly."""
    parts = []
    seen = set()
    for attr in PRIORITY_ATTRS + list(tag.attrs.keys()):
        if attr in seen:
            continue
        seen.add(attr)
        val = tag.get(attr)
        if val is None:
            continue
        if isinstance(val, list):
            val = " ".join(val)
        val_str = str(val).replace("\n", " ").strip()
        if len(val_str) > _MAX_ATTR_VALUE_LEN:
            val_str = val_str[:_MAX_ATTR_VALUE_LEN] + "..."
        parts.append(f'{attr}="{val_str}"')
    return (" " + " ".join(parts)) if parts else ""


def _summarise_dom(raw_html: str) -> str:
    """
    Produces a compact, LLM-friendly summary of interactive DOM elements.

    Step 1 — Parse and scope to body only (skip <head> noise).
    Step 2 — Filter to interactive tags only (buttons, inputs, links, forms…).
    Step 3 — For each element, emit one clean line: tag + priority attrs + direct text.
    Step 4 — No positional XPaths. The LLM builds XPath from the attributes shown.
    Step 5 — Hard cap at _MAX_ELEMENTS with a truncation notice.
    """

    # Step 1 — scope to body
    soup = BeautifulSoup(raw_html, "html.parser")
    root = soup.body if soup.body else soup

    # Step 2 — filter to interactive tags only
    elements = [t for t in root.find_all(True) if t.name in INTERACTIVE_TAGS]

    lines: list[str] = []

    for tag in elements:
        # Step 5 — hard cap
        if len(lines) >= _MAX_ELEMENTS:
            lines.append(f"... truncated after {_MAX_ELEMENTS} elements ...")
            break

        # Step 3 — format attrs
        attrs_str = _format_attrs(tag)

        # Direct text only — not the full subtree text
        # Prevents a <form> from echoing all its children's text
        direct_text = "".join(
            s for s in tag.strings if s.parent == tag
        ).strip()[:60]

        # Step 4 — one clean line per element, no positional XPath
        if direct_text:
            lines.append(f"<{tag.name}{attrs_str}>{direct_text}</{tag.name}>")
        else:
            lines.append(f"<{tag.name}{attrs_str} />")

    return "\n".join(lines) if lines else "<empty/>"

#classify the failure type
def _classify_failure(error_msg: str) -> str:
    if any(k in error_msg.lower() for k in ["timeout", "not found", "stale"]):
        return "timing"
    if any(k in error_msg.lower() for k in ["no such element", "unable to locate"]):
        return "structure_changed"
    return "unstable_attr"  # default