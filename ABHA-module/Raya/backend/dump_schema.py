import sqlite3
import json

def get_schema(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    conn.close()
    return tables

print("--- ABHA DB ---")
for name, sql in get_schema('b:/RAYA/ABHA-module/Raya/backend/database/abha.db'):
    print(f"Table: {name}\n{sql}\n")

print("--- RAYA DB ---")
for name, sql in get_schema('b:/RAYA/ABHA-module/Raya/backend/database/raya.db'):
    print(f"Table: {name}\n{sql}\n")
