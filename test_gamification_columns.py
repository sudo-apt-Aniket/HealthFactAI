#!/usr/bin/env python3
"""
Test script to verify that gamification columns were added successfully to the users table.
This script tests the new columns and demonstrates their usage.
"""

import sqlite3
import json
from datetime import datetime, date
from database import get_db, DB_NAME

def test_gamification_columns():
    """
    Test function to verify that all gamification columns were added successfully.
    """
    print("Testing gamification columns in users table...")
    print(f"Database: {DB_NAME}")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Test 1: Check if all columns exist
        print("\n1. Checking table structure...")
        cursor.execute("PRAGMA table_info(users)")
        columns_info = cursor.fetchall()
        
        expected_columns = [
            'id', 'username', 'password', 
            'facts_learned', 'current_streak', 'last_activity_date', 
            'longest_streak', 'total_facts_count'
        ]
        
        existing_columns = [col[1] for col in columns_info]
        print(f"Existing columns: {existing_columns}")
        
        missing_columns = [col for col in expected_columns if col not in existing_columns]
        if missing_columns:
            print(f"✗ Missing columns: {missing_columns}")
            return False
        else:
            print("✓ All expected columns are present!")
        
        # Test 2: Check column types and defaults
        print("\n2. Checking column definitions...")
        column_details = {col[1]: {'type': col[2], 'default': col[4]} for col in columns_info}
        
        expected_types = {
            'facts_learned': 'TEXT',
            'current_streak': 'INTEGER',
            'last_activity_date': 'DATE',
            'longest_streak': 'INTEGER',
            'total_facts_count': 'INTEGER'
        }
        
        for col_name, expected_type in expected_types.items():
            actual_type = column_details[col_name]['type']
            if expected_type in actual_type:
                print(f"✓ {col_name}: {actual_type}")
            else:
                print(f"✗ {col_name}: Expected {expected_type}, got {actual_type}")
        
        # Test 3: Create a test user and verify default values
        print("\n3. Testing default values with a test user...")
        
        # Clean up any existing test user
        cursor.execute("DELETE FROM users WHERE username = 'test_gamification_user'")
        
        # Insert test user
        cursor.execute("""
            INSERT INTO users (username, password) 
            VALUES ('test_gamification_user', 'test_password_hash')
        """)
        
        # Retrieve the test user
        cursor.execute("""
            SELECT id, username, facts_learned, current_streak, 
                   last_activity_date, longest_streak, total_facts_count
            FROM users WHERE username = 'test_gamification_user'
        """)
        
        test_user = cursor.fetchone()
        if test_user:
            user_id, username, facts_learned, current_streak, last_activity_date, longest_streak, total_facts_count = test_user
            
            print(f"Test user created with ID: {user_id}")
            print(f"  facts_learned: {facts_learned} (should be '[]')")
            print(f"  current_streak: {current_streak} (should be 0)")
            print(f"  last_activity_date: {last_activity_date} (should be None)")
            print(f"  longest_streak: {longest_streak} (should be 0)")
            print(f"  total_facts_count: {total_facts_count} (should be 0)")
            
            # Verify defaults
            defaults_correct = (
                facts_learned == '[]' and
                current_streak == 0 and
                last_activity_date is None and
                longest_streak == 0 and
                total_facts_count == 0
            )
            
            if defaults_correct:
                print("✓ All default values are correct!")
            else:
                print("✗ Some default values are incorrect!")
                return False
        else:
            print("✗ Failed to create test user!")
            return False
        
        # Test 4: Test updating gamification data
        print("\n4. Testing gamification data updates...")
        
        # Update gamification data
        sample_facts = json.dumps([
            {"id": 1, "fact": "Drinking water helps maintain body temperature", "learned_date": "2024-01-15"},
            {"id": 2, "fact": "Regular exercise strengthens the heart", "learned_date": "2024-01-16"}
        ])
        
        today = date.today().isoformat()
        
        cursor.execute("""
            UPDATE users 
            SET facts_learned = ?, 
                current_streak = ?, 
                last_activity_date = ?, 
                longest_streak = ?, 
                total_facts_count = ?
            WHERE username = 'test_gamification_user'
        """, (sample_facts, 5, today, 10, 25))
        
        # Verify updates
        cursor.execute("""
            SELECT facts_learned, current_streak, last_activity_date, 
                   longest_streak, total_facts_count
            FROM users WHERE username = 'test_gamification_user'
        """)
        
        updated_data = cursor.fetchone()
        if updated_data:
            facts_learned, current_streak, last_activity_date, longest_streak, total_facts_count = updated_data
            
            print(f"Updated data:")
            print(f"  facts_learned: {len(json.loads(facts_learned))} facts stored")
            print(f"  current_streak: {current_streak}")
            print(f"  last_activity_date: {last_activity_date}")
            print(f"  longest_streak: {longest_streak}")
            print(f"  total_facts_count: {total_facts_count}")
            
            # Verify JSON parsing works
            try:
                parsed_facts = json.loads(facts_learned)
                print(f"✓ JSON parsing successful, {len(parsed_facts)} facts loaded")
                print(f"  Sample fact: {parsed_facts[0]['fact']}")
            except json.JSONDecodeError:
                print("✗ JSON parsing failed!")
                return False
            
            print("✓ Gamification data updates working correctly!")
        else:
            print("✗ Failed to retrieve updated data!")
            return False
        
        # Clean up test user
        cursor.execute("DELETE FROM users WHERE username = 'test_gamification_user'")
        conn.commit()
        
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED! Gamification columns are working correctly!")
        print("="*60)
        print("\nYou can now use these columns in your application:")
        print("- facts_learned: Store JSON array of learned facts")
        print("- current_streak: Track daily learning streaks")
        print("- last_activity_date: Record last learning activity")
        print("- longest_streak: Store best streak achievement")
        print("- total_facts_count: Count total facts learned")
        
        return True
        
    except sqlite3.Error as e:
        print(f"✗ Database error during testing: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during testing: {e}")
        return False
    finally:
        conn.close()

def show_current_schema():
    """
    Display the current users table schema for reference.
    """
    print("Current users table schema:")
    print("-" * 40)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        for col in columns:
            col_id, name, data_type, not_null, default_value, pk = col
            default_str = f" DEFAULT {default_value}" if default_value else ""
            null_str = " NOT NULL" if not_null else ""
            pk_str = " PRIMARY KEY" if pk else ""
            print(f"{name}: {data_type}{default_str}{null_str}{pk_str}")
            
    except sqlite3.Error as e:
        print(f"Error retrieving schema: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--schema":
        show_current_schema()
    else:
        success = test_gamification_columns()
        if not success:
            print("\n" + "="*60)
            print("❌ TESTS FAILED! Please check the migration script.")
            print("="*60)
            sys.exit(1)
