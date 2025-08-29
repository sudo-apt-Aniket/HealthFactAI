from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./healthfact.db")

import sqlite3

DB_NAME = "healthfact.db"

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Users table (auth)
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)
    # Run guarded migration to add gamification columns
    _migrate_add_gamification_columns(conn)
    conn.commit()
    conn.close()

# Run on import
init_db()

def _table_columns(conn, table_name):
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({table_name})")
    rows = c.fetchall()
    return {row[1] for row in rows}

def _add_column_if_missing(conn, table_name, column_name, add_sql):
    existing = _table_columns(conn, table_name)
    if column_name not in existing:
        cur = conn.cursor()
        cur.execute(add_sql)

def _migrate_add_gamification_columns(conn):
    # SQLite: use ALTER TABLE ADD COLUMN guarded by PRAGMA checks
    _add_column_if_missing(
        conn,
        "users",
        "facts_learned",
        "ALTER TABLE users ADD COLUMN facts_learned TEXT NOT NULL DEFAULT '[]'",
    )
    _add_column_if_missing(
        conn,
        "users",
        "current_streak",
        "ALTER TABLE users ADD COLUMN current_streak INTEGER NOT NULL DEFAULT 0",
    )
    _add_column_if_missing(
        conn,
        "users",
        "last_activity_date",
        "ALTER TABLE users ADD COLUMN last_activity_date DATE",
    )
    _add_column_if_missing(
        conn,
        "users",
        "longest_streak",
        "ALTER TABLE users ADD COLUMN longest_streak INTEGER NOT NULL DEFAULT 0",
    )
    _add_column_if_missing(
        conn,
        "users",
        "total_facts_count",
        "ALTER TABLE users ADD COLUMN total_facts_count INTEGER NOT NULL DEFAULT 0",
    )

def verify_gamification_columns():
    """Return True if all new columns exist on users table, else False. Also returns details."""
    conn = get_db()
    try:
        cols = _table_columns(conn, "users")
        required = {
            "facts_learned",
            "current_streak",
            "last_activity_date",
            "longest_streak",
            "total_facts_count",
        }
        missing = sorted(list(required - cols))
        return {
            "ok": len(missing) == 0,
            "missing": missing,
            "present": sorted(list(cols & required)),
        }
    finally:
        conn.close()
