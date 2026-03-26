"""
self_healer.plugin
==================
Pytest plugin that automatically activates the self-healing agent when a
Playwright test fails due to a broken selector.

Registration:
    This module is registered as a pytest plugin via the ``pytest11`` entry
    point in ``pyproject.toml``.  When a user installs ``self-healer`` and
    runs ``pytest``, these hooks and fixtures are auto-discovered — zero
    configuration required.

What it provides:
    1. ``enable_healing(page)`` — call this in your own ``page`` fixture to
       enable locator tracking on the page.
    2. ``pytest_runtest_makereport`` hook — intercepts test failures and
       triggers the healing agent when a selector-related error is detected.
"""

import re
from dataclasses import dataclass
import pytest

from .main import run_healing_agent


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class ErrorReport:
    test_name: str
    selector:  str
    error:     str


_error_reports: list[ErrorReport] = []


# ── Plugin State ──────────────────────────────────────────────────────────────

_current_page     = None
_selector_tracker = {}


def _tracker_record_empty(selector: str):
    _selector_tracker['last_empty_selector'] = selector
    _selector_tracker['last_empty_error']    = f"Selector '{selector}' returned no elements"


def _tracker_get_last_empty() -> str | None:
    return _selector_tracker.get('last_empty_selector')


def _tracker_clear():
    _selector_tracker.clear()


# ── Public API: enable_healing() ──────────────────────────────────────────────

def enable_healing(page):
    """
    Patch a Playwright page so that locator calls are tracked for empty results.

    Call this inside your own ``page`` fixture::

        import pytest
        from playwright.sync_api import sync_playwright
        from self_healer import enable_healing

        @pytest.fixture(scope="session")
        def browser_instance():
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                yield browser
                browser.close()

        @pytest.fixture(scope="function")
        def page(browser_instance):
            pg = browser_instance.new_page()
            enable_healing(pg)          # ← this line
            pg.goto("https://your-app.com")
            yield pg
            pg.close()
    """
    global _current_page
    _current_page = page

    original_locator = page.locator

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

        # Patch: all_inner_texts()
        _orig_all_inner = loc.all_inner_texts
        def tracked_all_inner_texts():
            result = _orig_all_inner()
            if not result:
                _tracker_record_empty(selector)
            return result
        loc.all_inner_texts = tracked_all_inner_texts

        return loc

    page.locator = tracked_locator
    return page


# ── Selector Extraction ──────────────────────────────────────────────────────

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


# ── Trigger Logic ─────────────────────────────────────────────────────────────

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
    """
    print(f"\n[self-healer] Triggering for : {report_obj.test_name}")
    print(f"[self-healer] Selector       : {report_obj.selector}")
    print(f"[self-healer] Error snippet  : {report_obj.error[:120]}")

    run_healing_agent(
        test_name = report_obj.test_name,
        selector  = report_obj.selector,
        error     = report_obj.error,
        page      = _current_page,
    )


# ── Pytest Hook ───────────────────────────────────────────────────────────────

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
            print(f"\n[self-healer] Agent error: {e}")
        finally:
            _tracker_clear()
    else:
        print(f"\n[self-healer] Agent NOT triggered.")
        print(f"  _current_page is None : {_current_page is None}")
        print(f"  should_trigger        : {_should_trigger_agent(error_msg)}")
        print(f"  error_msg snippet     : {repr(error_msg[:120])}")
        print(f"  tracker state         : {_selector_tracker}")
