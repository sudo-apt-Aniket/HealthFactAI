"""
Base repository pattern for database operations.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Any
import sqlite3
from app.core.config import settings

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Base repository with common database operations."""
    
    def __init__(self):
        self.db_name = settings.DB_NAME
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_name, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an entity."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """Delete an entity."""
        pass
    
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute a SELECT query and return results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_command(self, command: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE command and return affected rows."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(command, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_command_get_id(self, command: str, params: tuple = ()) -> int:
        """Execute command and return the last inserted row ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(command, params)
            conn.commit()
            return cursor.lastrowid
