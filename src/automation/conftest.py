# ── [1] IMPORTS ───────────────────────────────────────────────────────────────
import re
import sys
import os
import pytest
from dataclasses import dataclass, field
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.app.main import run_healing_agent  # ← swap this import when packaged


# ── [2] DATA MODEL ────────────────────────────────────────────────────────────
# future: reporter.py → ErrorReport, store(), get_all()

@dataclass
class ErrorReport:
    test_name: str
    selector:  str
    error:     str

_error_reports: list[ErrorReport] = []


# ── [3] STATE ─────────────────────────────────────────────────────────────────
# future: tracker.py → record_empty(), get_last_empty(), clear()

_current_page     = None
_selector_tracker = {}

def _tracker_record_empty(selector: str):
    _selector_tracker['last_empty_selector'] = selector
    _selector_tracker['last_empty_error']    = f"Selector '{selector}' returned no elements"

def _tracker_get_last_empty() -> str | None:
    return _selector_tracker.get('last_empty_selector')

def _tracker_clear():
    _selector_tracker.clear()


# ── [4] BROWSER FIXTURE ───────────────────────────────────────────────────────
# future: page_fixture.py → session-scoped browser factory
# Session-scoped so the browser stays alive when the pytest hook fires after tests

@pytest.fixture(scope="session")
def browser_instance():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        yield browser
        browser.close()


# ── [5] PAGE FIXTURE ──────────────────────────────────────────────────────────
# future: page_fixture.py → patch_page(), page fixture factory
# Patches the page's locator so empty results are tracked automatically

@pytest.fixture(scope="function")
def page(browser_instance):
    global _current_page

    pg = browser_instance.new_page()
    pg.goto("https://www.saucedemo.com/")
    _current_page = pg

    # ── locator patch ─────────────────────────────────────────────────────────
    # Intercepts locator calls to detect selectors that return empty results.
    # Add more method patches below if your page objects use other locator methods.
    original_locator = pg.locator

    def tracked_locator(selector, **kwargs):
        loc = original_locator(selector, **kwargs)

        # Patch: all_text_contents()
        _orig_all_text = loc.all_text_contents
        def tracked_all_text_contents():
            result = _orig_all_text()
            if not result:
                _tracker_record_empty(selector)
            return result
        loc.all_text_contents = tracked_all_text_contents

        # Patch: all()
        _orig_all = loc.all
        def tracked_all():
            result = _orig_all()
            if not result:
                _tracker_record_empty(selector)
            return result
        loc.all = tracked_all

        # Patch: all_inner_texts() ← used by get_cart_prices(), get_cart_names(), get_cart_desc()
        _orig_all_inner = loc.all_inner_texts
        def tracked_all_inner_texts():
            result = _orig_all_inner()
            if not result:
                _tracker_record_empty(selector)
            return result
        loc.all_inner_texts = tracked_all_inner_texts

        return loc

    pg.locator = tracked_locator

    yield pg
    pg.close()  # only closes the page, NOT the browser


# ── [6] SELECTOR UTILS ────────────────────────────────────────────────────────
# future: agent.py → extract_selector()

def _extract_selector(exc_value: BaseException, item) -> str:
    # Priority 1: manually set on the test item
    manual = getattr(item, "_current_selector", None)
    if manual:
        return manual

    # Priority 2: captured by the locator tracker
    if _tracker_get_last_empty():
        return _tracker_get_last_empty()

    # Priority 3: parse from the error message string
    match = re.search(
        r'locator\("([^"]+)"\)|locator\(\'([^\']+)\'\)',
        str(exc_value)
    )
    if match:
        return match.group(1) or match.group(2)

    return "unknown"


# ── [7] TRIGGER LOGIC ─────────────────────────────────────────────────────────
# future: agent.py → should_trigger(), trigger()

def _should_trigger_agent(error_msg: str) -> bool:
    # Strip ANSI color codes before matching
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    clean_msg = ansi_escape.sub('', error_msg)

    # Playwright timeout
    if "Timeout" in clean_msg:
        return True

    # Playwright locator error
    if "locator" in clean_msg.lower():
        return True

    # Assertion where actual value was an empty list  e.g. assert [] == [...]
    normalized = " ".join(clean_msg.split())
    if "AssertionError" in normalized and "assert []" in normalized:
        return True

    # Tracker caught an empty selector during the test
    if _tracker_get_last_empty():
        return True

    return False


def _trigger_agent(report_obj: ErrorReport):
    """
    Single place that calls run_healing_agent.
    When packaged: replace run_healing_agent with the user-supplied callable.
    """
    print(f"\n[self-healing] Triggering for : {report_obj.test_name}")
    print(f"[self-healing] Selector       : {report_obj.selector}")
    print(f"[self-healing] Error snippet  : {report_obj.error[:120]}")

    run_healing_agent(           # ← single line to swap when packaged
        test_name = report_obj.test_name,
        selector  = report_obj.selector,
        error     = report_obj.error,
        page      = _current_page,
    )


# ── [8] PYTEST HOOK ───────────────────────────────────────────────────────────
# future: hooks.py → pytest_runtest_makereport()

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report  = outcome.get_result()

    if call.when != "call" or not report.failed:
        return

    exc       = call.excinfo
    error_msg = str(exc.value) if exc else "Unknown error"
    selector  = _extract_selector(exc.value, item) if exc else "unknown"

    # Build and store the error report
    report_obj = ErrorReport(
        test_name = item.nodeid,
        selector  = selector,
        error     = error_msg,
    )
    _error_reports.append(report_obj)

    # Attach to pytest output
    report.sections.append((
        "Error Report",
        f"test_name : {report_obj.test_name}\n"
        f"selector  : {report_obj.selector}\n"
        f"error     : {report_obj.error}",
    ))

    # Decide whether to trigger the healing agent
    if _current_page and _should_trigger_agent(error_msg):
        try:
            _trigger_agent(report_obj)
        except Exception as e:
            print(f"\n[self-healing] Agent error: {e}")
        finally:
            _tracker_clear()
    else:
        # Debug output — remove when stable
        print(f"\n[self-healing] Agent NOT triggered.")
        print(f"  _current_page is None : {_current_page is None}")
        print(f"  should_trigger        : {_should_trigger_agent(error_msg)}")
        print(f"  error_msg snippet     : {repr(error_msg[:120])}")
        print(f"  tracker state         : {_selector_tracker}")