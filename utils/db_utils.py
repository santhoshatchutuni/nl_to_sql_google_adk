import os
import mysql.connector
from mysql.connector import Error as MySQLError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MySQL configuration
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "sakila"),
    "port": int(os.getenv("MYSQL_PORT", "3306"))
}

class DatabaseConnector:
    """Manages MySQL database connections for the Sakila database."""
    
    _connection = None
    
    @staticmethod
    def get_connection():
        """Get MySQL connection."""
        if DatabaseConnector._connection is None or not DatabaseConnector._connection.is_connected():
            try:
                DatabaseConnector._connection = mysql.connector.connect(**MYSQL_CONFIG)
            except MySQLError as e:
                raise Exception(f"MySQL Connection Error: {str(e)}")
        return DatabaseConnector._connection
    
    @staticmethod
    def execute_query(query: str, params: list = None) -> list:
        """Execute query and return results."""
        try:
            connection = DatabaseConnector.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Not all queries return results (like INSERT/UPDATE), but we're mostly SELECTing
            if cursor.with_rows:
                results = cursor.fetchall()
            else:
                connection.commit()
                results = []
                
            cursor.close()
            return results
        except MySQLError as e:
            raise Exception(f"Query Error: {str(e)}")
