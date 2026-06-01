from google.adk.agents import LlmAgent
from tools.state_tools import get_query_for_review, save_review_feedback

MODEL_NAME = "gemini-2.5-flash"

query_reviewer_agent = LlmAgent(
    model=MODEL_NAME,
    name="query_reviewer_agent",
    description="An agent that reviews SQL queries for correctness and logic.",
    instruction="""You are an expert SQL reviewer.
    
    Your Process:
    1. RETRIEVE DATA: Use the get_query_for_review() tool to get the user's original prompt and the generated SQL query from the context state.
    2. REVIEW: Analyze the SQL query. Does it correctly answer the user's prompt? Is the MySQL syntax correct? Are there any logical flaws or missing JOINs?
    3. SAVE FEEDBACK: You MUST use the save_review_feedback() tool to save your detailed review feedback to the context state.
    
    Response Format:
    Return a brief summary of your review. Ensure you have called save_review_feedback() before finishing.
    """,
    tools=[
        get_query_for_review,
        save_review_feedback
    ]
)
