"""
User repository for database operations.
"""
from typing import Optional, List
import sqlite3
from app.repositories.base import BaseRepository
from app.models.user import User

class UserRepository(BaseRepository[User]):
    """Repository for user-related database operations."""
    
    def create(self, user: User) -> User:
        """Create a new user."""
        command = """
            INSERT INTO users (username, password, email, facts_learned, current_streak, 
                             longest_streak, total_facts_count, last_activity_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            user.username, user.password, user.email, user.facts_learned,
            user.current_streak, user.longest_streak, user.total_facts_count,
            user.last_activity_date
        )
        
        user_id = self.execute_command_get_id(command, params)
        user.id = user_id
        return user
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        query = """
            SELECT id, username, password, email, facts_learned, current_streak,
                   longest_streak, total_facts_count, last_activity_date
            FROM users WHERE id = ?
        """
        rows = self.execute_query(query, (user_id,))
        return User.from_db_row(rows[0]) if rows else None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        query = """
            SELECT id, username, password, email, facts_learned, current_streak,
                   longest_streak, total_facts_count, last_activity_date
            FROM users WHERE username = ?
        """
        rows = self.execute_query(query, (username,))
        return User.from_db_row(rows[0]) if rows else None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        query = """
            SELECT id, username, password, email, facts_learned, current_streak,
                   longest_streak, total_facts_count, last_activity_date
            FROM users WHERE email = ?
        """
        rows = self.execute_query(query, (email,))
        return User.from_db_row(rows[0]) if rows else None
    
    def get_by_username_or_email(self, identifier: str) -> Optional[User]:
        """Get user by username or email."""
        if "@" in identifier:
            return self.get_by_email(identifier)
        else:
            return self.get_by_username(identifier)
    
    def update(self, user: User) -> User:
        """Update user."""
        command = """
            UPDATE users 
            SET username = ?, password = ?, email = ?, facts_learned = ?,
                current_streak = ?, longest_streak = ?, total_facts_count = ?,
                last_activity_date = ?
            WHERE id = ?
        """
        params = (
            user.username, user.password, user.email, user.facts_learned,
            user.current_streak, user.longest_streak, user.total_facts_count,
            user.last_activity_date, user.id
        )
        
        self.execute_command(command, params)
        return user
    
    def update_progress(self, user_id: int, facts_learned: str, total_facts_count: int,
                       current_streak: int, longest_streak: int, last_activity_date: str) -> bool:
        """Update user progress fields efficiently."""
        command = """
            UPDATE users 
            SET facts_learned = ?, total_facts_count = ?, current_streak = ?,
                longest_streak = ?, last_activity_date = ?
            WHERE id = ?
        """
        params = (facts_learned, total_facts_count, current_streak, 
                 longest_streak, last_activity_date, user_id)
        
        return self.execute_command(command, params) > 0
    
    def delete(self, user_id: int) -> bool:
        """Delete user."""
        command = "DELETE FROM users WHERE id = ?"
        return self.execute_command(command, (user_id,)) > 0
    
    def exists_username(self, username: str) -> bool:
        """Check if username exists."""
        query = "SELECT 1 FROM users WHERE username = ?"
        rows = self.execute_query(query, (username,))
        return len(rows) > 0
    
    def exists_email(self, email: str) -> bool:
        """Check if email exists."""
        if not email:
            return False
        query = "SELECT 1 FROM users WHERE email = ?"
        rows = self.execute_query(query, (email,))
        return len(rows) > 0
