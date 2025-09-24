import os
import sqlite3
import pandas as pd
import google.generativeai as genai
from decouple import config
import json
import re

# Configure Gemini
genai.configure(api_key=config("GOOGLE_API_KEY"))


# Initialize DB connection + schema together
def init_database(db_path="db.sqlite3", query_type=None, analysis_id=None):
    conn = sqlite3.connect(db_path, check_same_thread=False)

    # Decide main table
    if query_type == "input_file":
        main_table = "Analysis_summarydata"
    else:
        main_table = "AnalysisData"

    # You can add more allowed tables here if needed
    allowed_tables = [main_table]

    query = f"SELECT * FROM {main_table}"
    params = ()
    if analysis_id is not None:
        query += " WHERE multiple_analysis_id = ?"
        params = (analysis_id,)
    print("Initial load:", query, params)

    # Load data
    df = pd.read_sql_query(query, conn, params=params)
    print("Sample Data:\n", df.head())

    # Build schema description only for allowed tables
    cursor = conn.cursor()
    schema_description = {}
    for table in allowed_tables:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        schema_description[table] = [col[1] for col in columns]

    schema = json.dumps(schema_description, indent=2)
    print(schema)

    return conn, schema


# Generate SQL from natural language
def get_sql_from_gemini(user_prompt, schema):
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""
    You are an expert SQL query generator.
    Convert the user request into a valid **SQLite** SQL query.
    
    ### Allowed Schema:
    {schema}

    ### Rules:
    - Use only the tables and columns present in Allowed Schema.
    - Do not invent new columns or tables.
    - Keep the SQL simple and valid for SQLite.

    User question: {user_prompt}
    """
    response = model.generate_content(prompt)
    raw_sql = response.text

    # --- CLEAN SQL OUTPUT ---
    cleaned = re.sub(r"```.*?```", lambda m: m.group(0).replace("```sql", "").replace("```", ""), raw_sql, flags=re.S)
    cleaned = cleaned.strip()

    # Keep only the first SQL-looking part
    match = re.search(r"(SELECT|INSERT|UPDATE|DELETE).*", cleaned, re.I | re.S)
    if match:
        return match.group(0).strip()
    return cleaned

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
# Run query safely
def run_query(conn, sql, analysis_id):
    print("Original SQL:", sql)

    # Normalize SQL
    sql = sql.strip().rstrip(";")

    # If there's already a WHERE, add with AND
    if re.search(r"\bwhere\b", sql, re.I):
        sql = re.sub(r"\bwhere\b", f"WHERE multiple_analysis_id = {analysis_id} AND", sql, count=1, flags=re.I)
    else:
        # Insert before ORDER BY or LIMIT if present
        if re.search(r"\border\s+by\b", sql, re.I):
            sql = re.sub(r"\border\s+by\b", f"WHERE multiple_analysis_id = {analysis_id} ORDER BY", sql, flags=re.I)
        elif re.search(r"\blimit\b", sql, re.I):
            sql = re.sub(r"\blimit\b", f"WHERE multiple_analysis_id = {analysis_id} LIMIT", sql, flags=re.I)
        else:
            sql += f" WHERE multiple_analysis_id = {analysis_id}"

    print("Executing SQL:", sql)

    try:
        sql = clean_sql_query(sql)
        df = pd.read_sql_query(sql, conn)
        if df.empty:
            return "No results found."
        return df
    except Exception as e:
        return f"Error executing query: {e}"

# Summarize SQL result into human readable text
def make_human_response(user_question, result):
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    if not isinstance(result, pd.DataFrame):
        return "I couldn't find any information matching your request."
        
    prompt = f"""
    You are a helpful assistant. A user asked the following question:
    "{user_question}"
    
    I ran a database query and got the following results:
    {result.to_string()}
    
    Please provide a clear, natural language answer based on these results.
    Summarize the information and do not just repeat the table.
    """
    
    response = model.generate_content(prompt)
    return response.text





# Chatbot function
def start_chatbot():
    print("Initializing chatbot...")
    conn, schema = init_database(
        db_path="Bills/db.sqlite3",
        query_type="input_file",
        analysis_id=57
    )
    print("Chatbot ready. Ask your questions! (type 'exit' to quit)\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye 👋")
            break

        sql = get_sql_from_gemini(user_input, schema)
        print(f"\nGenerated SQL: {sql}")
        result = run_query(conn, sql, analysis_id=57)
        print("results==", result)

        if isinstance(result, pd.DataFrame):
            print("\nAI Response:")
            print(make_human_response(user_input, result))
        else:
            # Even for errors or "No results", pass it to AI for friendly phrasing
            print("\nAI Response:")
            print(make_human_response(user_input, result))


if __name__ == "__main__":
    start_chatbot()
