#!/usr/bin/env python3
"""
Standalone migration script to add gamification columns to the users table.
This script doesn't depend on the existing database.py module to avoid connection issues.
"""

import sqlite3
import sys
import os
from datetime import datetime

# Database file path
DB_PATH = "healthfact.db"

def add_gamification_columns():
    """
    Add gamification columns to the existing users table.
    Uses ALTER TABLE with error handling for existing columns.
    """
    print(f"Starting migration to add gamification columns to users table...")
    print(f"Database path: {os.path.abspath(DB_PATH)}")
    
    # Check if database file exists
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} does not exist. Creating it first...")
        # Create the database and users table
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )
            """)
            conn.commit()
            conn.close()
            print("✓ Database and users table created successfully!")
        except sqlite3.Error as e:
            print(f"✗ Error creating database: {e}")
            return False
    
    # Now proceed with the migration
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency
        cursor = conn.cursor()
        
        # List of columns to add with their definitions
        columns_to_add = [
            ("facts_learned", "TEXT DEFAULT '[]'"),
            ("current_streak", "INTEGER DEFAULT 0"),
            ("last_activity_date", "DATE"),
            ("longest_streak", "INTEGER DEFAULT 0"),
            ("total_facts_count", "INTEGER DEFAULT 0")
        ]
        
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
                conn.rollback()
                return False
        
        # Commit all changes
        conn.commit()
        
        print(f"\nMigration completed successfully!")
        print(f"Columns added: {columns_added}")
        print(f"Columns skipped (already existed): {columns_skipped}")
        
        # Verify the final table structure
        cursor.execute("PRAGMA table_info(users)")
        final_columns = cursor.fetchall()
        print(f"\nFinal table structure:")
        for col in final_columns:
            col_id, name, data_type, not_null, default_value, pk = col
            default_str = f" DEFAULT {default_value}" if default_value else ""
            null_str = " NOT NULL" if not_null else ""
            pk_str = " PRIMARY KEY" if pk else ""
            print(f"  {name}: {data_type}{default_str}{null_str}{pk_str}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"Database error during migration: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during migration: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def test_migration():
    """
    Quick test to verify the migration worked.
    """
    print("\nTesting migration...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Insert a test user
        cursor.execute("DELETE FROM users WHERE username = 'migration_test_user'")
        cursor.execute("""
            INSERT INTO users (username, password) 
            VALUES ('migration_test_user', 'test_hash')
        """)
        
        # Retrieve the test user with new columns
        cursor.execute("""
            SELECT username, facts_learned, current_streak, 
                   last_activity_date, longest_streak, total_facts_count
            FROM users WHERE username = 'migration_test_user'
        """)
        
        result = cursor.fetchone()
        if result:
            username, facts_learned, current_streak, last_activity_date, longest_streak, total_facts_count = result
            print(f"✓ Test user created successfully:")
            print(f"  Username: {username}")
            print(f"  facts_learned: {facts_learned}")
            print(f"  current_streak: {current_streak}")
            print(f"  last_activity_date: {last_activity_date}")
            print(f"  longest_streak: {longest_streak}")
            print(f"  total_facts_count: {total_facts_count}")
            
            # Clean up test user
            cursor.execute("DELETE FROM users WHERE username = 'migration_test_user'")
            conn.commit()
            
            print("✓ Migration test passed!")
            return True
        else:
            print("✗ Failed to create test user")
            return False
            
    except sqlite3.Error as e:
        print(f"✗ Test failed with database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = add_gamification_columns()
    if success:
        test_success = test_migration()
        if test_success:
            print("\n" + "="*60)
            print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("\nYour users table now includes these gamification columns:")
            print("- facts_learned (TEXT, default '[]')")
            print("- current_streak (INTEGER, default 0)")
            print("- last_activity_date (DATE)")
            print("- longest_streak (INTEGER, default 0)")
            print("- total_facts_count (INTEGER, default 0)")
            print("\nYou can now run: python test_gamification_columns.py")
            print("for comprehensive testing.")
        else:
            print("\n" + "="*60)
            print("⚠️  Migration completed but test failed!")
            print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ MIGRATION FAILED!")
        print("="*60)
        sys.exit(1)
