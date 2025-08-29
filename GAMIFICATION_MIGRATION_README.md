# Gamification Columns Migration Guide

This guide provides multiple methods to add gamification columns to your existing users table in the HealthFactAI project.

## Overview

The migration adds the following columns to your `users` table:

- `facts_learned` (TEXT, default '[]') - JSON array of learned facts
- `current_streak` (INTEGER, default 0) - current daily streak count  
- `last_activity_date` (DATE) - last date user learned a fact
- `longest_streak` (INTEGER, default 0) - best streak ever achieved
- `total_facts_count` (INTEGER, default 0) - total facts learned count

## Migration Methods

### Method 1: Direct SQL Script (Recommended)

If you have SQLite command line tool installed:

```bash
# First, ensure your database exists
python -c "from database import init_db; init_db()"

# Then run the migration
sqlite3 healthfact.db < migration.sql
```

### Method 2: Manual SQL Commands

If you prefer to run commands manually:

1. Open SQLite command line:
   ```bash
   sqlite3 healthfact.db
   ```

2. Run these commands one by one:
   ```sql
   ALTER TABLE users ADD COLUMN facts_learned TEXT DEFAULT '[]';
   ALTER TABLE users ADD COLUMN current_streak INTEGER DEFAULT 0;
   ALTER TABLE users ADD COLUMN last_activity_date DATE;
   ALTER TABLE users ADD COLUMN longest_streak INTEGER DEFAULT 0;
   ALTER TABLE users ADD COLUMN total_facts_count INTEGER DEFAULT 0;
   ```

3. Verify the changes:
   ```sql
   PRAGMA table_info(users);
   .quit
   ```

### Method 3: Python Script (If SQLite access works)

If the Python SQLite access issue is resolved:

```bash
python migration_standalone.py
```

## Verification

After running the migration, verify it worked by running:

```bash
python test_gamification_columns.py
```

Or manually check the table structure:

```bash
sqlite3 healthfact.db "PRAGMA table_info(users);"
```

Expected output should include these columns:
```
3|facts_learned|TEXT|0|'[]'|0
4|current_streak|INTEGER|0|0|0
5|last_activity_date|DATE|0||0
6|longest_streak|INTEGER|0|0|0
7|total_facts_count|INTEGER|0|0|0
```

## Usage Examples

### Updating User Gamification Data

```python
import sqlite3
import json
from datetime import date

def update_user_gamification(username, new_fact):
    conn = sqlite3.connect('healthfact.db')
    cursor = conn.cursor()
    
    # Get current user data
    cursor.execute("""
        SELECT facts_learned, current_streak, longest_streak, total_facts_count
        FROM users WHERE username = ?
    """, (username,))
    
    result = cursor.fetchone()
    if result:
        facts_learned, current_streak, longest_streak, total_facts_count = result
        
        # Parse existing facts
        facts_list = json.loads(facts_learned)
        
        # Add new fact
        facts_list.append({
            "id": len(facts_list) + 1,
            "fact": new_fact,
            "learned_date": date.today().isoformat()
        })
        
        # Update counters
        new_total = total_facts_count + 1
        new_streak = current_streak + 1  # Simplified - you'd check dates in real implementation
        new_longest = max(longest_streak, new_streak)
        
        # Update database
        cursor.execute("""
            UPDATE users 
            SET facts_learned = ?, 
                current_streak = ?, 
                last_activity_date = ?, 
                longest_streak = ?, 
                total_facts_count = ?
            WHERE username = ?
        """, (json.dumps(facts_list), new_streak, date.today().isoformat(), 
              new_longest, new_total, username))
        
        conn.commit()
    
    conn.close()

# Example usage
update_user_gamification("john_doe", "Regular exercise strengthens the heart")
```

### Retrieving User Progress

```python
def get_user_progress(username):
    conn = sqlite3.connect('healthfact.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT current_streak, longest_streak, total_facts_count, 
               last_activity_date, facts_learned
        FROM users WHERE username = ?
    """, (username,))
    
    result = cursor.fetchone()
    if result:
        current_streak, longest_streak, total_facts_count, last_activity_date, facts_learned = result
        
        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "total_facts_count": total_facts_count,
            "last_activity_date": last_activity_date,
            "facts_learned": json.loads(facts_learned)
        }
    
    conn.close()
    return None
```

## Integration with FastAPI

Add these endpoints to your `main.py`:

```python
from pydantic import BaseModel
from typing import List, Optional
import json

class UserProgress(BaseModel):
    current_streak: int
    longest_streak: int
    total_facts_count: int
    last_activity_date: Optional[str]
    facts_learned: List[dict]

@app.get("/user/{username}/progress", response_model=UserProgress)
def get_user_progress(username: str, token: str = Depends(oauth2_scheme)):
    # Add authentication logic here
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""
        SELECT current_streak, longest_streak, total_facts_count, 
               last_activity_date, facts_learned
        FROM users WHERE username = ?
    """, (username,))
    
    result = c.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    current_streak, longest_streak, total_facts_count, last_activity_date, facts_learned = result
    
    return UserProgress(
        current_streak=current_streak,
        longest_streak=longest_streak,
        total_facts_count=total_facts_count,
        last_activity_date=last_activity_date,
        facts_learned=json.loads(facts_learned)
    )

class LearnFactRequest(BaseModel):
    fact: str

@app.post("/user/{username}/learn-fact")
def learn_fact(username: str, request: LearnFactRequest, token: str = Depends(oauth2_scheme)):
    # Add authentication logic here
    # Implementation similar to update_user_gamification function above
    pass
```

## Troubleshooting

### Column Already Exists Error
If you get "duplicate column name" errors, the columns already exist. You can check with:
```bash
sqlite3 healthfact.db "PRAGMA table_info(users);"
```

### Database Lock Issues
If you encounter database lock issues:
1. Make sure no other processes are using the database
2. Try closing any open database connections
3. Restart your development server

### Testing the Migration
Always test the migration on a backup of your database first:
```bash
cp healthfact.db healthfact_backup.db
# Run migration on the backup first
```

## Files Created

- `migration.sql` - Direct SQL migration script
- `migration_standalone.py` - Python migration script
- `migration_add_gamification_columns.py` - Original migration script
- `test_gamification_columns.py` - Comprehensive test suite
- `GAMIFICATION_MIGRATION_README.md` - This documentation

## Next Steps

After successful migration:
1. Update your user registration/login logic to initialize gamification fields
2. Add endpoints for tracking fact learning
3. Implement streak calculation logic
4. Add gamification UI components
5. Consider adding indexes for performance if you have many users

## Support

If you encounter issues:
1. Check that SQLite is properly installed
2. Verify database file permissions
3. Ensure no other processes are locking the database
4. Try the manual SQL method if Python scripts fail
