from pydantic import BaseModel, Field

class SQLQueryGeneratorInput(BaseModel):
    natural_language_query: str = Field(
        description="The user's question in natural language that needs to be converted to SQL"
    )

class SQLQueryGeneratorOutput(BaseModel):
    sql_query: str = Field(
        description="The generated SQL query that answers the user's question"
    )
    explanation: str = Field(
        description="Explanation of the SQL query and tables/joins used"
    )
    tables_used: list = Field(
        description="List of tables used in the query"
    )
