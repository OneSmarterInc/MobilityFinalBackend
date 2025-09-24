
import os
import sqlite3
import pandas as pd
import google.generativeai as genai
from decouple import config
import json

genai.configure(api_key=config("GOOGLE_API_KEY"))


def get_database(db_path="db.sqlite3"):
    conn = sqlite3.connect(db_path,check_same_thread=False)
    cursor = conn.cursor()

    allowed_tables = {"Vendors","BaseDataTable", "BaselineDataTable", "Company", "Organizations"}
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

    return conn, json.dumps(schema, indent=2)



import re

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
        - **First-class foreign keys**: `banOnboarded_id` and `banUploaded_id` → represent onboarded account numbers under an organization.
        - **Second-class foreign keys**: `viewuploaded_id` and `viewpapered_id` → represent bills uploaded under the onboarded account numbers.
        - If there are similarly named tables (e.g., BaseDataTable vs BaselineDataTable), pick the one that matches the question’s wording exactly.
        - Never substitute or approximate table names.
        - query regarding account number should be searched in BaseDataTable only.
        - query regarding vendor name should be searched in Vendors table only.
        - query regarding phone/wireless number should be searched in BaselineDataTable only.
        - query regarding organization name should be searched in Organizations table only.
        - query regarding company name should be searched in Company table only.
        - query asking about bills are non null values of viewuploaded_id and viewpapered_id in BaseDataTable table and BaselineDataTable only.


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


def execute_sql_query(conn, query):
    try:
        query = clean_sql_query(query)
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

import time
def main():
    # db_connection = setup_database()
    db_connection,schema  = get_database("Bills/db.sqlite3")
    
    # print("schema==", schema)
    
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
        result_df = execute_sql_query(db_connection, sql_query)
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



# chatbot_first_match.py
# ---------------------------------------
# Single-file implementation:
# - Short-circuits at the first compatible table (priority-ordered)
# - Preserves your "wireless" number normalization
# - Gemini -> SQL with strict routing hints
# - Clean, testable functions + optional CLI main()
# ---------------------------------------

# import os
# import re
# import json
# import time
# import sqlite3
# import pandas as pd
# from decouple import config
# import google.generativeai as genai

# # ---------------------------
# # Config
# # ---------------------------
# GOOGLE_API_KEY = config("GOOGLE_API_KEY")
# genai.configure(api_key=GOOGLE_API_KEY)

# # Prefer absolute path or env; falls back to Bills/db.sqlite3
# DEFAULT_DB_PATH = config("DB_PATH", default="Bills/db.sqlite3")

# # Your explicit table priority (first match wins)
# TABLE_PRIORITY = ["Vendors", "BaseDataTable", "BaselineDataTable", "Company", "Organizations"]

# # ---------------------------
# # DB & schema helpers
# # ---------------------------
# def get_database(db_path: str = DEFAULT_DB_PATH):
#     """
#     Returns:
#       conn: sqlite3.Connection
#       schema_json: str               (pretty JSON for the LLM)
#       schema_cols_only: dict[str,set[str]]
#       tables_ordered: list[str]      (existing tables in priority order)
#     """
#     conn = sqlite3.connect(db_path, check_same_thread=False)
#     cursor = conn.cursor()

#     # Keep only existing tables, in declared priority
#     cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
#     existing = {t[0] for t in cursor.fetchall()}
#     tables_ordered = [t for t in TABLE_PRIORITY if t in existing]

#     # Build schema detail for LLM + a fast lookup set of column names
#     schema = {}
#     for table in tables_ordered:
#         schema[table] = []
#         cursor.execute(f"PRAGMA table_info({table});")
#         for col_id, name, col_type, notnull, default, pk in cursor.fetchall():
#             schema[table].append(f"{name} {col_type}")

#     schema_cols_only = {t: {c.split()[0] for c in cols} for t, cols in schema.items()}
#     return conn, json.dumps(schema, indent=2), schema_cols_only, tables_ordered

# # ---------------------------
# # SQL cleanup & normalization
# # ---------------------------
# def clean_sql_query(query: str) -> str:
#     # Slice from first SQL keyword to drop any LLM preamble
#     keywords = ("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP")
#     upper_q = query.upper()
#     for kw in keywords:
#         idx = upper_q.find(kw)
#         if idx != -1:
#             query = query[idx:]
#             break

#     # Case-insensitive equality for general cols; strong normalization for "wireless" cols
#     pattern = r"(\b[A-Za-z_][A-Za-z0-9_]*\b)\s*=\s*'([^']*)'"

#     def repl(m):
#         col, val = m.group(1), m.group(2)
#         if "wireless" in col.lower():
#             digits_only = re.sub(r"\D", "", val)
#             # REPLACE-chain to strip formatting in DB values
#             return (
#                 "REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE("
#                 "REPLACE(REPLACE(REPLACE(REPLACE("
#                 f"{col}, '-', ''), ' ', ''), '(', ''), ')', ''), '.', ''), '+', ''), '*', ''), '#', ''), '/', ''), '\\\\', '') "
#                 f"= '{digits_only}'"
#             )
#         else:
#             return f"{col} COLLATE NOCASE = '{val}'"

#     return re.sub(pattern, repl, query)

# # ---------------------------
# # Gemini: NL -> SQL
# # ---------------------------
# def get_sql_from_gemini(user_prompt: str, schema_json: str) -> str:
#     model = genai.GenerativeModel("gemini-2.5-flash-lite")

#     prompt = f"""
# You are an expert SQL query generator for SQLite.

# Rules:
# - Use only the tables and columns in the schema. If the question cannot be answered, return exactly: NO_SQL
# - Output only the SQL (no explanations, no code fences).
# - Prefer single-table SELECTs unless absolutely necessary.
# - Routing hints (hard rules):
#   - account number -> BaseDataTable
#   - vendor name -> Vendors
#   - phone/wireless number -> BaselineDataTable
#   - organization name -> Organizations
#   - company name -> Company
#   - "bills" -> non-null viewuploaded_id/viewpapered_id in BaseDataTable or BaselineDataTable
# - If similar table names exist, pick the one matching wording exactly. Never invent names.

# Schema:
# {schema_json}

# User Question:
# {user_prompt}
# """
#     response = model.generate_content(prompt)
#     sql_query = (response.text or "").strip()
#     # strip fences/labels if any
#     sql_query = sql_query.replace("```sql", "").replace("```", "").replace("SQL Query:", "").strip()

#     if not sql_query.upper().startswith(("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP")):
#         return "NO_SQL"
#     return sql_query

# # ---------------------------
# # First-match executor (short-circuit)
# # ---------------------------
# _TABLE_RE = re.compile(r"\bFROM\s+([A-Za-z_][A-Za-z0-9_]*)\b", re.IGNORECASE)

# def _extract_table(sql: str) -> str | None:
#     m = _TABLE_RE.search(sql)
#     return m.group(1) if m else None

# def _extract_columns_used(sql: str, schema_cols_only: dict[str, set[str]]) -> set[str]:
#     tokens = set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", sql))
#     all_known_cols = set().union(*schema_cols_only.values()) if schema_cols_only else set()
#     return {tok for tok in tokens if tok in all_known_cols}

# def _swap_table(sql: str, new_table: str) -> str:
#     return _TABLE_RE.sub(lambda m: m.group(0).replace(m.group(1), new_table), sql, count=1)

# def execute_sql_query(conn: sqlite3.Connection, query: str):
#     try:
#         q = clean_sql_query(query)
#         return pd.read_sql_query(q, conn)
#     except Exception as e:
#         # Optional: log the SQL/exception somewhere central
#         print(f"[sql-error] {e}")
#         return None

# def execute_first_match(
#     conn: sqlite3.Connection,
#     base_sql: str,
#     schema_cols_only: dict[str, set[str]],
#     tables_ordered: list[str],
# ):
#     """
#     First compatible table wins:
#     1) If SQL already names a FROM table and it exists in priority list, try it first.
#     2) Otherwise follow `tables_ordered`.
#     3) Pick the FIRST table that contains ALL referenced columns.
#     4) Run once and STOP. Return empty df if no rows (do NOT try others).

#     Returns: (df_or_none, reason, chosen_table_or_none)
#     """
#     cols_used = _extract_columns_used(base_sql, schema_cols_only)
#     explicit = _extract_table(base_sql)

#     # Build try order: explicit table (if valid) first, then remaining by priority
#     try_order = []
#     if explicit and explicit in tables_ordered:
#         try_order.append(explicit)
#     try_order += [t for t in tables_ordered if t != explicit]

#     # If no column signal, still try once (short-circuit)
#     if not cols_used:
#         df = execute_sql_query(conn, base_sql)
#         return df, "no-column-signal", explicit

#     # Choose first compatible table
#     chosen = None
#     for t in try_order:
#         if cols_used.issubset(schema_cols_only.get(t, set())):
#             chosen = t
#             break

#     if not chosen:
#         return None, "columns-missing-in-all-tables", None

#     sql_to_run = base_sql if (explicit is None or explicit == chosen) else _swap_table(base_sql, chosen)
#     df = execute_sql_query(conn, sql_to_run)
#     if df is None:
#         return None, "sql-error", chosen
#     return df, ("ok-empty" if df.empty else "ok"), chosen

# # ---------------------------
# # Gemini: verbalize result
# # ---------------------------
# def get_response_from_gemini(user_prompt: str, dataframe: pd.DataFrame | None) -> str:
#     model = genai.GenerativeModel("gemini-2.5-flash-lite")

#     if dataframe is None:
#         return "I couldn’t process your request due to a query error."
#     if dataframe.empty:
#         return "No matching records were found."

#     prompt = f"""
# User question:
# {user_prompt}

# Query results (sample up to 50 rows):
# {dataframe.head(50).to_string(index=False)}

# Give a clear natural-language answer based ONLY on the table above. Summarize; don't repeat rows verbatim.
# """
#     return (model.generate_content(prompt).text or "").strip()

# # ---------------------------
# # Optional CLI runner for quick local testing
# # ---------------------------
# def main():
#     conn, schema_json, schema_cols_only, tables_ordered = get_database(DEFAULT_DB_PATH)

#     print("\nWelcome to the Database Chatbot (first-match). Type 'exit' to quit.")
#     try:
#         while True:
#             user_question = input("\nYour question: ").strip()
#             if user_question.lower() == "exit":
#                 break

#             t0 = time.perf_counter()
#             print("Translating your question into a database query...")
#             sql_query = get_sql_from_gemini(user_question, schema_json)
#             print(f"🔍 Generated SQL: {sql_query}")

#             if sql_query == "NO_SQL":
#                 print("Sorry, this question can’t be answered with the current schema.")
#                 continue

#             print("Running first-match query (short-circuit)...")
#             df, reason, chosen_table = execute_first_match(conn, sql_query, schema_cols_only, tables_ordered)
#             print(f"[diagnostic] reason={reason}, table={chosen_table}")
#             if isinstance(df, pd.DataFrame):
#                 print(df.head())

#             print("Interpreting the results...")
#             final_answer = get_response_from_gemini(user_question, df)
#             print("\n--- Answer ---")
#             print(final_answer)
#             print(f"{(time.perf_counter() - t0):.2f} seconds to process")
#             print("--------------")
#     finally:
#         conn.close()
#         print("\nChatbot session ended. Goodbye!")

# if __name__ == "__main__":
#     main()
