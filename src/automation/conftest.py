import re
import sys
import os
import pytest
from dataclasses import dataclass
from playwright.sync_api import sync_playwright

# ── path fix FIRST ────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# ── import entry point ────────────────────────────────────────────────────────
from src.app.main import run_healing_agent

# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class ErrorReport:
    test_name: str
    selector:  str
    error:     str

# ── Session storage ───────────────────────────────────────────────────────────

_error_reports: list[ErrorReport] = []
_current_page  = None

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def error_store() -> list[ErrorReport]:
    return _error_reports

@pytest.fixture(scope="session")
def page():
    global _current_page
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        pg      = browser.new_page()
        pg.goto("https://www.saucedemo.com/")
        _current_page = pg
        yield pg
        browser.close()

# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_selector(exc_value: BaseException, item) -> str:
    manual = getattr(item, "_current_selector", None)
    if manual:
        return manual
    msg   = str(exc_value)
    match = re.search(r'locator\("([^"]+)"\)|locator\(\'([^\']+)\'\)', msg)
    if match:
        return match.group(1) or match.group(2)
    return "unknown"

# ── Hook ──────────────────────────────────────────────────────────────────────

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report  = outcome.get_result()

    if call.when != "call" or not report.failed:
        return

    exc       = call.excinfo
    error_msg = str(exc.value) if exc else "Unknown error"
    selector  = _extract_selector(exc.value, item) if exc else "unknown"

    # ── build and store report ────────────────────────────────────────────────
    report_obj = ErrorReport(
        test_name = item.nodeid,
        selector  = selector,
        error     = error_msg,
    )
    _error_reports.append(report_obj)

    report.sections.append((
        "Error Report",
        f"test_name : {report_obj.test_name}\n"
        f"selector  : {report_obj.selector}\n"
        f"error     : {report_obj.error}",
    ))

    # ── invoke agent only for playwright timeout failures ─────────────────────
    if _current_page and ("Timeout" in error_msg or "locator" in error_msg.lower()):
        try:
            run_healing_agent(
                test_name = report_obj.test_name,
                selector  = report_obj.selector,
                error     = error_msg,
                page      = _current_page,
            )
        except Exception as e:
            print(f"\n[agent error] {e}")