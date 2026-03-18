from langgraph.graph import StateGraph, START, END
from src.app.nodes.llm_reason import reason_and_suggest
from src.app.state import AgentState

builder = StateGraph(AgentState)

# Add single node
builder.add_node("agent", reason_and_suggest)

# Linear flow
builder.add_edge(START, "agent")
builder.add_edge("agent", END)

self_healing_graph = builder.compile()

def graph_init():
    return self_healing_graph