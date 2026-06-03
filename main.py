import os
import json
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import google.adk.models.gemini_llm_connection # required to register the gemini connection

from agents import sql_orchestrator_agent

# Load environment variables
load_dotenv()

# Verify API credentials
gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not gemini_api_key:
    print("❌ Error: GEMINI_API_KEY not found in .env file")
    exit(1)

genai.configure(api_key=gemini_api_key)
os.environ["GOOGLE_API_KEY"] = gemini_api_key

APP_NAME = "sakila_nl2sql_app"

async def async_main():
    print("="*60)
    print("🤖 Natural Language to SQL Agent (Sakila Database)")
    print("="*60)
    print("Type 'exit' or 'quit' to stop.\n")

    # Setup persistent session service
    session_service = InMemorySessionService()
    
    user_id = "test_user"
    session_id = "sakila_nl2sql_session_1"
    
    # Pre-create the session to avoid 'Session not found' errors.
    try:
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
    except Exception:
        # Session already exists
        pass
    
    while True:
        try:
            user_input = input("\n🗣️ You: ")
            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
            
            if not user_input.strip():
                continue
                
            print("\n⏳ Processing... (This involves multiple agents running sequentially)\n")
            
            # Use Runner with the Sequential Orchestrator
            runner = Runner(
                agent=sql_orchestrator_agent,
                app_name=APP_NAME,
                session_service=session_service
            )
            
            prompt = f"Please generate a SQL query for this request and then review it: {user_input}"
            user_content = types.Content(role='user', parts=[types.Part(text=prompt)])
            
            # The sequential agent coordinates everything.
            async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_content):
                pass
            
            # Retrieve the final state to show the user
            session = await session_service.get_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id
            )
            
            state_dict = session.state if isinstance(session.state, dict) else session.state.to_dict()
            
            generated_sql = state_dict.get("generated_sql", "No SQL generated.")
            explanation = state_dict.get("explanation", "")
            tables_used = state_dict.get("tables_used", [])
            review_feedback = state_dict.get("review_feedback", "No review feedback available.")
            
            # Since ADK session might not expose a flat 'history' array easily, 
            # let's save the final natural language answer into the state dictionary 
            # within the DataInterpreterAgent tool itself. 
            # Let's temporarily retrieve it if it exists.
            final_answer = state_dict.get("final_answer", "Final answer not saved to state.")
            
            final_output = {
                "sql_query": generated_sql,
                "explanation": explanation,
                "tables_used": tables_used,
                "review_feedback": review_feedback,
            }
            
            print(f"✅ Final Result:")
            print("-" * 60)
            print(json.dumps(final_output, indent=2))
            
            print("\n📊 Data Interpreter Answer:")
            print("-" * 60)
            print(final_answer)
            print("=" * 60)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error during execution: {str(e)}")

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
