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

        # Inside reason_and_suggest(state: AgentState) in llm_reason.py

        if is_dynamic:
            sys_prompt = SystemMessage(content="""
You are an expert Test Automation AI specialized in healing broken Playwright selectors
on DYNAMIC websites.

CRITICAL STRATEGY: RELATIONAL ANCHORING
If the element being sought is a dynamic value (like a price, status, or date), 
DO NOT suggest a selector based on that value's text. Instead:
1. Identify a STABLE ANCHOR nearby (e.g., a Product Name or Label text).
2. Use XPath axes (ancestor, following-sibling, parent) to bridge from the 
Stable Anchor to the Dynamic Target.

Updated Stability Ranking:
1. data-testid / data-cy         →  Primary Choice
2. Relational Anchor             →  (e.g., //div[text()='Name']/ancestor::div//div[@class='price'])
3. aria-label                    →  Accessibility-based
4. placeholder                   →  For inputs
5. Label Relationship            →  //label[text()='Email']/following-sibling::input

Your task:
- Analyze the 'test_name' and 'selector' to understand the INTENT (e.g., if it's 'item_price', look for a price).
- If the original selector used 'ancestor' or 'sibling', preserve that relational logic in your fix.
- Return the best 2-3 selectors. Favor XPaths that use stable text anchors to find dynamic siblings.

REPLY ONLY WITH JSON:
{
  "suggestion": "the corrected xpath",
  "reason": "explanation of the relational bridge used",
  "confidence": "how much it is in 0-100 range",
  "intent": "brief description of action"
}
No extra text. No markdown fences. Be precise with the names and xpath.
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

#         task_prompt = HumanMessage(content=f"""
# Test Name : {state['test_name']}
# Selector  : {state['selector']}
# Error     : {state['error']}
# DOM       : {state['dom_context']}
# {xpath_section}
# """)

        if is_dynamic:
            task_prompt = HumanMessage(content=f"""
Test Name : {state['test_name']}
Selector  : {state['selector']}
Error     : {state['error']}
DOM       : {state['dom_context']}
xpath      : {state['suggestion']}
confidence : {state['confidence']}
reason     : {state['reason']}
intent     : {state['intent']}
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

        # print("yeh gaaya llm main: ", state["dom_context"])

        messages = [sys_prompt, task_prompt]
        new_messages.extend(messages)

    response = llm.invoke(messages)
    new_messages.append(response)

    # return {
    #     "messages": new_messages,
    #     **_parse_llm_output(response.content),
    # }

    print("RESPONSE CONTENT: ", response.content)
    
    parsed = _parse_llm_output(response.content)

    print("What is going: ", parsed)
    suggestion = parsed.get("suggestion")
    reason = parsed.get("reason")
    confidence = parsed.get("confidence")

    state["suggestion"] = suggestion
    state["confidence"] = confidence
    state["reason"] = reason

    print("=== what is going ===")
    print(f"xpath      : {state['suggestion']} : {suggestion}")
    print(f"confidence : {state['confidence']} : {confidence}")
    print(f"reason     : {state['reason']}: {reason}")
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
        # if conf > 1.0:
        #     conf = conf / 100.0

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