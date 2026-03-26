import re
from difflib import get_close_matches


def extract_needle(selector: str) -> str:
    if selector.startswith('.'):
        return selector[1:]
    if selector.startswith('#'):
        return selector[1:]
    if selector.startswith('text='):
        return selector.removeprefix('text=').strip('"\'')
    if selector.startswith('role='):
        m = re.search(r'name=["\']?(.*?)["\']?\]', selector)
        return m.group(1) if m else ""
    m = re.search(r'\[[\w-]+=["\'](.*?)["\']\]', selector)
    if m:
        return m.group(1)
    m = re.search(r'\.([a-zA-Z][\w-]*)', selector)
    if m:
        return m.group(1)
    return selector


def climb_to_container(node, max_levels: int = 4):
    structural = {'form', 'main', 'section', 'article', 'header', 'nav', 'ul', 'table'}
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


def safe_serialize(node, char_limit: int) -> str:
    if node is None:
        return ""
    children = list(node.children)
    if not children:
        return str(node)[:char_limit]

    full = node.prettify()
    if len(full) <= char_limit:
        return full

    parts = [f"<{node.name}"]
    for attr, val in (node.attrs or {}).items():
        val_str = ' '.join(val) if isinstance(val, list) else val
        parts[0] += f' {attr}="{val_str}"'
    parts[0] += ">"

    budget = char_limit - len(parts[0]) - 20
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


def build_selector_hints(soup, selector: str) -> str:
    all_classes, all_ids, all_testids, all_aria_labels, all_names = set(), set(), set(), set(), set()

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

    needle = extract_needle(selector)
    if not needle:
        return ""

    lines = ["\n\n=== SELECTOR HINTS ===", f"Failed selector: {selector}"]

    def fuzzy(pool, label):
        matches = get_close_matches(needle, list(pool), n=5, cutoff=0.55)
        if matches:
            lines.append(f"Similar {label}: {matches}")

    fuzzy(all_classes,     "classes")
    fuzzy(all_ids,         "IDs")
    fuzzy(all_testids,     "data-testids")
    fuzzy(all_aria_labels, "aria-labels")
    fuzzy(all_names,       "name attrs")

    if all_testids:
        lines.append(f"All data-testids: {sorted(all_testids)}")

    return "\n".join(lines)