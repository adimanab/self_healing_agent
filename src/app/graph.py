from langgraph.graph import StateGraph, START, END
from src.app.nodes.dom_extractor import dom_extractor
from src.app.nodes.llm_reason import reason_and_suggest
from src.app.nodes.xpath_builder import xpath_builder
from src.app.state import AgentState

def route_after_dom(state: AgentState):
    """Conditional routing: dynamic sites get xpath building, static go direct"""
    return "xpath" if state.get("is_dynamic") else "agent" 

builder = StateGraph(AgentState)

# Add single node
builder.add_node("agent", reason_and_suggest)
builder.add_node("dom", dom_extractor)
builder.add_node("xpath", xpath_builder)  # building XPath candidates

# Linear flow
builder.add_edge(START, "dom")

builder.add_conditional_edges("dom", 
    route_after_dom,
    {
        "xpath": "xpath",
        "agent": "agent",   
    }
)
builder.add_edge("dom", "xpath")
builder.add_edge("xpath", "agent")
builder.add_edge("agent", END)

self_healing_graph = builder.compile()

def graph_init():
    return self_healing_graph