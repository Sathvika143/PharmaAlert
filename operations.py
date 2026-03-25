"""
CRUD and stock operations for medicines and batches.
"""
import sqlite3
from datetime import datetime
from db_config import DB_PATH

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ==================== MEDICINES ====================

def add_medicine(name, category, low_stock_threshold=50):
    """Add a new medicine."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO medicines (name, category, low_stock_threshold) VALUES (?, ?, ?)",
            (name, category, low_stock_threshold)
        )
        conn.commit()
        medicine_id = cursor.lastrowid
        return {"success": True, "id": medicine_id}
    except sqlite3.IntegrityError as e:
        return {"success": False, "error": f"Medicine already exists: {e}"}
    finally:
        conn.close()

def get_all_medicines():
    """Get all medicines with their batch count and total stock."""
    conn = get_db()
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
    return [dict(row) for row in rows]

def get_medicine(medicine_id):
    """Get a specific medicine."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM medicines WHERE id = ?", (medicine_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_medicine(medicine_id, name=None, category=None, low_stock_threshold=None):
    """Update medicine details."""
    conn = get_db()
    cursor = conn.cursor()
    updates = []
    params = []
    
    if name:
        updates.append("name = ?")
        params.append(name)
    if category:
        updates.append("category = ?")
        params.append(category)
    if low_stock_threshold is not None:
        updates.append("low_stock_threshold = ?")
        params.append(low_stock_threshold)
    
    if not updates:
        return {"success": False, "error": "No updates provided"}
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(medicine_id)
    
    try:
        query = f"UPDATE medicines SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def delete_medicine(medicine_id):
    """Delete a medicine and its batches."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM batches WHERE medicine_id = ?", (medicine_id,))
        cursor.execute("DELETE FROM medicines WHERE id = ?", (medicine_id,))
        conn.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

# ==================== BATCHES ====================

def add_batch(medicine_id, batch_number, expiry_date, quantity):
    """Add a new batch for a medicine."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO batches (medicine_id, batch_number, expiry_date, quantity) VALUES (?, ?, ?, ?)",
            (medicine_id, batch_number, expiry_date, quantity)
        )
        conn.commit()
        batch_id = cursor.lastrowid
        return {"success": True, "id": batch_id}
    except sqlite3.IntegrityError as e:
        return {"success": False, "error": f"Batch already exists: {e}"}
    finally:
        conn.close()

def get_batches_by_medicine(medicine_id):
    """Get all batches for a medicine."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM batches WHERE medicine_id = ? ORDER BY expiry_date ASC",
        (medicine_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_batch(batch_id):
    """Get a specific batch."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM batches WHERE id = ?", (batch_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# ==================== STOCK OPERATIONS ====================

def receive_stock(batch_id, quantity, reason="Stock received"):
    """Receive stock (increase batch quantity)."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE batches SET quantity = quantity + ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (quantity, batch_id)
        )
        cursor.execute(
            "INSERT INTO usage_log (batch_id, qty_change, reason) VALUES (?, ?, ?)",
            (batch_id, quantity, reason)
        )
        conn.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def issue_stock(batch_id, quantity, reason="Stock issued"):
    """Issue stock (decrease batch quantity)."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check available stock
        cursor.execute("SELECT quantity FROM batches WHERE id = ?", (batch_id,))
        row = cursor.fetchone()
        if not row or row[0] < quantity:
            return {"success": False, "error": "Insufficient stock"}
        
        cursor.execute(
            "UPDATE batches SET quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (quantity, batch_id)
        )
        cursor.execute(
            "INSERT INTO usage_log (batch_id, qty_change, reason) VALUES (?, ?, ?)",
            (batch_id, -quantity, reason)
        )
        conn.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def get_usage_log(limit=50):
    """Get recent usage log."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ul.id, b.medicine_id, m.name, ul.qty_change, ul.reason, ul.timestamp
        FROM usage_log ul
        JOIN batches b ON ul.batch_id = b.id
        JOIN medicines m ON b.medicine_id = m.id
        ORDER BY ul.timestamp DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# ==================== ALERTS ====================

def get_near_expiry_medicines(lead_days=180):
    """Get medicines expiring within lead_days."""
    conn = get_db()
    cursor = conn.cursor()
    from datetime import timedelta
    threshold = (datetime.today() + timedelta(days=lead_days)).strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT m.id, m.name, b.id as batch_id, b.batch_number, b.expiry_date, b.quantity
        FROM medicines m
        JOIN batches b ON m.id = b.medicine_id
        WHERE b.expiry_date <= ? AND b.quantity > 0
        ORDER BY b.expiry_date ASC
    """, (threshold,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_low_stock_medicines():
    """Get medicines below their low_stock_threshold."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, m.name, m.low_stock_threshold,
               COALESCE(SUM(b.quantity), 0) as total_stock
        FROM medicines m
        LEFT JOIN batches b ON m.id = b.medicine_id
        GROUP BY m.id
        HAVING total_stock < low_stock_threshold
        ORDER BY total_stock ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_expired_medicines():
    """Get medicines that have already expired."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, m.name, b.id as batch_id, b.batch_number, b.expiry_date, b.quantity
        FROM medicines m
        JOIN batches b ON m.id = b.medicine_id
        WHERE b.expiry_date < DATE('now') AND b.quantity > 0
        ORDER BY b.expiry_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_dashboard_stats():
    """Get summary stats for dashboard."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Total SKUs
    cursor.execute("SELECT COUNT(*) FROM medicines")
    total_skus = cursor.fetchone()[0]
    
    # Near-expiry count
    cursor.execute("SELECT COUNT(*) FROM (SELECT DISTINCT b.medicine_id FROM batches b WHERE b.expiry_date <= DATE('now', '+180 days') AND b.quantity > 0)")
    near_expiry_count = cursor.fetchone()[0]
    
    # Low-stock count
    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT m.id FROM medicines m
            LEFT JOIN batches b ON m.id = b.medicine_id
            GROUP BY m.id
            HAVING COALESCE(SUM(b.quantity), 0) < m.low_stock_threshold
        )
    """)
    low_stock_count = cursor.fetchone()[0]
    
    # Total stock value
    cursor.execute("SELECT COUNT(*) FROM batches WHERE quantity > 0")
    total_batches = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_skus": total_skus,
        "near_expiry_count": near_expiry_count,
        "low_stock_count": low_stock_count,
        "total_batches": total_batches
    }
