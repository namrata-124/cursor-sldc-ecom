# run_query.py
import sqlite3
import pandas as pd

conn = sqlite3.connect("ecom.db")
with open("top_products_per_customer.sql", "r") as f:
    sql = f.read()
try:
    df = pd.read_sql_query(sql, conn)
except Exception as e:
    print("Error executing SQL:", e)
    conn.close()
    raise
df.to_csv("top_products_per_customer.csv", index=False)
print("Query exported to top_products_per_customer.csv")
print(df.head())
conn.close()
