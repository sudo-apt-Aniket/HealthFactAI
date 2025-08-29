-- SQL Migration Script to Add Gamification Columns to Users Table
-- This script can be executed directly with SQLite command line tool
-- Usage: sqlite3 healthfact.db < migration.sql

-- Enable foreign key constraints (good practice)
PRAGMA foreign_keys = ON;

-- Add gamification columns to users table
-- Using IF NOT EXISTS equivalent for SQLite (will fail gracefully if column exists)

-- Add facts_learned column (JSON array of learned facts)
ALTER TABLE users ADD COLUMN facts_learned TEXT DEFAULT '[]';

-- Add current_streak column (current daily streak count)
ALTER TABLE users ADD COLUMN current_streak INTEGER DEFAULT 0;

-- Add last_activity_date column (last date user learned a fact)
ALTER TABLE users ADD COLUMN last_activity_date DATE;

-- Add longest_streak column (best streak ever achieved)
ALTER TABLE users ADD COLUMN longest_streak INTEGER DEFAULT 0;

-- Add total_facts_count column (total facts learned count)
ALTER TABLE users ADD COLUMN total_facts_count INTEGER DEFAULT 0;

-- Display the updated table structure
.schema users

-- Show a sample of the updated table (will be empty if no users exist)
SELECT 'Updated users table structure:' as message;
PRAGMA table_info(users);
