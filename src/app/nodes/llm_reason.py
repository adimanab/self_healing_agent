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
# No tools bound — dom_extractor node already handled extraction
 

def reason_and_suggest(state: AgentState) -> dict:
    messages = state.get("messages", [])
    new_messages = []

    if not messages:
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

        task_prompt = HumanMessage(content=f"""
        Test Name : {state['test_name']}
        Selector  : {state['selector']}
        Error     : {state['error']}
        DOM       : {state['dom_context']}
        """)

        # print("yeh gaaya llm main: ", state["dom_context"])

        messages = [sys_prompt, task_prompt]
        new_messages.extend(messages)

    response = llm.invoke(messages)   # plain invoke, no tools needed
    new_messages.append(response)

    return {
        "messages":  new_messages,
        **_parse_llm_output(response.content),
    }


def _parse_llm_output(content: str) -> dict:
    try:
        clean = content.strip().removeprefix("```json").removesuffix("```").strip()
        parsed = json.loads(clean)
        return {
            "suggestion":  parsed.get("suggestion"),
            "reason":      parsed.get("reason"),
            "confidence":  float(100*float(parsed.get("confidence", 0.000))),
            "step_passed": bool(parsed.get("step_passed", False)),
        }
    except (json.JSONDecodeError, ValueError):
        return {
            "suggestion":  content,
            "reason":      "Failed to parse structured output from LLM",
            "confidence":  0.0,
            "step_passed": False,
        }