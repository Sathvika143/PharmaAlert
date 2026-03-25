"""
Migration script to port existing medicine_stock data into new schema (medicines + batches).
"""
import sqlite3
import pandas as pd
from datetime import datetime

def migrate_data(old_db="pharmacy.db", new_db="pharmacy.db"):
    """Migrate old medicine_stock table to new schema."""
    conn = sqlite3.connect(new_db)
    cursor = conn.cursor()

    try:
        # Check if old table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='medicine_stock'")
        if not cursor.fetchone():
            print("No old medicine_stock table found. Starting fresh.")
            conn.close()
            return

        # Read old data
        df = pd.read_sql("SELECT * FROM medicine_stock", conn)
        
        if df.empty:
            print("Old table is empty. Starting fresh.")
            conn.close()
            return

        print(f"Migrating {len(df)} records...")

        # Insert medicines and batches
        batch_counter = 0
        for _, row in df.iterrows():
            medicine_name = row.get('medicine_name', 'Unknown')
            expiry_date = row.get('expiry_date', None)
            stock_quantity = row.get('stock_quantity', 0)

            # Insert or ignore medicine
            cursor.execute(
                "INSERT OR IGNORE INTO medicines (name, category, low_stock_threshold) VALUES (?, ?, ?)",
                (medicine_name, 'General', 50)
            )
            
            # Get medicine_id
            cursor.execute("SELECT id FROM medicines WHERE name = ?", (medicine_name,))
            med_id = cursor.fetchone()[0]

            # Insert batch with unique batch number per medicine
            batch_no = f"BATCH_{med_id}_{batch_counter}"
            batch_counter += 1
            cursor.execute(
                "INSERT OR IGNORE INTO batches (medicine_id, batch_number, expiry_date, quantity) VALUES (?, ?, ?, ?)",
                (med_id, batch_no, expiry_date, stock_quantity)
            )

        conn.commit()
        print("Migration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_data()
