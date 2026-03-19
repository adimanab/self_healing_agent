# 1. The Playwright Error (Simulated)
from langchain.messages import HumanMessage, ToolMessage
from src.app.graph import graph_init

test_error = """
Error: page.click: Timeout 5000ms exceeded.
Call log:
  - waiting for locator("button#login-btn")
  -   locator resolved to hidden
  -   waiting for element to be visible, enabled and stable
"""

# 2. The Current Dynamic DOM (Simulated)
# Note how the ID has changed, but the text "Login" remains.
test_dom = """
<html>
    <body>
        <nav>Navigation Bar</nav>
        <main>
            <section id="auth-container" class="login-form">
                <h2>Welcome Back</h2>
                <form action="/login" method="POST">
                    <input type="text" name="username" placeholder="Username" />
                    <input type="password" name="password" placeholder="Password" />
                    <button type="submit" id="submit-auth" class="btn-primary">Login</button>
                </form>
            </section>
        </main>
        <footer>Contact us at support@example.com</footer>
    </body>
</html>
"""

# Entry point
# Initialize the state
initial_state = {
    "messages": [],
    "error_message": test_error,
    "dom_string": test_dom
}

# Run the graph
print("--- Starting Agent Execution ---")
self_healing_graph = graph_init()
final_output = self_healing_graph.invoke(initial_state)

# Print the conversation flow to see the "Thinking"
for msg in final_output["messages"]:
    role = "AI" if hasattr(msg, 'content') and not isinstance(msg, HumanMessage) else "User"
    if isinstance(msg, ToolMessage):
        print(f"\n[TOOL RESULT]:\n{msg.content[:200]}...")
    else:
        print(f"\n[{role}]:\n{msg.content}")

print("\n--- Final Suggestion ---")
print(final_output["messages"][-1].content)