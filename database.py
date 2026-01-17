"""
Database schema and operations for Activity Tracker.
"""

import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
import config


def get_connection() -> sqlite3.Connection:
    """Get a connection to the database."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create category table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS category (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            color TEXT,
            description TEXT
        )
    """)
    
    # Create category_rule table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS category_rule (
            id INTEGER PRIMARY KEY,
            pattern TEXT NOT NULL,
            match_field TEXT NOT NULL CHECK(match_field IN ('url', 'window_title', 'process_name')),
            category_id INTEGER NOT NULL REFERENCES category(id),
            priority INTEGER NOT NULL DEFAULT 0
        )
    """)
    
    # Create activity_log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            duration_seconds INTEGER NOT NULL,
            process_name TEXT NOT NULL,
            window_title TEXT NOT NULL,
            url TEXT,
            chrome_profile TEXT,
            category_id INTEGER REFERENCES category(id)
        )
    """)
    
    conn.commit()
    conn.close()


# Category operations
def add_category(name: str, color: Optional[str] = None, description: Optional[str] = None) -> int:
    """Add a new category."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO category (name, color, description) VALUES (?, ?, ?)",
        (name, color, description)
    )
    category_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return category_id


def get_all_categories() -> List[Dict[str, Any]]:
    """Get all categories."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM category ORDER BY name")
    categories = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return categories


def delete_category(category_id: int):
    """Delete a category."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM category WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()


# Category rule operations
def add_category_rule(pattern: str, match_field: str, category_id: int, priority: int = 0) -> int:
    """Add a new category rule."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO category_rule (pattern, match_field, category_id, priority) VALUES (?, ?, ?, ?)",
        (pattern, match_field, category_id, priority)
    )
    rule_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return rule_id


def get_all_category_rules() -> List[Dict[str, Any]]:
    """Get all category rules ordered by priority (highest first)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM category_rule ORDER BY priority DESC")
    rules = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rules


def delete_category_rule(rule_id: int):
    """Delete a category rule."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM category_rule WHERE id = ?", (rule_id,))
    conn.commit()
    conn.close()


# Activity log operations
def add_activity_log(
    timestamp: str,
    duration_seconds: int,
    process_name: str,
    window_title: str,
    url: Optional[str] = None,
    chrome_profile: Optional[str] = None,
    category_id: Optional[int] = None
) -> int:
    """Add a new activity log entry."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO activity_log 
        (timestamp, duration_seconds, process_name, window_title, url, chrome_profile, category_id) 
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (timestamp, duration_seconds, process_name, window_title, url, chrome_profile, category_id)
    )
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id


def get_activity_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Get activity logs with optional filters."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM activity_log WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date)
    
    if category_id is not None:
        query += " AND category_id = ?"
        params.append(category_id)
    
    query += " ORDER BY timestamp DESC"
    
    cursor.execute(query, params)
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return logs


def get_activity_summary_by_category(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get total time spent by category."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            c.name as category_name,
            c.color,
            SUM(al.duration_seconds) as total_seconds,
            COUNT(*) as activity_count
        FROM activity_log al
        LEFT JOIN category c ON al.category_id = c.id
        WHERE 1=1
    """
    params = []
    
    if start_date:
        query += " AND al.timestamp >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND al.timestamp <= ?"
        params.append(end_date)
    
    query += " GROUP BY al.category_id ORDER BY total_seconds DESC"
    
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_activity_summary_by_process(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get total time spent by process."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            process_name,
            SUM(duration_seconds) as total_seconds,
            COUNT(*) as activity_count
        FROM activity_log
        WHERE 1=1
    """
    params = []
    
    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date)
    
    query += " GROUP BY process_name ORDER BY total_seconds DESC"
    
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_activity_summary_by_chrome_profile(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get total time spent by Chrome profile."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            chrome_profile,
            SUM(duration_seconds) as total_seconds,
            COUNT(*) as activity_count
        FROM activity_log
        WHERE chrome_profile IS NOT NULL
    """
    params = []
    
    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date)
    
    query += " GROUP BY chrome_profile ORDER BY total_seconds DESC"
    
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results
