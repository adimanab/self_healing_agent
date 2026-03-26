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
playwright install chromium
```

### Step 2: Set Environment Variables

```bash
# Required
export GROQ_API_KEY="gsk_your_api_key_here"

# Optional (these have defaults)
export GROQ_BASE_URL="https://api.groq.com/openai/v1"
export SELF_HEAL_MODEL="llama-3.3-70b-versatile"
export SELF_HEAL_TEMPERATURE="0.4"
```

On Windows (PowerShell):
```powershell
$env:GROQ_API_KEY = "gsk_your_api_key_here"
```

### Step 3: Add to your conftest.py

```python
# conftest.py
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
pytest -v -s
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
| `GROQ_API_KEY` | ✅ | — | Your Groq API key |
| `GROQ_BASE_URL` | ❌ | `https://api.groq.com/openai/v1` | API endpoint URL |
| `SELF_HEAL_MODEL` | ❌ | `llama-3.3-70b-versatile` | LLM model name |
| `SELF_HEAL_TEMPERATURE` | ❌ | `0.4` | LLM temperature (0.0–1.0) |

---

## 🏗️ How It Works

```
Test Fails (broken selector)
        │
        ▼
┌─────────────────┐
│  Detect Failure  │  pytest hook intercepts the error
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│  DOM Extractor   │────▶│  XPath Builder    │  (for dynamic sites)
└────────┬────────┘     └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌──────────────────┐
         │  LLM Reasoning   │  Groq / LLaMA analyzes intent + DOM
         └────────┬─────────┘
                  ▼
         ┌──────────────────┐
         │  File Locator    │  Finds the exact file:line of the selector
         └────────┬─────────┘
                  ▼
         ┌──────────────────┐
         │  Human Approval  │  Rich TUI: Accept / Reject / Copy
         └────────┬─────────┘
                  ▼
         ┌──────────────────┐
         │  Apply Fix       │  Edits the source file + opens editor
         └─────────────────┘
```

---

## 📦 For Package Developers

### Building from source

```bash
git clone https://github.com/your-username/self-healer.git
cd self-healer
pip install build
python -m build
```

### Publishing to PyPI

```bash
# Test on TestPyPI first
pip install twine
twine upload --repository testpypi dist/*

# Then publish to real PyPI
twine upload dist/*
```

### Running the example project

```bash
pip install -e .
playwright install chromium
export GROQ_API_KEY="gsk_..."
pytest examples/saucedemo/tests/ -v -s
```

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or pull request.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.