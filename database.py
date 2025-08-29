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

def _index_exists(conn, table_name, index_name):
    cur = conn.cursor()
    cur.execute("PRAGMA index_list(%s)" % table_name)
    indexes = [row[1] for row in cur.fetchall()]  # row[1] is name
    return index_name in indexes

def _create_index_if_missing(conn, table_name, index_name, create_sql):
    if not _index_exists(conn, table_name, index_name):
        cur = conn.cursor()
        cur.execute(create_sql)

def _migrate_add_auth_and_gamification_columns(conn):
    # Auth-related: ensure email column exists and is unique via index
    _add_column_if_missing(
        conn,
        "users",
        "email",
        "ALTER TABLE users ADD COLUMN email TEXT",
    )
    # Unique index for email if provided (allows NULL duplicates but unique for non-NULL)
    _create_index_if_missing(
        conn,
        "users",
        "idx_users_email_unique",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique ON users(email)",
    )

    # SQLite: use ALTER TABLE ADD COLUMN guarded by PRAGMA checks for gamification fields
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
    # Run guarded migration to add auth and gamification columns
    _migrate_add_auth_and_gamification_columns(conn)
    conn.commit()
    conn.close()

def verify_gamification_columns():
    """Return True if all new columns exist on users table, else False. Also returns details."""
    conn = get_db()
    try:
        cols = _table_columns(conn, "users")
        required = {
            "email",
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

# Run on import
init_db()
