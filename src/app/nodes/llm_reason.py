import os
import json
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
load_dotenv(override=True)
from src.app.state import AgentState
from langchain_openai import ChatOpenAI


llm = ChatOpenAI(
    model="llama-3.3-70b-versatile",
    base_url=os.getenv("GROQ_BASE_URL"),
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.4
)


def reason_and_suggest(state: AgentState) -> dict:
    messages = state.get("messages", [])
    new_messages = []

    if not messages:
        is_dynamic = state.get("is_dynamic", False)
        xpath_candidates = state.get("xpath_candidates") or []

        # ── 1. SYSTEM PROMPT ─────────────────────────────────────────────────
        if is_dynamic:
            sys_prompt = SystemMessage(content="""
You are an expert Test Automation AI specialized in healing broken Playwright selectors
on DYNAMIC websites (React, Vue, Angular, Next.js).

These sites auto-generate class names and IDs that change on every deploy.
CSS selectors based on those will keep breaking. Your job is to suggest STABLE alternatives.

Selector stability ranking (prefer top):
  1. data-testid / data-cy / data-test-id  →  set by devs, never auto-generated
  2. aria-label                             →  accessibility attr, very stable
  3. visible text content                   →  //button[text()='Submit']
  4. placeholder                            →  //input[@placeholder='Email']
  5. label relationship                     →  //label[text()='Email']/following-sibling::input
  6. type attribute                         →  //input[@type='email']
  7. CSS with semantic class (not hashed)   →  .login-form button

Your task:
  1. Analyze why the selector failed (auto-generated ID/class, element not yet rendered, etc.)
  2. Review the pre-computed XPath candidates provided — evaluate each for stability
  3. Also look at the DOM directly for any stable attributes you can use
  4. Return the best 2-3 selectors ranked by stability, mixing XPath and CSS as appropriate

Respond with ONLY a JSON object with these exact keys:
  - "suggestion": single best selector (string) — for backward compatibility
  - "reason": why the original failed and how you chose the fix
  - "confidence": float 0.0-1.0
  - "step_passed": false
  - "ranked_selectors": list of objects, each with:
      - "selector": the selector string
      - "type": "xpath" or "css"
      - "confidence": float 0.0-1.0
      - "reason": one-line explanation of why this selector is stable

No extra text. No markdown fences.
""")
        else:
            # ── original static site prompt — completely unchanged ────────────
            sys_prompt = SystemMessage(content="""
You are an expert Test Automation AI specialized in healing broken Playwright selectors.
You will receive a failing selector, the Playwright error, and the most relevant DOM subtree.

Your task:
1. Analyze why the selector failed (typo, wrong class name, etc.)
2. Look at available classes/IDs in the DOM and find similar ones
3. Suggest the CORRECT selector that exists in the actual DOM
4. Explain the issue and your reasoning

Respond with ONLY a JSON object with these exact keys:
  - "suggestion": corrected Playwright selector (must exist in the provided DOM)
  - "reason":     detailed explanation of why the original failed and how you found the correction
  - "confidence": float 0.0-1.0 (high if you found exact match in DOM, lower if guessing)
  - "step_passed": false

No extra text. No markdown fences. Be precise with the class names and selectors.
""")

        # ── 2. TASK PROMPT ────────────────────────────────────────────────────
        xpath_section = ""
        if xpath_candidates:
            ranked = "\n".join(
                f"  {i+1}. {x}" for i, x in enumerate(xpath_candidates)
            )
            xpath_section = f"""
XPath Candidates (pre-computed, ranked by stability — evaluate each):
{ranked}
"""

        task_prompt = HumanMessage(content=f"""
Test Name : {state['test_name']}
Selector  : {state['selector']}
Error     : {state['error']}
DOM       : {state['dom_context']}
{xpath_section}
""")

        print("yeh gaaya llm main: ", state["dom_context"])

        messages = [sys_prompt, task_prompt]
        new_messages.extend(messages)

    response = llm.invoke(messages)
    new_messages.append(response)

    return {
        "messages": new_messages,
        **_parse_llm_output(response.content),
    }


def _parse_llm_output(content: str) -> dict:
    try:
        clean = content.strip().removeprefix("```json").removesuffix("```").strip()
        parsed = json.loads(clean)

        # ── 3. PARSE ranked_selectors if present ─────────────────────────────
        raw_ranked = parsed.get("ranked_selectors")
        ranked_selectors = None
        if isinstance(raw_ranked, list):
            ranked_selectors = [
                {
                    "selector":   str(item.get("selector", "")),
                    "type":       str(item.get("type", "css")),
                    "confidence": float(item.get("confidence", 0.0)),
                    "reason":     str(item.get("reason", "")),
                }
                for item in raw_ranked
                if isinstance(item, dict) and item.get("selector")
            ]

        return {
            "suggestion":       parsed.get("suggestion"),
            "reason":           parsed.get("reason"),
            "confidence":       float(100 * float(parsed.get("confidence", 0.0))),
            "step_passed":      bool(parsed.get("step_passed", False)),
            "ranked_selectors": ranked_selectors,   # None for static sites
        }

    except (json.JSONDecodeError, ValueError):
        return {
            "suggestion":       content,
            "reason":           "Failed to parse structured output from LLM",
            "confidence":       0.0,
            "step_passed":      False,
            "ranked_selectors": None,
        }