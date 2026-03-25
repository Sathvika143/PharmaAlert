import sqlite3
import pandas as pd
from db_config import DB_PATH

# Connect to SQLite database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create Medicine Stock Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS medicine_stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_name TEXT,
    expiry_date DATE,
    stock_quantity INTEGER
)
''')

# Load data from CSV
df = pd.read_csv("medicine_data.csv")
df.to_sql("medicine_stock", conn, if_exists="replace", index=False)

conn.commit()
conn.close()
