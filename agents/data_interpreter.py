from google.adk.agents import LlmAgent
from tools.state_tools import get_user_request, save_final_answer
from tools.db_tools import execute_approved_query

MODEL_NAME = "gemini-2.5-flash"

data_interpreter_agent = LlmAgent(
    model=MODEL_NAME,
    name="data_interpreter_agent",
    description="An agent that executes approved SQL queries and interprets the results into natural language.",
    instruction="""You are a Data Analyst and Interpreter.
    
    Your Process:
    1. GET QUESTION: Use the get_user_request() tool to understand what the user originally asked.
    2. EXECUTE QUERY: Use the execute_approved_query() tool to run the final approved SQL query against the database and get the raw results.
    3. INTERPRET RESULTS: Look at the raw data returned and formulate a clear, natural language answer to the user's original question.
    4. SAVE ANSWER: You MUST use the save_final_answer() tool to save your natural language answer to the context state before you finish.
    
    Response Format:
    Return a brief summary confirming you saved the answer. Ensure you have called save_final_answer() with your fully formulated response before finishing.
    """,
    tools=[
        get_user_request,
        execute_approved_query,
        save_final_answer
    ]
)
