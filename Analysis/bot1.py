import sqlite3
import pandas as pd
import google.generativeai as genai
from decouple import config
import json
import re

class Bot:
    def __init__(self, api_key,db_path, bot_type=None, hisDF=None):
        genai.configure(api_key=api_key)
        self.bot_type = bot_type
        self.db = db_path
        self.history=hisDF
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
            allowed_tables = ["Company", "Organizations", "Vendors", "BaseDataTable", "UniquePdfDataTable"]
        cursor = conn.cursor()
        schema_description = {}
        for table in allowed_tables:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            schema_description[table] = [f'{col[1]} {col[2]}' for col in columns]

        schema = json.dumps(schema_description, indent=2)

        return conn, schema
    
    # def sql_from_gemini(self, )
