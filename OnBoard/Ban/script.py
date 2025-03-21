import sqlite3
import pandas as pd
import os

conn = sqlite3.connect('Bills/db.sqlite3')
c = conn.cursor()
q = "SELECT * FROM UniquePdfDataTable"

c.execute(q)
rows = c.fetchall()
df = pd.DataFrame(rows)
print(df[10:20])
q = "SELECT * FROM UniquePdfDataTable WHERE account_number='685773812-00004'"

df = pd.read_sql_query(q, conn)
print(df)
# df.to_excel("Bills/sample.xlsx")
conn.close()
