"""
Database module for Ollama MCP API
Handles SQLite database operations for storing settings, models, sessions, and chat history
"""

import os
import json
import sqlite3
import datetime
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ollama_mcp.db")

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
    session_type TEXT NOT NULL,  -- 'chatbot' or 'mcp_client'
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

# ----- Database migration functions -----

def check_column_exists(conn, table, column):
    """Check if a column exists in the given table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    return any(col['name'] == column for col in columns)

def add_column_if_not_exists(conn, table, column, type_definition):
    """Add a column to a table if it doesn't exist"""
    if not check_column_exists(conn, table, column):
        cursor = conn.cursor()
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_definition}")
        return True
    return False

def migrate_database():
    """Apply database migrations"""
    conn = get_db_connection()
    try:
        # Add last_used column to models table if it doesn't exist
        if add_column_if_not_exists(conn, "models", "last_used", "TIMESTAMP"):
            print("Migration: Added 'last_used' column to models table")
        
        # Add any future migrations here
        
        conn.commit()
        print("Database migration completed successfully")
    except Exception as e:
        conn.rollback()
        print(f"Error during database migration: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    
    print("Applying database migrations...")
    migrate_database()
    
    print("Database setup complete!")