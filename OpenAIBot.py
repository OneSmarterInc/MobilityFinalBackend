import sqlite3
import pandas as pd
from openai import OpenAI
from decouple import config
import json
from openai import RateLimitError
import re, time
import ast
class OpenAIBotClass: 
    _last_call = 0
    def __init__(self, db_path="db.sqlite3", bot_type=None):
        
        self.client = OpenAI(
            api_key=config("OPENAI_API_KEY"),
            max_retries=3
        )


        self.bot_type = bot_type
        self.db = db_path

        self.query_model = "gpt-4o"
        self.response_model = "gpt-4o-mini"

    def _rate_limit(self, min_interval=1.2):
        now = time.time()
        elapsed = now - self._last_call
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_call = time.time()

    def init_database(self, query_type=None):
        conn = sqlite3.connect(self.db, check_same_thread=False)

        if self.bot_type == "analysis":
            if query_type == "input_file":
                allowed_tables = ["Analysis_summarydata"]
            else:
                allowed_tables = ["AnalysisData"]
        elif self.bot_type == "bill":
            allowed_tables = ["BaselineDataTable"]
        else:
            allowed_tables = [
                "Company", "Organizations", "Vendors",
                "BaseDataTable", "UniquePdfDataTable",
                "Requests", "AccessoriesRequest",
                "upgrade_device_request"
            ]

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

        return conn, json.dumps(schema_description, indent=2)

    from openai import RateLimitError

    def _chat(self, model, prompt):
        self._rate_limit()
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            return response.choices[0].message.content.strip()

        except RateLimitError:
            # DO NOT retry
            return "RATE_LIMITED"


    def get_analysis_sql_from_gemini(self, user_prompt, schema, special_id=None, chat_history=None):
        try:
            prompt = f"""
                You are an expert SQL query generator.
                Convert the user request into a valid **SQLite** SQL query.

                ### User Question:
                {user_prompt}

                ### Allowed Schema:
                {schema}

                ### Conversation history:
                {chat_history}

                ### Important Rules:
                - Don't ignore user question, generate query only if question is relatable to db schema
                - Use only the tables and columns present in the Allowed Schema.
                - Do not invent new columns or tables.
                - Always generate syntactically valid and only one SQLite.
                - Queries must work when 1, 2, or 3 files have been uploaded.
                - Files are distinguished by the column **bill_date**.
                - If the user refers to a specific file, treat that as filtering by bill_date.
                - If aggregation is required (COUNT, SUM, etc.), group by bill_date when relevant.
                - Add filter in the query: multiple_analysis_id = {special_id}.
                - Whenever asked about variance, consider only the **highest two values** of each wireless number.
                - Treat '0', '0 gb', '0gb' as 0.0 (we have 0.0 in DB).
                - Respond with SQL only — no explanations, no markdown, no code fences.
                - When using UNION / UNION ALL with ORDER BY + LIMIT on each branch, wrap each SELECT in parentheses.
                - When cleaning numeric columns that may contain '$', 'GB', commas, or 'NA', coerce with REPLACE/CAST to REAL.
                - Whenever you asked about variance always refer these columns, variance_with_last_month, how_variance_is_related_with_last_month
                - Whenever you asked about variance add these columns in query - variance_with_last_month, how_variance_is_related_with_last_month
                - Values stored of variance_with_last_month are string can be stored as 0, positive integer, or NA
                - Values stored of how_variance_is_related_with_last_month are string either be "NA" or of format Jul 2025 > May 2024

                
                """
            sql = self._chat(self.query_model, prompt)
            if sql == "RATE_LIMITED":
                return False, "LLM rate limit hit. Try again later."
            return True, sql
        except Exception:
            return False, ""

    def get_view_sql_from_gemini(self, user_prompt, schema, bill_type=None, special_id=None, chathistory=None):
        try:
            prompt = f"""
            You are an expert SQL query generator.
            Convert the user request into a valid **SQLite** SQL query.

            User question: {user_prompt}
            
            ### Allowed Schema:
            {schema}

            ### Conversation history:
            {chathistory}

            ### Rules:
            - Don't ignore user question, generate query only if question is relatable to db schema
            - Use only the tables and columns present in Allowed Schema.
            - Do not invent new columns or tables.
            - Keep the SQL simple and valid for SQLite.
            - always add filter in the query as if paper in {bill_type} then viewpapered_id={special_id} otherwise viewuploaded_id={special_id}
            - Refer the Conversation history if present
            
            """
            sql = self._chat(self.query_model, prompt)
            if sql == "RATE_LIMITED":
                return False, "LLM rate limit hit. Try again later."

            if not re.search(r"\b(SELECT|INSERT|UPDATE|DELETE)\b", sql, re.I):
                return False, ""

            return True, sql.strip()
        except Exception:
            return False, ""

    def get_general_sql_from_gemini(self, user_prompt, schema, chat_history):
        try:
            prompt = f"""
            You are an expert SQL query generator.
            Convert the user request into a valid **SQLite** SQL query.

            User question: {user_prompt}
            
            ### Allowed Schema:
            {schema}

            ### Conversation history:
            {chat_history}

            ### Rules:
            - Don't ignore user question, generate query only if question is relatable to db schema
            - Use only the tables and columns present in Allowed Schema.
            - Always add filter in the query as viewuploaded_id=None, viewpapered=None if fields are present
            - Do not invent new columns or tables.
            - Keep the SQL simple and valid for SQLite.
            - Refer the Conversation history if present

            
            """
            sql = self._chat(self.query_model, prompt)
            if sql == "RATE_LIMITED":
                return False, "LLM rate limit hit. Try again later."
            return True, sql.strip()
        except Exception:
            return False, ""

    def clean_sql_query(self, query: str) -> str:
        keywords = ("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "WITH")
        upper_q = query.upper()
        for kw in keywords:
            idx = upper_q.find(kw)
            if idx != -1:
                query = query[idx:]
                break

        pattern = r"(\w+)\s*=\s*'([^']*)'"

        def repl(m):
            col, val = m.group(1), m.group(2)
            if "wireless" in col.lower():
                digits = re.sub(r"\D", "", val)
                return f"{col} = '{digits}'"
            return f"{col} COLLATE NOCASE = '{val}'"

        query = re.sub(pattern, repl, query)
        return query.strip().rstrip(";") + ";"

    def run_query(self, conn, sql):
        try:
            sql = self.clean_sql_query(sql)
            df = pd.read_sql_query(sql, conn)
            return (False, "No results found.") if df.empty else (True, df)
        except Exception as e:
            return False, str(e)

    def make_human_response(self, user_question, result, db_schema=None):
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
        - Each question must end with question mark (?).
        - Questions should feel like smart suggestions, not technical jargon.
        - Keep them concise, helpful, and answerable by the chatbot using the schema.
        
        
        ### Output format:
        - List of questions (no numbering, just plain text).
        """
        sql = self._chat(self.query_model, prompt)
        if sql == "RATE_LIMITED":
            return False, "LLM rate limit hit. Try again later."
        return True, sql
        
