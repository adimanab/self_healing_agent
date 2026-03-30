# scripts/check_xpath_builder.py
import sys, os

from src.self_healer.nodes.xpath_builder import xpath_builder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


fixture_path = os.path.join(
    os.path.dirname(__file__), '..',
    'src', 'automation', 'tests', 'fixtures', 'dynamic_page.html'
)
html = open(fixture_path).read()

# ── Test 1: dynamic=True, hashed CSS selector (the broken case) ──────────────
print("=" * 55)
print("Test 1: dynamic site, broken hashed class selector")
print("=" * 55)
state = {
    "selector":    ".sc-btn-hAsH3",        # broken hashed class
    "error":       "Timeout 30000ms exceeded",
    "dom_context": html,
    "is_xpath":  True,
    "xpath_candidates": [],
}
result = xpath_builder(state)
candidates = result["xpath_candidates"]
print(f"Candidates found: {len(candidates)}")
for i, c in enumerate(candidates):
    print(f"  {i+1}. {c}")
print("PASS" if len(candidates) > 0 else "FAIL — no candidates generated")

print()

# ── Test 2: dynamic=False, must be skipped entirely ──────────────────────────
print("=" * 55)
print("Test 2: static site, xpath_builder must be skipped")
print("=" * 55)
state2 = {
    "selector":    "#submit-btn",
    "error":       "Timeout",
    "dom_context": html,
    "is_xpath":  False,
    "xpath_candidates": [],
}
result2 = xpath_builder(state2)
print(f"Candidates: {result2['xpath_candidates']}")
print("PASS" if result2["xpath_candidates"] == [] else "FAIL — should be empty for static")

print()

# ── Test 3: check stability ordering ─────────────────────────────────────────
print("=" * 55)
print("Test 3: data-testid must be first candidate")
print("=" * 55)
if candidates:
    first = candidates[0]
    print(f"First candidate: {first}")
    is_testid_first = "data-testid" in first or "data-cy" in first or "aria-label" in first
    print("PASS" if is_testid_first else "FAIL — most stable attr should be first")
else:
    print("SKIP — no candidates from Test 1")