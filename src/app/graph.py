from langgraph.graph import StateGraph, START, END
from src.app.state import AgentState


# from src.app.nodes.extract_dom import extract_dom
# from src.app.nodes.llm_node    import llm_node
# from src.app.nodes.reporter    import reporter

builder = StateGraph(AgentState)

# builder.add_node("extract_dom", extract_dom)
# builder.add_node("llm_node",    llm_node)
# builder.add_node("reporter",    reporter)

# builder.add_edge(START,         "extract_dom")
# builder.add_edge("extract_dom", "llm_node")
# builder.add_edge("llm_node",    "reporter")
# builder.add_edge("reporter",    END)

self_healing_graph = builder.compile()

def graph_init():
    return self_healing_graph