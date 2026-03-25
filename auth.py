"""
Authentication: User management and login/logout functionality.
"""
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from db_config import DB_PATH


class User(UserMixin):
    """User class for Flask-Login."""
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role


def init_users():
    """Create users table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users should already exist from schema.py, but ensure password field
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    except:
        pass  # Column already exists
    
    conn.commit()
    conn.close()


def create_user(username, password, role="pharmacist"):
    """Create a new user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Use pbkdf2:sha256 for Python 3.7 compatibility
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password_hash, role)
        )
        conn.commit()
        return {"success": True, "id": cursor.lastrowid}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "Username already exists"}
    finally:
        conn.close()


def get_user_by_username(username):
    """Get user by username."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return User(row["id"], row["username"], row["role"])
    return None


def get_user_by_id(user_id):
    """Get user by ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return User(row["id"], row["username"], row["role"])
    return None


def verify_user_password(username, password):
    """Verify user credentials."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    
    if row and check_password_hash(row["password"], password):
        return User(row["id"], row["username"], row["role"])
    return None


def log_audit(user_id, action, table_name, record_id):
    """Log audit trail."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO audit_log (user_id, action, table_name, record_id) VALUES (?, ?, ?, ?)",
        (user_id, action, table_name, record_id)
    )
    conn.commit()
    conn.close()
