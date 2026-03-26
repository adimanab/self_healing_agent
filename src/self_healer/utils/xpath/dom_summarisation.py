from bs4 import BeautifulSoup, Tag

_MAX_ELEMENTS = 100      # Slightly increased since we're capturing the whole tree
_MAX_ATTR_VALUE_LEN = 50 
_MAX_DEPTH = 10          # Prevent recursion depth issues in deeply nested SPAs

def _get_xpath(tag: Tag) -> str:
    """Generates a unique XPath for a given BeautifulSoup Tag."""
    path = []
    current = tag
    while current and current.name and current.name != '[document]':
        # Get siblings of the same name to determine index
        siblings = current.find_previous_siblings(current.name)
        index = len(siblings) + 1
        
        # If there are no siblings of the same name AND no future siblings, 
        # index [1] is often omitted in shorthand, but for LLMs, explicit is better.
        path.append(f"{current.name}[{index}]")
        current = current.parent
    
    return "/" + "/".join(reversed(path))

def _summarise_dom(raw_html: str) -> str:
    """
    Summarizes the entire DOM tree with XPaths and structural enrichment.
    """
    soup = BeautifulSoup(raw_html, "html.parser")
    # Focus on body to avoid head metadata unless specifically needed
    root = soup.body if soup.body else soup
    
    lines: list[str] = []
    
    # Using recursive=True to get all elements in depth-first order
    all_elements = root.find_all(True, recursive=True)

    for tag in all_elements:
        if len(lines) >= _MAX_ELEMENTS:
            lines.append(f"")
            break

        xpath = _get_xpath(tag)
        attrs_str = _format_attrs(tag)
        
        # Determine if the element is "leaf-like" or has direct text
        text = tag.get_text(separator=" ", strip=True)
        # Only include text if it's direct child text to keep it concise
        # (This prevents a <div> from repeating all the text of its 50 children)
        direct_text = "".join([t for t in tag.children if isinstance(t, str)]).strip()[:50]
        
        # Enrich the output with XPath and structural info
        lines.append(f"")
        if direct_text:
            lines.append(f"<{tag.name}{attrs_str}>{direct_text}</{tag.name}>")
        else:
            lines.append(f"<{tag.name}{attrs_str} />")

    return "\n".join(lines) if lines else ""

def _format_attrs(tag: Tag) -> str:
    parts: list[str] = []
    # Priority attributes that help an LLM identify elements quickly
    priority = ["id", "class", "name", "type", "role", "aria-label", "href", "data-testid"]

    seen = set()
    for attr in priority + list(tag.attrs.keys()):
        if attr in seen:
            continue
        seen.add(attr)
        
        val = tag.get(attr)
        if val is None:
            continue
            
        if isinstance(val, list):
            val = " ".join(val)
        
        # Clean and truncate
        val_str = str(val).replace('\n', ' ').strip()
        if len(val_str) > _MAX_ATTR_VALUE_LEN:
            val_str = val_str[:_MAX_ATTR_VALUE_LEN] + "..."
            
        parts.append(f' {attr}="{val_str}"')

    return "".join(parts)