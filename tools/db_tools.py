from utils.db_utils import DatabaseConnector, MYSQL_CONFIG

def get_database_schema() -> str:
    """
    Tool: Get the complete database schema including all tables, columns, data types, keys.
    This helps the agent understand the database structure.
    """
    try:
        query = """
        SELECT 
            TABLE_NAME,
            COLUMN_NAME,
            COLUMN_TYPE,
            IS_NULLABLE,
            COLUMN_KEY,
            EXTRA
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_NAME, ORDINAL_POSITION
        """
        results = DatabaseConnector.execute_query(query, [MYSQL_CONFIG["database"]])
        
        if not results:
            return "No tables found in database."
        
        # Group by table
        schema_dict = {}
        for row in results:
            table = row['TABLE_NAME']
            if table not in schema_dict:
                schema_dict[table] = []
            
            col_info = f"{row['COLUMN_NAME']} ({row['COLUMN_TYPE']}"
            if row['COLUMN_KEY'] == 'PRI':
                col_info += " PRIMARY KEY"
            if row['COLUMN_KEY'] == 'MUL':
                col_info += " FOREIGN KEY"
            if row['IS_NULLABLE'] == 'NO':
                col_info += " NOT NULL"
            col_info += ")"
            
            schema_dict[table].append(col_info)
        
        # Format output
        schema_text = f"Database Schema for {MYSQL_CONFIG['database']}:\n"
        schema_text += "="*60 + "\n\n"
        
        for table_name in sorted(schema_dict.keys()):
            schema_text += f"Table: {table_name}\n"
            schema_text += "-" * 40 + "\n"
            for col in schema_dict[table_name]:
                schema_text += f"  {col}\n"
            schema_text += "\n"
        
        return schema_text
    except Exception as e:
        return f"Error retrieving schema: {str(e)}"

def get_sample_data_from_table(table_name: str) -> str:
    """
    Tool: Get sample data from a specific table to understand data patterns and values.
    This helps the agent understand what kind of data is in each table.
    """
    try:
        # Get column info first
        col_query = """
        SELECT COLUMN_NAME, COLUMN_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """
        col_results = DatabaseConnector.execute_query(col_query, [MYSQL_CONFIG["database"], table_name])
        
        if not col_results:
            return f"Table '{table_name}' not found."
        
        # Get row count
        count_query = f"SELECT COUNT(*) as count FROM {table_name}"
        count_result = DatabaseConnector.execute_query(count_query)
        total_rows = count_result[0]['count'] if count_result else 0
        
        # Get sample data (first 5 rows)
        sample_query = f"SELECT * FROM {table_name} LIMIT 5"
        sample_data = DatabaseConnector.execute_query(sample_query)
        
        # Format output
        output = f"Sample Data from '{table_name}':\n"
        output += "="*60 + "\n"
        output += f"Total rows in table: {total_rows}\n"
        output += f"Columns: {len(col_results)}\n\n"
        
        # Show column info
        output += "Column Information:\n"
        for col in col_results:
            output += f"  - {col['COLUMN_NAME']} ({col['COLUMN_TYPE']})\n"
        
        # Show sample rows
        if sample_data:
            output += "\nSample Data (first 5 rows):\n"
            output += "-"*60 + "\n"
            for i, row in enumerate(sample_data, 1):
                output += f"Row {i}:\n"
                for key, value in row.items():
                    output += f"  {key}: {value}\n"
                output += "\n"
        else:
            output += "\n(No data in table)\n"
        
        return output
    except Exception as e:
        return f"Error retrieving sample data: {str(e)}"

def get_table_relationships() -> str:
    """
    Tool: Get relationships between tables (foreign keys).
    This helps the agent understand which tables need to be joined.
    """
    try:
        query = """
        SELECT 
            TABLE_NAME,
            COLUMN_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s 
        AND REFERENCED_TABLE_NAME IS NOT NULL
        """
        results = DatabaseConnector.execute_query(query, [MYSQL_CONFIG["database"]])
        
        if not results:
            return "No relationships (foreign keys) found in database."
        
        # Format relationships
        output = "Table Relationships (Foreign Keys):\n"
        output += "="*60 + "\n\n"
        
        for rel in results:
            output += f"{rel['TABLE_NAME']}.{rel['COLUMN_NAME']}"
            output += f" → {rel['REFERENCED_TABLE_NAME']}.{rel['REFERENCED_COLUMN_NAME']}\n"
        
        return output
    except Exception as e:
        return f"Error retrieving relationships: {str(e)}"

def get_distinct_values(table_name: str, column_name: str) -> str:
    """
    Tool: Get distinct values from a specific column (useful for understanding data).
    This helps the agent see example values for filters and conditions.
    """
    try:
        query = f"SELECT DISTINCT {column_name} FROM {table_name} LIMIT 10"
        results = DatabaseConnector.execute_query(query)
        if not results:
            return f"No values found for {table_name}.{column_name}"
            
        output = f"Distinct values for {table_name}.{column_name}:\n"
        for row in results:
            output += f"- {row[column_name]}\n"
        return output
    except Exception as e:
        return f"Error retrieving distinct values: {str(e)}"

def execute_generated_sql(sql_query: str) -> str:
    """
    Tool: Execute the generated SQL query and return the results.
    """
    try:
        results = DatabaseConnector.execute_query(sql_query)
        if not results:
            return "Query executed successfully, but returned no results."
            
        # Format output
        output = f"Query Results (showing up to 20 rows):\n"
        output += "-"*60 + "\n"
        
        # Determine column headers from first row
        if len(results) > 0:
            headers = list(results[0].keys())
            output += " | ".join(headers) + "\n"
            output += "-"*60 + "\n"
            
            for i, row in enumerate(results[:20]):
                output += " | ".join([str(row[h]) for h in headers]) + "\n"
                
            if len(results) > 20:
                output += f"\n... and {len(results) - 20} more rows."
                
        return output
    except Exception as e:
        return f"Error executing query: {str(e)}"
