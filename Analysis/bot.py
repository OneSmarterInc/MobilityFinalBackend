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
def init_database(db_path="db.sqlite3", query_type=None):
    print("query type", query_type)
    conn = sqlite3.connect(db_path, check_same_thread=False)

    # Decide main table
    if query_type == "input_file":
        main_table = "Analysis_summarydata"
    else:
        main_table = "AnalysisData"

    # You can add more allowed tables here if needed
    allowed_tables = [main_table]

    # Build schema description only for allowed tables
    cursor = conn.cursor()
    schema_description = {}
    type_choices = [
        ('zero_usage', 'Zero Usage'),
        ('less_than_5_gb', 'Less than 5 GB'),
        ('between_5_and_15_gb', 'Between 5 and 15 GB'),
        ('more_than_15_gb', 'More than 15 GB'),
        ('NA_not_unlimited', 'N/A (Not Unlimited)'),
        ('NA_unlimited', 'N/A (Unlimited)'),        
    ]
    for table in allowed_tables:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()

        col_descriptions = []
        for col in columns:
            col_name, col_type = col[1], col[2]
            if table == "AnalysisData" and col_name == "data_usage_range":
                choices_text = ", ".join([f"'{c[0]}' ({c[1]})" for c in type_choices])
                col_descriptions.append(f"{col_name} {col_type} [choices: {choices_text}]")
            else:
                col_descriptions.append(f"{col_name} {col_type}")

        schema_description[table] = col_descriptions

    schema = json.dumps(schema_description, indent=2)

    return conn, schema


# Generate SQL from natural language
def get_sql_from_gemini(user_prompt, schema, special_id=None, chat_history=None):
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
        You are an expert SQL query generator.
        Convert the user request into a valid **SQLite** SQL query.

        ### Allowed Schema:
        {schema}

        ### Conversation history:
        {chat_history}

        ### Important Rules:
        - Use only the tables and columns present in the Allowed Schema.
        - Do not invent new columns or tables.
        - Always generate syntactically valid and only one SQLite.
        - Queries must work when 1, 2, or 3 files have been uploaded.
        - Files are distinguished by the column **bill_date**.
        - If the user refers to a specific file, treat that as filtering by bill_date.
        - If aggregation is required (COUNT, SUM, etc.), group by bill_date when relevant.
        - Always add filter in the query: multiple_analysis_id = {special_id}.
        - Whenever asked about variance, consider only the **highest two values** of each wireless number.
        - Treat '0', '0 gb', '0gb' as 0.0 (we have 0.0 in DB).
        - Respond with SQL only — no explanations, no markdown, no code fences.
        - When using UNION / UNION ALL with ORDER BY + LIMIT on each branch, wrap each SELECT in parentheses.
        - When cleaning numeric columns that may contain '$', 'GB', commas, or 'NA', coerce with REPLACE/CAST to REAL.
        - Whenever you asked about variance always refer these columns, variance_with_last_month, how_variance_is_related_with_last_month
        - Whenever you asked about variance add these columns in query - variance_with_last_month, how_variance_is_related_with_last_month
        - Values stored of variance_with_last_month are string can be stored as 0, positive integer, or NA
        - Values stored of how_variance_is_related_with_last_month are string either be "NA" or of format Jul 2025 > May 2024

        ### User Question:
        {user_prompt}
        """

    response = model.generate_content(prompt)
    raw_sql = response.text or ""
    return raw_sql


import re

def clean_sql_query(query: str) -> str:
    # Step 1: Slice query from the first SQL keyword
    keywords = ("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "WITH")
    upper_q = query.upper()
    for kw in keywords:
        idx = upper_q.find(kw)
        if idx != -1:
            query = query[idx:]
            break

    # Step 2: Normalize WHERE clause comparisons
    # Pattern: column = 'value'
    pattern = r"(\w+)\s*=\s*'([^']*)'"

    def repl(m):
        col, val = m.group(1), m.group(2)
        if "wireless" in col.lower():
            # keep only digits from the value
            digits_only = re.sub(r"\D", "", val)
            # normalize wireless_number column (strip symbols, spaces, etc.)
            cleaned_col = (
                "REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE("
                f"{col}, '-', ''), ' ', ''), '(', ''), ')', ''), '.', ''), '+', ''), '*', ''), '#', ''), '/', ''), '\\\\', '')"
            )
            return f"{cleaned_col} = '{digits_only}'"
        else:
            return f"{col} COLLATE NOCASE = '{val}'"

    query = re.sub(pattern, repl, query)

    # Step 3: Ensure trailing semicolon
    query = query.strip().rstrip(";") + ";"

    return query

# Run query safely
def run_query(conn, sql, analysis_id):
    print("Original SQL:", sql)

    sql = sql.strip().rstrip(";")

    print("Executing SQL:", sql)

    try:
        sql = clean_sql_query(sql)
        df = pd.read_sql_query(sql, conn)
        if df.empty:
            return "No results found."
        return df
    except Exception as e:
        return f"Error executing query: {e}"


def make_human_response(user_question, result, db_schema=None):
    model = genai.GenerativeModel("gemini-2.5-flash-lite")

    # if not isinstance(result, pd.DataFrame):
    #     return "I couldn't find any information matching your request."

    prompt = f"""
    You are a helpful assistant. The user asked:

    **User Question:** "{user_question}"

    I executed a database query and got the following results:
    {result}
    Summarize this result clearly in plain, natural language as human-readable text.
    
    ## Instructions

    -- For answer format
    - Always show months in string format (e.g., 1 as January, 2 as February).
    - Amounts will always be in dollars.
    - Data usage will always be in GB.
    - Try to use all column data to make the answer more clear
    - answer should be in plain text format not with extra decorations like bold, undeline, etc.

    -- generate questions
    - Database Schema: {db_schema}
    - After the summary, generate exactly 2 natural, human-like recommendation questions.
    - Each question must reference valid columns or tables from the schema.
    - Questions should feel like smart suggestions, not technical jargon.
    - Keep them concise, helpful, and answerable by the chatbot using the schema.
    
    
    ### Output format:
    - List of questions (no numbering, just plain text).
    """

    response = model.generate_content(prompt)
    return response.text







# # Chatbot function
# def start_chatbot():
#     print("Initializing chatbot...")
#     conn, schema = init_database(
#         db_path="Bills/db.sqlite3",
#         query_type="input_file",
#         analysis_id=57
#     )
#     print("Chatbot ready. Ask your questions! (type 'exit' to quit)\n")

#     while True:
#         user_input = input("You: ")
#         if user_input.lower() in ["exit", "quit"]:
#             print("Goodbye 👋")
#             break

#         sql = get_sql_from_gemini(user_input, schema)
#         print(f"\nGenerated SQL: {sql}")
#         result = run_query(conn, sql, analysis_id=57)

#         if isinstance(result, pd.DataFrame):
#             print("\nAI Response:")
#             print(make_human_response(user_input, result))
#         else:
#             # Even for errors or "No results", pass it to AI for friendly phrasing
#             print("\nAI Response:")
#             print(make_human_response(user_input, result))


# if __name__ == "__main__":
#     start_chatbot()
