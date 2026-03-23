from difflib import get_close_matches
from .dom_utils import extract_needle


def infer_fingerprint_from_selector(selector: str) -> dict:
    needle = extract_needle(selector).lower()

    common_fields = {
        'password': {'tag': 'input', 'type': 'password', 'associated_label': 'Password'},
        'username': {'tag': 'input', 'type': 'text',     'associated_label': 'Username'},
        'email':    {'tag': 'input', 'type': 'email',    'associated_label': 'Email'},
        'phone':    {'tag': 'input', 'type': 'tel',      'associated_label': 'Phone'},
        'search':   {'tag': 'input', 'type': 'search',   'associated_label': 'Search'},
        'submit':   {'tag': 'button', 'text_content': 'Submit'},
        'login':    {'tag': 'button', 'text_content': 'Login'},
    }

    matches = get_close_matches(needle, common_fields.keys(), n=1, cutoff=0.6)
    if matches:
        return common_fields[matches[0]]
    return {}


def find_by_fingerprint(soup, fingerprint: dict, cutoff: float = 0.6):
    if not fingerprint or not fingerprint.get('tag'):
        return None

    candidates = []
    for element in soup.find_all(fingerprint['tag']):
        score = _score_fingerprint_match(element, fingerprint)
        if score >= cutoff:
            candidates.append((element, score))

    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    return None


def _score_fingerprint_match(element, target: dict) -> float:
    score, max_score = 0.0, 0.0

    max_score += 2.0
    if element.get('type') == target.get('type'):
        score += 2.0

    max_score += 2.0
    if target.get('placeholder'):
        if element.get('placeholder') == target.get('placeholder'):
            score += 2.0
        elif target['placeholder'].lower() in (element.get('placeholder') or '').lower():
            score += 1.5

    max_score += 2.0
    if target.get('aria_label'):
        if element.get('aria-label') == target.get('aria_label'):
            score += 2.0

    max_score += 2.0
    if target.get('associated_label'):
        elem_label = ""
        if element.get('id'):
            lbl = element.find_previous('label', attrs={'for': element.get('id')})
            if lbl:
                elem_label = lbl.get_text(strip=True)
        if elem_label == target['associated_label']:
            score += 2.0
        elif target['associated_label'].lower() in elem_label.lower():
            score += 1.0

    max_score += 1.0
    if target.get('name_attr') and element.get('name') == target['name_attr']:
        score += 1.0

    max_score += 1.0
    if target.get('form_id'):
        form = element.find_parent('form')
        if form and form.get('id') == target['form_id']:
            score += 1.0

    return score / max_score if max_score > 0 else 0.0