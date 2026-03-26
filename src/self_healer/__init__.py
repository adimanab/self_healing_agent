"""
self_healer — AI-powered self-healing pytest plugin for Playwright.

Automatically detects broken selectors in your Playwright tests and uses
LLM reasoning to suggest (and optionally apply) fixes.

Usage:
    pip install self-healer
    export GROQ_API_KEY="gsk_..."
    pytest -v -s

Public API:
    - run_healing_agent()   — invoke the agent programmatically
    - enable_healing(page)  — patch a Playwright page for selector tracking
"""

__version__ = "0.1.0"

from .main import run_healing_agent
from .plugin import enable_healing

__all__ = ["run_healing_agent", "enable_healing", "__version__"]
