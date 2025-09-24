
import os
import sqlite3
import pandas as pd
import google.generativeai as genai
from decouple import config
import json

genai.configure(api_key=config("GOOGLE_API_KEY"))
# print("Available models:")
# for m in genai.list_models():
#   if 'generateContent' in m.supported_generation_methods:
#     print(m.name)

def get_database(db_path="db.sqlite3", query_type=None):
    print(query_type)
    conn = sqlite3.connect(db_path,check_same_thread=False)
    cursor = conn.cursor()
    
    allowed_tables = {"UniquePdfDataTable",}
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

    print(json.dumps(schema))

    return conn, json.dumps(schema, indent=2)

# def get_database(db_path="db.sqlite3"):
#     conn = sqlite3.connect(db_path, check_same_thread=False)
#     cursor = conn.cursor()

#     # Only keep these tables
#     allowed_tables = {"Vendors", "UniquePdfDataTable", "BaseDataTable", "BaselineDataTable", "Company", "Organizations"}

#     # Fetch CREATE TABLE statements
#     schema = {}
#     cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
#     for name, sql in cursor.fetchall():
#         if name in allowed_tables and sql is not None:
#             schema[name] = sql.strip()  # Full CREATE TABLE statement

#     return conn, schema

import re

def clean_sql_query(query: str) -> str:
    # Step 1: Sanitize query by slicing from first SQL keyword
    keywords = ("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP")
    upper_q = query.upper()
    for kw in keywords:
        idx = upper_q.find(kw)
        if idx != -1:
            query = query[idx:]
            break

    # Step 2: Make WHERE clause comparisons case-insensitive
    pattern = r"(\w+)\s*=\s*'([^']*)'"
    def repl(m):
        col, val = m.group(1), m.group(2)
        if "wireless" in col.lower():
            # normalize to digits only
            digits_only = re.sub(r"\D", "", val)
            # SQLite trick: remove non-digits from DB column using REPLACE chain
            return f"REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE({col}, '-', ''), ' ', ''), '(', ''), ')', ''), '.', ''), '+', ''), '*', ''), '#', ''), '/', ''), '\\\\', '') = '{digits_only}'"
        else:
            return f"{col} COLLATE NOCASE = '{val}'"

    query = re.sub(pattern, repl, query)

    return query


def get_sql_from_gemini(user_prompt, schema):
    model = genai.GenerativeModel("gemini-2.5-flash-lite")

    prompt = f"""
        You are an expert SQL query generator. Your job is to convert a natural language question into a valid SQLite SQL query.

        ### Rules:
        - Use **only** the tables and columns explicitly provided in the database schema below. Do not assume or invent anything not in the schema.
        - If the question cannot be answered with the given schema, return exactly: NO_SQL
        - Output only the SQL query. Do not include explanations, comments, or extra text.
        - Queries must be **syntactically correct** for SQLite.
        - Respect table relationships:
        - Never substitute or approximate table names.
        - while generating query always focus on column type.

        ### Database Schema:
        {schema}

        ### User Question:
        {user_prompt}
        """


    response = model.generate_content(prompt)
    sql_query = response.text.strip()

    # --- Cleanup Gemini's output ---
    sql_query = sql_query.replace("```sql", "").replace("```", "")
    sql_query = sql_query.replace("SQL Query:", "").replace("sql", "").replace("SQL", "")
    sql_query = sql_query.strip()

    if not sql_query.upper().startswith(("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP")):
        return "NO_SQL"

    return sql_query

def inject_analysis_filter(query: str, bill_id: int, billType: str) -> str:
    query = query.strip().rstrip(";")
    lowered = query.lower()

    column = "viewpapered_id" if billType == "paper" else "viewuploaded_id"

    # Check if a WHERE clause already exists in the query.
    if " where " in lowered:
        # If it exists, add the new condition with 'AND'.
        return f"{query} AND {column} = {bill_id}"
    else:
        # If no WHERE clause exists, add one with the new condition.
        return f"{query} WHERE {column} = {bill_id}"


def execute_sql_query(conn, query,billType, billid):
    try:
        query = clean_sql_query(query).strip()
        query = inject_analysis_filter(query, bill_id=billid, billType=billType)
        print(query)
        df = pd.read_sql_query(query, conn)
        print(df)
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

import time
def main():
    # db_connection = setup_database()
    db_connection,schema  = get_database("Bills/db.sqlite3")
    
    print("schema==", schema)
    
    print("\nWelcome to the Database Chatbot! 🤖")
    print("You can ask questions about our employees. Type 'exit' to quit.")
    
    while True:
        
        user_question = input("\nYour question: ")
        query_start_time = time.perf_counter()
        if user_question.lower() == 'exit':
            break
            
        print("Translating your question into a database query...")
        sql_query = get_sql_from_gemini(user_question, schema)
        print(f"🔍 Generated SQL: {sql_query}")
        
        print("Fetching data from the database...")
        result_df = execute_sql_query(db_connection, billType="uploaded", billid=93)
        print(result_df)
        if result_df is not None:
            print("Interpreting the results...")
            print(result_df)
            final_answer = get_response_from_gemini(user_question, result_df)
            print("\n--- Answer ---")
            print(final_answer)
            query_end_time = time.perf_counter()
            print(f"{(query_end_time - query_start_time):.2f}", "seconds to process query")
            print("--------------")
        else:
            print("Sorry, I could not process your request.")
        
        

    db_connection.close()
    print("\nChatbot session ended. Goodbye!")

if __name__ == "__main__":
    main()