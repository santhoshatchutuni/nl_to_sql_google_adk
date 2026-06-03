from google.adk.agents import SequentialAgent
from agents.sql_generator import sql_generator_agent
from agents.query_reviewer import query_reviewer_agent
from agents.data_interpreter import data_interpreter_agent

sql_orchestrator_agent = SequentialAgent(
    name="sql_orchestrator",
    description="Orchestrates the generation, review, and execution of SQL queries to answer user questions.",
    sub_agents=[sql_generator_agent, query_reviewer_agent, data_interpreter_agent]
)
