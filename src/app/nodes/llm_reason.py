from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.app.state import AgentState
from src.app.tools.dom_extractor import extract_relevant_dom_subtree # Or your preferred LLM
from dotenv import load_dotenv

import os

load_dotenv(override=True)

groq_api_key = os.getenv("GROQ_API_KEY")
groq_base_url = os.getenv("GROQ_BASE_URL")

# Initialize LLM and bind the tool
llm = ChatOpenAI(
    model="llama-3.3-70b-versatile",
    base_url=groq_base_url,
    api_key=groq_api_key,
    temperature=0.4
)
tools = [extract_relevant_dom_subtree]
llm_with_tools = llm.bind_tools(tools)

def reason_and_suggest(state: AgentState):
    messages = state.get("messages", [])
    new_messages = [] # Track only new messages to return to the state reducer
    
    # 1. Setup initial prompts if this is the first execution
    if not messages:
        sys_prompt = SystemMessage(content="""
        You are an expert Test Automation AI.
        1. Use the 'extract_relevant_dom_subtree' tool.
        2. Analyze the extracted HTML subtree.
        3. Output a JSON-like suggestion with "location", "reason", and "suggestion".
        """)
        task_prompt = HumanMessage(content=f"Error: {state['error_message']}\nDOM: {state['dom_string']}")
        
        messages = [sys_prompt, task_prompt]
        new_messages.extend(messages)

    # 2. First LLM Call
    response = llm_with_tools.invoke(messages)
    new_messages.append(response)
    
    # 3. Check if LLM wants to call a tool
    if response.tool_calls:
        messages.append(response) # Update local context
        
        # Execute requested tools
        for tool_call in response.tool_calls:
            if tool_call["name"] == "extract_relevant_dom_subtree":
                # Execute the actual Python function
                tool_result = extract_relevant_dom_subtree.invoke(tool_call["args"])
                
                # Format the result as a ToolMessage
                tool_msg = ToolMessage(
                    content=str(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"]
                )
                messages.append(tool_msg)
                new_messages.append(tool_msg)
        
        # 4. Second LLM Call with the tool output included
        final_response = llm_with_tools.invoke(messages)
        new_messages.append(final_response)

    # Return only the delta for the state reducer
    return {"messages": new_messages}