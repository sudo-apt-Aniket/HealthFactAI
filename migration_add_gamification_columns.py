#!/usr/bin/env python3
"""
Migration script to add gamification columns to the users table.
This script safely adds the new columns and handles cases where they might already exist.
"""

import sqlite3
import sys
from datetime import datetime
from database import get_db, DB_NAME

def add_gamification_columns():
    """
    Add gamification columns to the existing users table.
    Uses ALTER TABLE with error handling for existing columns.
    """
    try:
        conn = sqlite3.connect(DB_NAME, timeout=30.0)
        cursor = conn.cursor()
    except sqlite3.Error as e:
        print(f"Failed to connect to database: {e}")
        return False
    
    # List of columns to add with their definitions
    columns_to_add = [
        ("facts_learned", "TEXT DEFAULT '[]'"),
        ("current_streak", "INTEGER DEFAULT 0"),
        ("last_activity_date", "DATE"),
        ("longest_streak", "INTEGER DEFAULT 0"),
        ("total_facts_count", "INTEGER DEFAULT 0")
    ]
    
    print(f"Starting migration to add gamification columns to users table...")
    print(f"Database: {DB_NAME}")
    
    try:
        # Check existing columns first
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"Existing columns: {existing_columns}")
        
        columns_added = []
        columns_skipped = []
        
        for column_name, column_definition in columns_to_add:
            if column_name in existing_columns:
                print(f"Column '{column_name}' already exists, skipping...")
                columns_skipped.append(column_name)
                continue
            
            try:
                alter_sql = f"ALTER TABLE users ADD COLUMN {column_name} {column_definition}"
                print(f"Executing: {alter_sql}")
                cursor.execute(alter_sql)
                columns_added.append(column_name)
                print(f"✓ Successfully added column '{column_name}'")
            except sqlite3.Error as e:
                print(f"✗ Error adding column '{column_name}': {e}")
                raise
        
        # Commit all changes
        conn.commit()
        
        print(f"\nMigration completed successfully!")
        print(f"Columns added: {columns_added}")
        print(f"Columns skipped (already existed): {columns_skipped}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"Database error during migration: {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"Unexpected error during migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def rollback_migration():
    """
    Rollback function to remove the gamification columns if needed.
    Note: SQLite doesn't support DROP COLUMN directly, so this creates a new table.
    """
    print("WARNING: Rolling back migration will remove all gamification data!")
    confirm = input("Are you sure you want to proceed? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Rollback cancelled.")
        return False
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Create backup table with original structure
        cursor.execute("""
            CREATE TABLE users_backup AS 
            SELECT id, username, password FROM users
        """)
        
        # Drop original table
        cursor.execute("DROP TABLE users")
        
        # Recreate original table
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        """)
        
        # Restore original data
        cursor.execute("""
            INSERT INTO users (id, username, password)
            SELECT id, username, password FROM users_backup
        """)
        
        # Drop backup table
        cursor.execute("DROP TABLE users_backup")
        
        conn.commit()
        print("✓ Migration rolled back successfully!")
        return True
        
    except sqlite3.Error as e:
        print(f"✗ Error during rollback: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        rollback_migration()
    else:
        success = add_gamification_columns()
        if success:
            print("\n" + "="*50)
            print("Migration completed! You can now use the test function to verify.")
            print("Run: python test_gamification_columns.py")
            print("="*50)
        else:
            print("\n" + "="*50)
            print("Migration failed! Please check the errors above.")
            print("="*50)
            sys.exit(1)
