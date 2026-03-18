import re
from bs4 import BeautifulSoup
from langchain_core.tools import tool

@tool
def extract_relevant_dom_subtree(error_message: str, dom_string: str) -> str:
    """
    Analyzes a Playwright error message and extracts the most relevant 
    HTML subtree from the provided DOM string to help diagnose the failure.
    """
    # 1. Extract potential text or locator clues from the error (e.g., 'Installations', '#login')
    clues = re.findall(r"'(.*?)'", error_message)
    soup = BeautifulSoup(dom_string, 'html.parser')
    
    if not clues:
        return f"No extraction clues found. Truncated DOM: {str(soup.body)[:2000]}"
        
    candidates = []
    for clue in clues:
        # Avoid matching extremely short or generic strings
        if len(clue) < 3: 
            continue
            
        # Search by exact or partial text match
        text_nodes = soup.find_all(string=re.compile(re.escape(clue), re.IGNORECASE))
        for text_node in text_nodes:
            candidates.append(text_node.parent)
            
        # If clue looks like an ID or Class selector
        if clue.startswith('#'):
            element = soup.find(id=clue[1:])
            if element: candidates.append(element)
        elif clue.startswith('.'):
            elements = soup.find_all(class_=clue[1:])
            candidates.extend(elements)

    # 2. Ascend the DOM tree to find a substantial structural container
    if candidates:
        target_node = candidates[0] # Prioritize the first matched clue
        structural_tags = ['form', 'main', 'section', 'div', 'body', 'header', 'nav']
        
        # Traverse up until we hit a structural tag or the top of the tree
        while target_node.name not in structural_tags and target_node.parent:
            target_node = target_node.parent
            
        # Return the prettified subtree (capped to prevent token overflow)
        return target_node.prettify()[:4000]

    return f"Clues {clues} not found in DOM. Truncated DOM: {str(soup.body)[:2000]}"