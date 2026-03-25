from bs4 import BeautifulSoup
from langgraph.graph import StateGraph, START, END
from src.app.nodes.dom_extractor import dom_extractor
from src.app.nodes.llm_reason import reason_and_suggest
from src.app.nodes.file_locator import file_locator
from src.app.nodes.human_approval import human_approval
from src.app.nodes.apply_fix import apply_fix
from src.app.nodes.xpath_builder import xpath_builder
from src.app.state import AgentState

def route_after_dom(state: AgentState):
    """Conditional routing: dynamic sites get xpath building, static go direct"""
    return "xpath" if state.get("is_dynamic") else "Dom_Extractor" 

builder = StateGraph(AgentState)

# Add nodes
builder.add_node("Dom_Extractor", dom_extractor)
builder.add_node("Reasoning_agent", reason_and_suggest)
builder.add_node("File_Locator", file_locator)
builder.add_node("Human_Approval", human_approval)
builder.add_node("Apply_Fix", apply_fix)
builder.add_node("xpath", xpath_builder)    # building XPath candidates

def check_approval(state: AgentState):
    if state.get("approved"):
        return "Apply_Fix"
    return END

# Set flow

builder.add_conditional_edges(START,
                              route_after_dom, 
    {
        "Dom_Extractor": "Dom_Extractor",
        "xpath": "xpath",
    })

builder.add_edge("xpath", "Reasoning_agent")
builder.add_edge("Dom_Extractor", "Reasoning_agent")
builder.add_edge("Reasoning_agent", "File_Locator")
builder.add_edge("File_Locator", "Human_Approval")

builder.add_conditional_edges("Human_Approval", 
    check_approval, 
    {
        "Apply_Fix": "Apply_Fix",
        END: END
    }
)
builder.add_edge("Apply_Fix", END)

self_healing_graph = builder.compile()

def graph_init():
    return self_healing_graph