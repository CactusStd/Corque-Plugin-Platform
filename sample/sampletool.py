from langchain_core.tools import tool
from typing import Optional, List
import json

# ==========================================
# Core principle (Note for developer):
# 1. Docstring must be clear！Agent depends on it to know how to use it.
# 2. Arguments/parameter must have type hint，otherwise Agent does not know how to pass arguments。
# 3. Never just raise exception or crashes, but return a string that contains the error information.
# ==========================================

@tool
def sampleTool(query: str, limit: int = 5) -> str: # 这个工具的名称是 sampleTool
    """
    [What is this tool about, for example：Search for relevant academic papers.]
    [When to use this tool, for example：Use this tool when the user asks for scientific research.]
    
    Args:
        query (str): The search topic or question.
        limit (int): The max number of results to return. Default is 5.
    
    Returns:
        str: A formatted string containing the results or an error message.
    """
    
    # --- 1. Argument refinement (Optional) ---
    if not query:
        return "Error: query parameter cannot be empty."

    try:
        # --- 2. Core logic (API use / comptutation) ---
        print(f"🔧 Tool Triggered: [tool_function_name] with query='{query}'")
        
        # 模拟业务逻辑 (Mock Logic)
        # result = your_api_call(query)
        result = {"data": f"Mock results for {query}", "count": limit}

        # --- 3. format output(optional) ---
        # It is the best to let agent to read json
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        # --- 4. Error handler ---
        # Even the code do not work or crashes, let the agent know what happened instead of crashes
        return f"Error executing tool: {str(e)}. Please try again with different parameters."













