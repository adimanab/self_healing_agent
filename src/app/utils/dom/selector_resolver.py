import re
from bs4 import BeautifulSoup


def resolve_playwright_selector(soup, selector: str):
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


def resolve_from_error(soup, error: str):
    clues = re.findall(r"['\"](.*?)['\"]", error)
    noise = {'strict mode', 'timeout', 'expected', 'visible', 'hidden', 'enabled', 'disabled'}
    for clue in clues:
        if len(clue) < 3 or clue.lower() in noise:
            continue
        if clue.startswith('#'):
            el = soup.find(id=clue[1:])
        elif clue.startswith('.'):
            el = soup.find(class_=clue[1:])
        elif '=' in clue:
            continue
        else:
            node = soup.find(string=re.compile(re.escape(clue), re.I))
            el = node.parent if node else None
        if el:
            return el
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