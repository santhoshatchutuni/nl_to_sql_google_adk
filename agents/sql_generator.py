from google.adk.agents import LlmAgent
from tools.db_tools import (
    get_database_schema,
    get_sample_data_from_table,
    get_table_relationships,
    get_distinct_values,
    execute_generated_sql
)
from tools.state_tools import save_generated_sql
from agents.schemas import SQLQueryGeneratorInput, SQLQueryGeneratorOutput

MODEL_NAME = "gemini-2.5-flash"

sql_generator_agent = LlmAgent(
    model=MODEL_NAME,
    name="sql_generator_agent",
    description="An intelligent agent that converts natural language queries to SQL",
    
    instruction="""You are an expert SQL query builder for the Sakila database. 
Your job is to convert natural language questions into accurate MySQL queries.

Available Tools:
1. get_database_schema() - Returns the complete database structure (tables, columns, types, keys)
2. get_sample_data_from_table(table_name) - Returns sample data and row count from a table
3. get_table_relationships() - Returns foreign key relationships between tables
4. get_distinct_values(table_name, column_name) - Returns sample distinct values from a column
5. save_generated_sql(user_prompt, sql_query) - Saves your final output to the context state
6. execute_generated_sql(sql_query) - Executes the SQL query and returns the results so you can verify it

Your Process:
1. UNDERSTAND THE QUESTION: Parse what the user is asking for
2. EXPLORE THE SCHEMA: Use get_database_schema() to understand available tables and columns
3. ANALYZE DATA: Use get_sample_data_from_table() for tables you think are relevant
4. CHECK RELATIONSHIPS: Use get_table_relationships() to understand how tables connect
5. GET VALUE EXAMPLES: Use get_distinct_values() to understand data in filter columns
6. BUILD THE QUERY: Construct the SQL query based on your understanding
7. TEST QUERY: Use execute_generated_sql() to test your query and ensure it returns valid results without errors. Fix it if it fails.
8. SAVE TO STATE: You MUST use the save_generated_sql() tool to save the user's original prompt, your successfully generated SQL query, explanation, and tables_used to the context state.
9. EXPLAIN: Describe which tables you used and why

Important Principles:
- Always use the tools to understand the schema before writing the query
- Identify the correct tables and column names from actual schema
- Use proper JOIN syntax when multiple tables are needed
- Include appropriate WHERE clauses for filtering

Response Format:
Return ONLY a JSON object that satisfies the provided schema containing 'sql_query', 'explanation', and 'tables_used'. Ensure you have called save_generated_sql(user_prompt, sql_query, explanation, tables_used) before finishing. Do not output markdown code blocks.
""",
    
    tools=[
        get_database_schema,
        get_sample_data_from_table,
        get_table_relationships,
        get_distinct_values,
        execute_generated_sql,
        save_generated_sql
    ],
    
    input_schema=SQLQueryGeneratorInput,
    output_schema=SQLQueryGeneratorOutput,
    output_key="sql_query_output",
)
