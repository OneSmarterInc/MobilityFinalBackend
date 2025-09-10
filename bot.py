
import os
import sqlite3
import pandas as pd
import google.generativeai as genai
from decouple import config

genai.configure(api_key=config("GOOGLE_API_KEY"))
# print("Available models:")
# for m in genai.list_models():
#   if 'generateContent' in m.supported_generation_methods:
#     print(m.name)

def get_database(db_path="db.sqlite3"):
    conn = sqlite3.connect(db_path,check_same_thread=False)
    cursor = conn.cursor()

    allowed_tables = {"Vendors", "UniquePdfDataTable", "BaseDataTable", "BaselineDataTable", "Company", "Organizations"}
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall() if t[0] in allowed_tables]
    schema = {}
    for table in tables:
        schema[table] = []
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        for col in columns:
            col_id, name, col_type, notnull, default, pk = col
            schema[table].append(f"{name} {col_type}")

    return conn, schema

def make_case_insensitive(query: str) -> str:
    # Replace WHERE clauses like: column = 'value'
    return query.replace(" = ", " COLLATE NOCASE = ")

def get_sql_from_gemini(user_prompt, schema):
    model = genai.GenerativeModel("gemini-2.5-flash-lite")

    prompt = f"""
        You are an expert SQL generator. Your task is to translate a natural language question into a syntactically correct SQL query.

        - Always use the provided database schema.
        - Only use the tables and columns explicitly mentioned in the schema in the dictionary format.
        - If the user’s question cannot be answered with the given schema, respond with "NO_SQL".
        - Use proper SQL syntax compatible with SQLite.

        Database Schema:
        {schema}

        User Question:
        {user_prompt}

        Return only the SQL query (no explanation, no text before or after).
        """

    response = model.generate_content(prompt)
    sql_query = response.text.strip()

    # --- Cleanup Gemini's output ---
    sql_query = sql_query.replace("```sql", "").replace("```", "")
    sql_query = sql_query.replace("SQL Query:", "").replace("sql", "").replace("SQL", "")
    sql_query = sql_query.strip()

    # Ensure query starts correctly
    if not sql_query.upper().startswith(("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP")):
        return "NO_SQL"

    return sql_query


def execute_sql_query(conn, query):
    try:
        query = make_case_insensitive(query)
        print(query)
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"Error executing query: {e}")
        return None

def get_response_from_gemini(user_prompt, dataframe):

    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    if dataframe.empty:
        return "I couldn't find any information matching your request."
        
    prompt = f"""
    You are a helpful assistant. A user asked the following question:
    "{user_prompt}"
    
    I ran a database query and got the following results:
    {dataframe.to_string()}
    
    Please provide a clear, natural language answer based on these results.
    Summarize the information and do not just repeat the table.
    """
    
    response = model.generate_content(prompt)
    return response.text

# import time
# def main():
#     # db_connection = setup_database()
#     db_connection,schema  = get_database("Bills/db.sqlite3")
    
#     # print("schema==", schema)
    
#     print("\nWelcome to the Database Chatbot! 🤖")
#     print("You can ask questions about our employees. Type 'exit' to quit.")
    
#     while True:
        
#         user_question = input("\nYour question: ")
#         query_start_time = time.perf_counter()
#         if user_question.lower() == 'exit':
#             break
            
#         print("Translating your question into a database query...")
#         sql_query = get_sql_from_gemini(user_question, schema)
#         print(f"🔍 Generated SQL: {sql_query}")
        
#         print("Fetching data from the database...")
#         result_df = execute_sql_query(db_connection, sql_query)
#         print(result_df)
#         if result_df is not None:
#             print("Interpreting the results...")
#             print(result_df)
#             final_answer = get_response_from_gemini(user_question, result_df)
#             print("\n--- Answer ---")
#             print(final_answer)
#             query_end_time = time.perf_counter()
#             print(f"{(query_end_time - query_start_time):.2f}", "seconds to process query")
#             print("--------------")
#         else:
#             print("Sorry, I could not process your request.")
        
        

#     db_connection.close()
#     print("\nChatbot session ended. Goodbye!")

# if __name__ == "__main__":
#     main()