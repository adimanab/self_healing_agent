# 🩺 Self-Healer

**AI-powered self-healing pytest plugin for Playwright** — automatically detects broken selectors in your tests and uses LLM reasoning to suggest (and optionally apply) fixes.

[![PyPI version](https://badge.fury.io/py/self-healer.svg)](https://pypi.org/project/self-healer/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ What It Does

When a Playwright test fails because a CSS selector or XPath no longer matches an element:

1. **Detects** the broken selector and extracts the relevant DOM context
2. **Reasons** about what the selector was supposed to do (using Groq/LLM)
3. **Suggests** a corrected selector with confidence score  
4. **Shows** a rich TUI panel with the suggestion
5. **Applies** the fix directly to your source code (with your approval!)

All of this happens **automatically** — just install and run your tests.

---

## 🚀 Quick Start

### Step 1: Install

```bash
pip install self-healer
```

### Step 2: Set Environment Variables

```python
# Required
API_KEY="sk_..."
LLM_MODEL="openai/gpt-4.1-mini"

# Optional (these have defaults)
BASE_URL="https://api.openai.com"
TEMPERATURE="0.4"
```

### Step 3: Add to your conftest.py

```python
# conftest.py
import pytest
from playwright.sync_api import sync_playwright

from dotenv import load_dotenv
load_dotenv()
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
    enable_healing(pg)                    # ← Enable self-healing
    pg.goto("https://your-app.com")
    yield pg
    pg.close()
```

### Step 4: Write Tests (normal Playwright)

```python
# tests/test_login.py
from playwright.sync_api import Page

def test_login(page: Page):
    page.fill("#user-name", "admin")
    page.fill("#password", "secret")
    page.click("#login-button")
    assert "dashboard" in page.url
```

### Step 5: Run

```bash
pytest -v
```

If `#login-button` changes to `#btn-login`, the agent will:
- Detect the failure
- Analyze the live DOM  
- Suggest `#btn-login` with high confidence
- Ask you to **Accept**, **Reject**, or **Copy** the fix

---

## ⚙️ Configuration

All configuration is via environment variables — no config files needed.

| Variable | Required | Default | Description |
|---|---|---|---|
| `API_KEY` | ✅ | — | Your API key |
| `LLM_MODEL` | ✅ | — | LLM model name |
| `BASE_URL` | ❌ | `https://api.openai.com` | API endpoint URL |
| `TEMPERATURE` | ❌ | `0.4` | LLM temperature (0.0–1.0) |

---

## 🏗️ How It Works

```
                Test Fails (broken selector)
                    │
                    ▼
            ┌─────────────────┐
            │  Detect Failure │  pytest hook intercepts the error
            └────────┬────────┘
            ┌────────┴─────────┐
            ▼                  ▼
┌─────────────────┐     ┌──────────────────┐
│  DOM Extractor  │     │   XPath Builder  │  (for dynamic sites)
└────────┬────────┘     └────────┬─────────┘
         └───────────┬───────────┘
                     ▼
            ┌──────────────────┐
            │  LLM Reasoning   │  Groq/LLaMA analyzes intent + DOM
            └────────┬─────────┘
                     ▼
            ┌──────────────────┐
            │  File Locator    │  Finds exact file:line of selector
            └────────┬─────────┘
                     ▼
            ┌──────────────────┐
            │ Human Approval   │  Rich TUI: Accept / Reject / Copy
            └────────┬─────────┘
            ┌────────┴─────────┐
           Yes                 No
            │                  │
            ▼                  ▼
    ┌────────────────┐ ┌───────────────┐
    │    Apply Fix   │ │  Reject Fix   │
    └────┬───────────┘ └───────┬───────┘
         └──────────┬──────────┘
                    ▼
                ┌─────────┐
                │   END   │
                └─────────┘
```

---

## 📦 For Package Developers

### Building from source

```bash
git clone https://github.com/ankan01-cbnits/self_healing_agent.git
cd self-healing_agent
uv sync
uv build
```

### Publishing to PyPI

```bash
# Test on TestPyPI first
pip install twine
twine upload --repository testpypi dist/*

# Then publish to real PyPI
twine upload dist/*
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.