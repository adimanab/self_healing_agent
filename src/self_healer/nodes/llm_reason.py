import json
from langchain_core.messages import HumanMessage, SystemMessage
from ..state import AgentState
from ..config import get_api_key, get_base_url, get_model_name, get_temperature
from langchain_openai import ChatOpenAI


def _get_llm():
    """Lazy-initialise the LLM so env vars are read at call time, not import time."""
    return ChatOpenAI(
        model=get_model_name(),
        base_url=get_base_url(),
        api_key=get_api_key(),
        temperature=get_temperature(),
    )


def reason_and_suggest(state: AgentState) -> dict:
    messages = state.get("messages", [])
    new_messages = []

    if not messages:
        is_xpath = state.get("is_xpath", False)
        xpath_candidates = state.get("xpath_candidates") or []

        if is_xpath:
            sys_prompt = SystemMessage(content="""
You are an expert Test Automation AI validating a suggested XPath repair.
A previous agent has already analyzed the DOM and suggested a fix.

Your task:
1. Review the suggested XPath against the DOM and the original intent.
2. If the suggestion is correct, confirm it.
3. If it can be improved, provide a better one.
4. If it is wrong, provide the correct XPath using relational anchoring:
   - data-testid / data-cy        → Primary choice
   - aria-label                   → Accessibility-based  
   - Stable text anchor + axes    → ancestor, following-sibling
   - placeholder / label relation → For inputs

REPLY ONLY WITH JSON:
{
  "suggestion": "confirmed or improved xpath",
  "reason": "why this xpath is correct or what was wrong with the previous one",
  "confidence": 0-100,
  "intent": "brief description of action"
}
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

REPLY ONLY WITH JSON:
{
  "suggestion": "the corrected xpath",
  "reason": "explanation of the relational bridge used",
  "confidence": "how much it is in 0-100 range",
  "intent": "brief description of action"
}
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

        if is_xpath:
            task_prompt = HumanMessage(content=f"""
Test Name : {state['test_name']}
Selector  : {state['selector']}
Error     : {state['error']}
DOM       : {state['dom_context']}
xpath      : {state['suggestion']}
confidence : {state['confidence']}
reason     : {state['reason']}
intent : {state.get('intent', 'Unknown')}
{xpath_section}
""")
        else:
            task_prompt = HumanMessage(content=f"""
Test Name : {state['test_name']}
Selector  : {state['selector']}
Error     : {state['error']}
DOM       : {state['dom_context']}
{xpath_section}
""")

        messages = [sys_prompt, task_prompt]
        new_messages.extend(messages)

    llm = _get_llm()
    response = llm.invoke(messages)
    new_messages.append(response)

    # print("RESPONSE CONTENT: ", response.content)
    
    parsed = _parse_llm_output(response.content)

    # print("What is going: ", parsed)
    suggestion = parsed.get("suggestion")
    reason = parsed.get("reason")
    confidence = parsed.get("confidence")

    state["suggestion"] = suggestion
    state["confidence"] = confidence
    state["reason"] = reason
    state["messages"] = new_messages
    # print("=== what is going ===")
    # print(f"xpath      : {state['suggestion']} : {suggestion}")
    # print(f"confidence : {state['confidence']} : {confidence}")
    # print(f"reason     : {state['reason']}: {reason}")
    return state

def _parse_llm_output(content: str) -> dict:
    try:
        # Remove markdown fences if present
        clean = content.strip().replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean)

        # Handle the LLM returning a list for "suggestion" or "selector"
        suggestion = parsed.get("suggestion") or parsed.get("selector")
        if isinstance(suggestion, list) and len(suggestion) > 0:
            suggestion = suggestion[0]
        elif not suggestion:
            suggestion = "No suggestion available"

        # Normalize confidence to 0.0 - 1.0 range
        conf = parsed.get("confidence", 0.0)

        return {
            "suggestion": suggestion,
            "reason":     parsed.get("reason") or "No reason provided",
            "confidence": float(conf),
            "intent":     parsed.get("intent", "Unknown")
        }

    except (json.JSONDecodeError, ValueError):
        return {
            "suggestion": "Failed to parse LLM output",
            "reason":     "The LLM response was not valid JSON",
            "confidence": 0.0,
            "intent":     "Unknown"
        }