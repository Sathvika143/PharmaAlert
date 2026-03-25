"""
Add test medicines with near-expiry dates for email testing.
"""
import sqlite3
from datetime import datetime, timedelta
from db_config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Add test medicines
test_medicines = [
    ("Aspirin Test", "Pain Relief", 50),
    ("Paracetamol Test", "Fever", 20),
    ("Amoxicillin Test", "Antibiotic", 100),
]

for name, category, threshold in test_medicines:
    cursor.execute(
        "INSERT OR IGNORE INTO medicines (name, category, low_stock_threshold) VALUES (?, ?, ?)",
        (name, category, threshold)
    )

conn.commit()

# Add batches with different expiry scenarios
cursor.execute("SELECT id FROM medicines WHERE name LIKE '%Test%'")
medicine_ids = [row[0] for row in cursor.fetchall()]

test_batches = [
    # Near-expiry (within 6 months)
    (medicine_ids[0], "BATCH_EXPIRING_SOON", (datetime.today() + timedelta(days=60)).strftime('%Y-%m-%d'), 100),
    (medicine_ids[1], "BATCH_EXPIRING_2MONTHS", (datetime.today() + timedelta(days=90)).strftime('%Y-%m-%d'), 50),
    
    # Already expired
    (medicine_ids[0], "BATCH_EXPIRED", (datetime.today() - timedelta(days=10)).strftime('%Y-%m-%d'), 25),
    
    # Low stock (below threshold)
    (medicine_ids[2], "BATCH_LOW_STOCK", (datetime.today() + timedelta(days=365)).strftime('%Y-%m-%d'), 10),
]

for med_id, batch_no, expiry, qty in test_batches:
    cursor.execute(
        "INSERT OR IGNORE INTO batches (medicine_id, batch_number, expiry_date, quantity) VALUES (?, ?, ?, ?)",
        (med_id, batch_no, expiry, qty)
    )

conn.commit()
conn.close()

print("✓ Test medicines added successfully!")
print("\nAdded:")
print("  - 3 test medicines")
print("  - 2 near-expiry batches (60 & 90 days)")
print("  - 1 already expired batch")
print("  - 1 low-stock batch")
print("\nNow trigger the email check from the dashboard!")
