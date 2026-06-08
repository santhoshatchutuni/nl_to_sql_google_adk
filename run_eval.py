import asyncio
import os
from dotenv import load_dotenv
from google.adk.evaluation.agent_evaluator import AgentEvaluator
from agents import sql_orchestrator_agent
from utils.telemetry import configure_observability

async def run_batch_evaluation():
    # Load environment variables (API Keys, DB config)
    load_dotenv()
    
    # Optional: Start Phoenix if you want to see the eval traces there too
    configure_observability()
    
    print("🚀 Starting ADK Batch Evaluation...")
    
    # Path to your test dataset
    dataset_path = os.path.join("tests", "sql_tests.json")
    
    # Official ADK Evaluation
    # Note: AgentEvaluator uses LLM-as-a-judge internally to compare 
    # the generated SQL with your 'expected_output'.
    await AgentEvaluator.evaluate(
        agent=sql_orchestrator_agent,
        eval_dataset_file_path_or_dir=dataset_path,
        # You can specify which model to use as the judge
        # judge_model="gemini-2.5-flash" 
    )
    
    print("\n✅ Evaluation Complete! Check the console output or Phoenix UI for details.")

if __name__ == "__main__":
    asyncio.run(run_batch_evaluation())
