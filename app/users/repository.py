from app.db.connection import get_pg_connection


def get_user_by_email(email: str):
    """Get user by email - returns dict with RealDictCursor"""
    conn = get_pg_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()  # Returns dict, not tuple
        return user
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()


def get_user_by_id(user_id: int):
    """Get user by ID - returns dict with RealDictCursor"""
    conn = get_pg_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()  # Returns dict, not tuple
        return user
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()


def create_user(email: str, password_hash: str):
    """Create user - returns dict with RealDictCursor"""
    conn = get_pg_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING *",
            (email, password_hash),
        )
        user = cur.fetchone()  # Returns dict, not tuple
        conn.commit()
        return user
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()
