import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from db_config import DB_PATH

# Connect to database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get today's date and expiry threshold (e.g., 6 months)
today = datetime.today()
threshold_date = today + timedelta(days=180)  # 6 months from today

# Fetch medicines expiring within the next 6 months
query = "SELECT * FROM medicine_stock WHERE expiry_date <= ?"
df = pd.read_sql(query, conn, params=(threshold_date.strftime('%Y-%m-%d'),))

# Display near-expiry medicines
if not df.empty:
    print(" Near-Expiry Medicines:")
    print(df)
else:
    print(" No medicines expiring soon.")

conn.close()
