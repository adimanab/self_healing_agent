import re
import pytest
from dataclasses import dataclass
from playwright.sync_api import sync_playwright

# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class ErrorReport:
    test_name: str
    selector:  str
    error:     str

# ── Session-level storage ─────────────────────────────────────────────────────

_error_reports: list[ErrorReport] = []

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def error_store() -> list[ErrorReport]:
    """Shared list that accumulates ErrorReport objects across the session."""
    return _error_reports


@pytest.fixture(scope="session")
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.saucedemo.com/")
        yield page
        browser.close()

# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_selector(exc_value: BaseException, item) -> str:
    """
    Try to pull the selector out of a Playwright error message first.
    Playwright errors typically look like:
        'locator.click: ... waiting for locator("#btn")...'
    Falls back to item._current_selector if set by the test, then 'unknown'.
    """
    # Check if the test set a selector explicitly
    manual = getattr(item, "_current_selector", None)
    if manual:
        return manual

    # Try to parse it from the Playwright exception message
    msg = str(exc_value)
    match = re.search(r'locator\("([^"]+)"\)|locator\(\'([^\']+)\'\)', msg)
    if match:
        return match.group(1) or match.group(2)

    return "unknown"


# ── Hook: capture failures automatically ─────────────────────────────────────
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report  = outcome.get_result()

    # Only act on the *call* phase (not setup/teardown) when the test failed
    if call.when != "call" or not report.failed:
        return

    exc       = call.excinfo
    error_msg = str(exc.value) if exc else "Unknown error"
    selector  = _extract_selector(exc.value, item) if exc else "unknown"

    report_obj = ErrorReport(
        test_name = item.nodeid,
        selector  = selector,
        error     = error_msg,
    )
    _error_reports.append(report_obj)

    # Attach a human-readable summary to the pytest terminal output
    report.sections.append((
        "Error Report",
        f"test_name : {report_obj.test_name}\n"
        f"selector  : {report_obj.selector}\n"
        f"error     : {report_obj.error}",
    ))
    print("\n\n_error_reports: ", _error_reports)