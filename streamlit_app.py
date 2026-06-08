import streamlit as st
import asyncio
import os
import json
import uuid
from dotenv import load_dotenv

# Google ADK / GenAI Imports
import google.generativeai as genai
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import google.adk.models.gemini_llm_connection # Registers the Gemini connection

from agents import sql_orchestrator_agent
from utils.telemetry import configure_observability
from utils.evaluator import evaluate_sql_quality
from tools.db_tools import get_database_schema
from opentelemetry import trace

# ---------------------------------------------------------
# Setup & Configuration
# ---------------------------------------------------------
load_dotenv()

# Verify API credentials
gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not gemini_api_key:
    st.error("❌ Error: GEMINI_API_KEY not found in .env file")
    st.stop()

genai.configure(api_key=gemini_api_key)
os.environ["GOOGLE_API_KEY"] = gemini_api_key

# Initialize observability ONCE for the Streamlit server
@st.cache_resource
def init_telemetry():
    return configure_observability()

phoenix_url = init_telemetry()

APP_NAME = "sakila_nl2sql_app"
USER_ID = "streamlit_user"

# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------
def init_session():
    """Initializes Streamlit session state variables."""
    # We store the InMemorySessionService in Streamlit's session state 
    # so it persists across UI re-renders and keeps the conversation history!
    if "session_service" not in st.session_state:
        st.session_state.session_service = InMemorySessionService()
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        
    if "messages" not in st.session_state:
        st.session_state.messages = []

async def process_user_query(user_input: str):
    """Runs the Google ADK workflow asynchronously."""
    service = st.session_state.session_service
    session_id = st.session_state.session_id
    
    # Pre-create session if it doesn't exist
    try:
        await service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id
        )
    except Exception:
        pass # Session already exists
        
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("agent_request") as parent_span:
        parent_span.set_attribute("user_query", user_input)
        
        runner = Runner(
            agent=sql_orchestrator_agent,
            app_name=APP_NAME,
            session_service=service
        )
        
        # We pass the user's input as the new message
        prompt = f"Please generate a SQL query for this request and then review it: {user_input}"
        user_content = types.Content(role='user', parts=[types.Part(text=prompt)])
        
        # Run the agent chain
        async for event in runner.run_async(user_id=USER_ID, session_id=session_id, new_message=user_content):
            pass
            
        # Retrieve the final state
        session = await service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id
        )
        
        state_dict = session.state if isinstance(session.state, dict) else session.state.to_dict()
        generated_sql = state_dict.get("generated_sql", "")

        # --- Start of Evaluation ---
        schema = get_database_schema()
        eval_details = await evaluate_sql_quality(user_input, generated_sql, schema)
        # --- End of Evaluation ---
    
    return {
        "sql_query": generated_sql,
        "explanation": state_dict.get("explanation", ""),
        "tables_used": state_dict.get("tables_used", []),
        "review_feedback": state_dict.get("review_feedback", "No review feedback available."),
        "final_answer": state_dict.get("final_answer", "Data Interpreter did not save an answer."),
        "eval_score": eval_details.get("score", 0.0),
        "eval_reason": eval_details.get("reason", "")
    }

# ---------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------
def main():
    st.set_page_config(page_title="NL to SQL Agent", page_icon="🤖", layout="wide")
    st.title("🤖 Natural Language to SQL Agent")
    st.markdown("Ask questions about the Sakila database!")
    
    init_session()
    
    # Render existing chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "details" in msg and msg["details"]:
                with st.expander("🛠️ View Agent Details (SQL, Review, etc.)"):
                    st.json(msg["details"])
                    
    # Chat Input
    if prompt := st.chat_input("E.g., How many actors are there?"):
        
        # 1. Show user message
        st.session_state.messages.append({"role": "user", "content": prompt, "details": None})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # 2. Process and show assistant message
        with st.chat_message("assistant"):
            with st.spinner("Agents are writing SQL, reviewing, and executing data..."):
                try:
                    # Run the async ADK pipeline
                    result = asyncio.run(process_user_query(prompt))
                    
                    final_answer = result["final_answer"]
                    
                    # Display the final human-readable answer
                    st.markdown(final_answer)
                    
                    # Display the internal workings in an expander
                    details = {
                        "SQL Query": result["sql_query"],
                        "Explanation": result["explanation"],
                        "Tables Used": result["tables_used"],
                        "Review Feedback": result["review_feedback"],
                        "LLM Judge Score": f"{result['eval_score']} / 1.0",
                        "Judge Reason": result["eval_reason"]
                    }
                    with st.expander("🛠️ View Agent Details (SQL, Review, etc.)"):
                        st.json(details)
                        
                    # Save to UI history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": final_answer, 
                        "details": details
                    })
                    
                except Exception as e:
                    # If Pydantic or ADK throws an error (like the Invalid JSON error)
                    st.error(f"❌ An error occurred during execution:\n\n{str(e)}")

if __name__ == "__main__":
    main()
