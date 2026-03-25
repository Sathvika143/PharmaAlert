"""
Reports: Generate CSV exports for various medicine reports.
"""
import io
import sqlite3
from datetime import datetime, timedelta
from db_config import DB_PATH
from operations import get_near_expiry_medicines, get_low_stock_medicines, get_expired_medicines, get_usage_log
import csv


def generate_csv_near_expiry(lead_days=180):
    """Generate CSV for near-expiry medicines."""
    medicines = get_near_expiry_medicines(lead_days)
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['medicine_name', 'batch_number', 'expiry_date', 'quantity'])
    writer.writeheader()
    
    for med in medicines:
        writer.writerow({
            'medicine_name': med['name'],
            'batch_number': med['batch_number'],
            'expiry_date': med['expiry_date'],
            'quantity': med['quantity']
        })
    
    return output.getvalue()


def generate_csv_low_stock():
    """Generate CSV for low-stock medicines."""
    medicines = get_low_stock_medicines()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['medicine_name', 'current_stock', 'low_stock_threshold'])
    writer.writeheader()
    
    for med in medicines:
        writer.writerow({
            'medicine_name': med['name'],
            'current_stock': med['total_stock'],
            'low_stock_threshold': med['low_stock_threshold']
        })
    
    return output.getvalue()


def generate_csv_expired():
    """Generate CSV for expired medicines."""
    medicines = get_expired_medicines()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['medicine_name', 'batch_number', 'expiry_date', 'quantity'])
    writer.writeheader()
    
    for med in medicines:
        writer.writerow({
            'medicine_name': med['name'],
            'batch_number': med['batch_number'],
            'expiry_date': med['expiry_date'],
            'quantity': med['quantity']
        })
    
    return output.getvalue()


def generate_csv_usage_log(days=30):
    """Generate CSV for usage log in past N days."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    since_date = (datetime.today() - timedelta(days=days)).strftime('%Y-%m-%d')
    cursor.execute("""
        SELECT ul.id, b.medicine_id, m.name, ul.qty_change, ul.reason, ul.timestamp
        FROM usage_log ul
        JOIN batches b ON ul.batch_id = b.id
        JOIN medicines m ON b.medicine_id = m.id
        WHERE ul.timestamp >= ?
        ORDER BY ul.timestamp DESC
    """, (since_date,))
    
    rows = cursor.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Log ID', 'Medicine', 'Quantity Change', 'Reason', 'Timestamp'])
    
    for row in rows:
        writer.writerow([row[0], row[2], row[3], row[4], row[5]])
    
    return output.getvalue()


def generate_csv_all_medicines():
    """Generate CSV for all medicines inventory."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT m.id, m.name, m.category, m.low_stock_threshold,
               COUNT(b.id) as batch_count,
               COALESCE(SUM(b.quantity), 0) as total_stock
        FROM medicines m
        LEFT JOIN batches b ON m.id = b.medicine_id
        GROUP BY m.id
        ORDER BY m.name
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Medicine ID', 'Name', 'Category', 'Low Stock Threshold', 'Batch Count', 'Total Stock'])
    
    for row in rows:
        writer.writerow(row)
    
    return output.getvalue()
