import json
import os
from opentelemetry import trace
import asyncio
from phoenix.evals import LLMEvaluator, LLM

# Get the tracer for the project
tracer = trace.get_tracer(__name__)

# 1. Setup the Phoenix Judge Model (Gemini)
judge_llm = LLM(provider="google", model="gemini-2.5-flash")

# 2. Define the Judge Prompt
SQL_JUDGE_PROMPT = """
You are an expert SQL Auditor. Evaluate the following SQL query generated for the user's question.

Database Context: {schema_context}
User Question: "{user_question}"
Generated SQL: "{generated_sql}"

Rate the query based on:
1. Logic Correctness: Does it correctly answer the question?
2. Syntax: Is it valid MySQL?
3. Efficiency: Is it using proper joins and filters?

Return your evaluation ONLY as a JSON object with these keys:
{{
    "score": (float between 0.0 and 1.0),
    "reason": "short explanation of the score",
    "hallucination": (boolean, true if it used non-existent tables/columns),
    "efficiency_rating": "Good/Fair/Poor"
}}
"""

# 3. Define the evaluation function
async def evaluate_sql_quality(user_question: str, generated_sql: str, schema_context: str) -> dict:
    """
    Uses the official phoenix.evals.LLM wrapper to judge the SQL.
    Logs the result to the current OpenTelemetry span.
    """
    current_span = trace.get_current_span()
    
    if not generated_sql or "SELECT" not in generated_sql.upper():
        result = {"score": 0.0, "reason": "No valid SQL was generated."}
        _log_to_span(current_span, result)
        return result

    try:
        # Format the prompt manually
        prompt = SQL_JUDGE_PROMPT.format(
            user_question=user_question,
            generated_sql=generated_sql,
            schema_context=schema_context
        )
        
        # Use Phoenix's LLM wrapper to generate the response
        # This ensures the call is tracked by Phoenix
        raw_response = await judge_llm.async_generate_text(prompt)
        
        # Parse the JSON response
        try:
            # Remove markdown code blocks if the LLM included them
            clean_text = raw_response.replace("```json", "").replace("```", "").strip()
            eval_result = json.loads(clean_text)
        except Exception:
            eval_result = {"score": 0.5, "reason": f"Could not parse judge response: {raw_response}"}
        
        # Log to Phoenix
        _log_to_span(current_span, eval_result)
        
        return eval_result
        
    except Exception as e:
        error_result = {"score": 0.0, "reason": f"Phoenix Evaluation failed: {str(e)}"}
        _log_to_span(current_span, error_result)
        return error_result

def _log_to_span(span, eval_result: dict):
    """Helper to attach evaluation metrics to the active span."""
    if not span.is_recording():
        return
        
    score = eval_result.get("score", 0.0)
    reason = eval_result.get("reason", "No reason provided")
    
    span.set_attribute("eval.sql_quality_score", score)
    span.set_attribute("eval.reason", reason)
    span.set_attribute("eval.hallucination", eval_result.get("hallucination", False))
    span.set_attribute("eval.efficiency", eval_result.get("efficiency_rating", "Unknown"))
    
    span.set_attribute("score", score)
    span.set_attribute("label", "SQL Quality")
    span.set_attribute("explanation", reason)
    span.set_attribute("openinference.span.kind", "EVALUATOR")
