"""
Database module for Ollama Desktop API
Handles SQLite database operations for storing settings, models, sessions, and chat history
"""

import os
import json
import sqlite3
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager
from pathlib import Path
import sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from api.config_io import read_ollama_config
from api.logger import app_logger
from datetime import datetime

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ollama_desktop.db")

# SQL statements for creating tables
CREATE_TABLES_SQL = """
-- Settings table
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Models table
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    parameters TEXT,  -- JSON string
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    model_name TEXT NOT NULL,
    session_type TEXT NOT NULL,  -- 'chatbot'
    system_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Chat history table
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);
"""

def get_db_connection():
    """Create a connection to the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database by creating tables if they don't exist"""
    conn = get_db_connection()
    try:
        conn.executescript(CREATE_TABLES_SQL)
        conn.commit()
    finally:
        conn.close()

@asynccontextmanager
async def async_db_connection():
    """Async context manager for database connections"""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

# ----- Settings operations -----

async def get_setting(key: str) -> Optional[str]:
    """Get a setting value by key"""
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        return result['value'] if result else None

async def set_setting(key: str, value: str) -> None:
    """Set a setting value"""
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP",
            (key, value, value)
        )
        conn.commit()

# ----- Models operations -----

async def get_models(sort_by: str = None) -> List[Dict]:
    """
    Get all models from the database
    
    Args:
        sort_by: Optional sorting parameter - 'last_used' to sort by last usage time
                 or 'name' to sort alphabetically
    """
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        
        # Determine sorting
        if sort_by == 'last_used':
            # Sort by last_used (most recent first), with NULL values last
            order_clause = "ORDER BY last_used IS NULL, last_used DESC"
        elif sort_by == 'name':
            order_clause = "ORDER BY name ASC"
        else:
            order_clause = ""  # Default sorting (by ID)
            
        cursor.execute(f"SELECT name, description, parameters, last_used FROM models {order_clause}")
        rows = cursor.fetchall()
        result = []
        for row in rows:
            model = dict(row)
            if model['parameters']:
                model['parameters'] = json.loads(model['parameters'])
            result.append(model)
        return result

async def save_model(name: str, description: Optional[str] = None, parameters: Optional[Dict] = None) -> None:
    """Save or update a model in the database"""
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        params_json = json.dumps(parameters) if parameters else None
        cursor.execute(
            "INSERT INTO models (name, description, parameters, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(name) DO UPDATE SET description = ?, parameters = ?, updated_at = CURRENT_TIMESTAMP",
            (name, description, params_json, description, params_json)
        )
        conn.commit()

async def ensure_model_exists(model_name: str) -> None:
    """Ensure a model exists in the database, inserting only if it's missing."""
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM models WHERE name = ?", (model_name,))
        result = cursor.fetchone()
        if not result:
            # Model doesn't exist, insert it with minimal info
            cursor.execute(
                "INSERT INTO models (name, updated_at) VALUES (?, CURRENT_TIMESTAMP)",
                (model_name,)
            )
            conn.commit()

async def update_model_usage(model_name: str) -> None:
    """
    Update the last_used timestamp for a model
    This should be called whenever a model is used in a session
    """
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        
        # Ensure the model exists first (using the new function)
        await ensure_model_exists(model_name)
        
        # Now update the last_used timestamp
        cursor.execute(
            "UPDATE models SET last_used = CURRENT_TIMESTAMP WHERE name = ?",
            (model_name,)
        )
        conn.commit()

async def get_recently_used_models(limit: int = 5) -> List[Dict]:
    """
    Get the most recently used models
    
    Args:
        limit: Maximum number of models to return
    """
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, description, parameters, last_used FROM models "
            "WHERE last_used IS NOT NULL "
            "ORDER BY last_used DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            model = dict(row)
            if model['parameters']:
                model['parameters'] = json.loads(model['parameters'])
            result.append(model)
        return result

# ----- Sessions operations -----

async def create_session(session_id: str, model_name: str, session_type: str, 
                          system_message: Optional[str] = None) -> None:
    """Create a new session in the database"""
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (session_id, model_name, session_type, system_message) "
            "VALUES (?, ?, ?, ?)",
            (session_id, model_name, session_type, system_message)
        )
        conn.commit()
    
    # Update the model's last_used timestamp
    await update_model_usage(model_name)

async def get_session(session_id: str) -> Optional[Dict]:
    """Get session details by session_id"""
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        result = cursor.fetchone()
        return dict(result) if result else None

async def update_session_activity(session_id: str) -> None:
    """Update the last_active timestamp for a session"""
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET last_active = CURRENT_TIMESTAMP WHERE session_id = ?",
            (session_id,)
        )
        conn.commit()

async def deactivate_session(session_id: str) -> None:
    """Mark a session as inactive"""
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET is_active = FALSE WHERE session_id = ?",
            (session_id,)
        )
        conn.commit()

async def get_active_sessions() -> List[Dict]:
    """Get all active sessions"""
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE is_active = TRUE")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

async def get_all_sessions(include_inactive: bool = False, limit: int = 100, offset: int = 0) -> List[Dict]:
    """
    Get all sessions from the database
    
    Args:
        include_inactive: Whether to include inactive sessions
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip (for pagination)
    """
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        
        # Build the query based on whether to include inactive sessions
        if include_inactive:
            query = "SELECT * FROM sessions"
        else:
            query = "SELECT * FROM sessions WHERE is_active = TRUE"
            
        # Add order by most recent first and pagination
        query += " ORDER BY last_active DESC LIMIT ? OFFSET ?"
        
        cursor.execute(query, (limit, offset))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

async def get_sessions_with_message_count(
    include_inactive: bool = True,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """
    Get all sessions with a count of messages in each session
    
    Args:
        include_inactive: Whether to include inactive sessions
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip (for pagination)
    """
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        
        # Base query with message counts and time bounds
        query = """
            SELECT s.*, 
                   COUNT(ch.id) as message_count,
                   MIN(ch.timestamp) as first_message_time,
                   MAX(ch.timestamp) as last_message_time
            FROM sessions s
            LEFT JOIN chat_history ch ON s.session_id = ch.session_id
        """
        
        # Add filter for active/inactive if needed
        params = []
        if not include_inactive:
            query += " WHERE s.is_active = TRUE"
            
        # Complete the query with grouping and ordering
        query += """
            GROUP BY s.session_id
            ORDER BY s.last_active DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

async def delete_session_permanently(session_id: str) -> None:
    """Permanently delete a session and its chat history from the database"""
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        # Ensure foreign key constraints are enabled (usually on by default but good practice)
        cursor.execute("PRAGMA foreign_keys = ON") 
        # Deleting from sessions will cascade delete from chat_history due to ON DELETE CASCADE
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
        app_logger.info(f"Permanently deleted session {session_id} and its history from the database.")

# ----- Chat history operations -----

async def add_chat_message(session_id: str, role: str, message: str) -> None:
    """Add a message to the chat history"""
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_history (session_id, role, message) VALUES (?, ?, ?)",
            (session_id, role, message)
        )
        conn.commit()

async def get_chat_history(session_id: str, limit: int = 100) -> List[Dict]:
    """Get chat history for a session"""
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, message, timestamp FROM chat_history "
            "WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
            (session_id, limit)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

async def get_filtered_chat_history(
    session_id: str, 
    limit: int = 100, 
    offset: int = 0,
    role: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict]:
    """
    Get filtered chat history for a session
    
    Args:
        session_id: The session ID to get history for
        limit: Maximum number of messages to return
        offset: Number of messages to skip (for pagination)
        role: Filter by message role ('user' or 'assistant')
        start_date: Filter messages after this date (format: YYYY-MM-DD)
        end_date: Filter messages before this date (format: YYYY-MM-DD)
    """
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        
        # Build query with filters
        query = "SELECT role, message, timestamp FROM chat_history WHERE session_id = ?"
        params = [session_id]
        
        # Add role filter if provided
        if role:
            query += " AND role = ?"
            params.append(role)
        
        # Add date filters if provided
        if start_date:
            query += " AND date(timestamp) >= date(?)"
            params.append(start_date)
        
        if end_date:
            query += " AND date(timestamp) <= date(?)"
            params.append(end_date)
        
        # Add order and pagination
        query += " ORDER BY timestamp ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

async def search_chats(
    search_term: str,
    include_inactive: bool = True,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """
    Search for sessions with matching text in messages, model name, or system message
    
    Args:
        search_term: Text to search for
        include_inactive: Whether to include inactive sessions
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip (for pagination)
    """
    async with async_db_connection() as conn:
        cursor = conn.cursor()
        
        # Base query with joins to find sessions with matching messages
        query = """
            SELECT DISTINCT s.*,
                   COUNT(DISTINCT ch.id) as message_count,
                   MIN(ch.timestamp) as first_message_time,
                   MAX(ch.timestamp) as last_message_time
            FROM sessions s
            LEFT JOIN chat_history ch ON s.session_id = ch.session_id
            WHERE (
                ch.message LIKE ? 
                OR s.model_name LIKE ? 
                OR s.system_message LIKE ?
            )
        """
        
        search_pattern = f"%{search_term}%"
        params = [search_pattern, search_pattern, search_pattern]
        
        # Add filter for active/inactive if needed
        if not include_inactive:
            query += " AND s.is_active = TRUE"
            
        # Complete the query with grouping and ordering
        query += """
            GROUP BY s.session_id
            ORDER BY s.last_active DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

# ----- Migrations for future changes -----

def check_column_exists(conn, table, column):
    """Check if a column exists in a table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    return any(col["name"] == column for col in columns)

def add_column_if_not_exists(conn, table, column, type_definition):
    """Add a column to a table if it doesn't exist"""
    if not check_column_exists(conn, table, column):
        cursor = conn.cursor()
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_definition}")
        conn.commit()

def migrate_database():
    """Apply database migrations"""
    conn = get_db_connection()
    try:
        # Example migration (add columns if they don't exist)
        add_column_if_not_exists(conn, "settings", "description", "TEXT")
        
        # You can add more migrations here as needed
        # For example, to add a new column to an existing table:
        # add_column_if_not_exists(conn, "sessions", "new_column", "TEXT DEFAULT NULL")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    
    print("Applying database migrations...")
    migrate_database()
    
    print("Database setup complete!")