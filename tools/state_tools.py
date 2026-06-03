from google.adk.tools import ToolContext

def save_generated_sql(user_prompt: str, sql_query: str, explanation: str, tables_used: list, tool_context: ToolContext) -> str:
    """
    Tool: Saves the user's original prompt and the generated SQL query into the context state.
    This allows the reviewer agent to access them.
    """
    # The ToolContext state is read-only (a property that returns the underlying dict/dataclass).
    # We should update its contents rather than re-assigning it.
    if hasattr(tool_context.state, 'to_dict'):
        # Usually it's a proto or custom object, sometimes updating directly works
        pass 
    
    try:
        tool_context.state["user_prompt"] = user_prompt
        tool_context.state["generated_sql"] = sql_query
        tool_context.state["explanation"] = explanation
        tool_context.state["tables_used"] = tables_used
    except TypeError:
        # If it doesn't support assignment, try updating its dict representation
        if hasattr(tool_context.state, '__dict__'):
             tool_context.state.__dict__["user_prompt"] = user_prompt
             tool_context.state.__dict__["generated_sql"] = sql_query
             tool_context.state.__dict__["explanation"] = explanation
             tool_context.state.__dict__["tables_used"] = tables_used
    
    return "Successfully saved user prompt and SQL query to state."

def get_query_for_review(tool_context: ToolContext) -> str:
    """
    Tool: Retrieves the user prompt and generated SQL query from the context state for review.
    """
    state_dict = tool_context.state if isinstance(tool_context.state, dict) else tool_context.state.to_dict()
    prompt = state_dict.get("user_prompt", "No prompt found")
    sql = state_dict.get("generated_sql", "No SQL found")
    return f"User Prompt: {prompt}\nGenerated SQL: {sql}"

def save_review_feedback(feedback: str, tool_context: ToolContext) -> str:
    """
    Tool: Saves the review feedback into the context state.
    """
    try:
        tool_context.state["review_feedback"] = feedback
    except TypeError:
        if hasattr(tool_context.state, '__dict__'):
             tool_context.state.__dict__["review_feedback"] = feedback
             
    return "Successfully saved review feedback to state."

def get_user_request(tool_context: ToolContext) -> str:
    """
    Tool: Retrieves the original user prompt from the context state.
    This helps the data interpreter know what question to answer with the executed data.
    """
    state_dict = tool_context.state if isinstance(tool_context.state, dict) else tool_context.state.to_dict()
    prompt = state_dict.get("user_prompt", "No user prompt found in state.")
    return f"Original User Question: {prompt}"

def save_final_answer(answer: str, tool_context: ToolContext) -> str:
    """
    Tool: Saves the final natural language answer into the context state so the main script can display it.
    """
    try:
        tool_context.state["final_answer"] = answer
    except TypeError:
        if hasattr(tool_context.state, '__dict__'):
             tool_context.state.__dict__["final_answer"] = answer
             
    return "Successfully saved the final answer to state."
