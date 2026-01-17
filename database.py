"""
Database schema and operations for the activity tracker.
"""
import sqlite3
import re
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
import config

# Cache for compiled regex patterns
_regex_cache = {}


def get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """Create all tables and default categories."""
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
    
    # Insert default "Uncategorized" category if not exists
    cursor.execute("""
        INSERT OR IGNORE INTO category (name, color, description)
        VALUES (?, ?, ?)
    """, (config.UNCATEGORIZED_CATEGORY, "#999999", "Activities without a category"))
    
    conn.commit()
    conn.close()


def add_category(name: str, color: Optional[str] = None, description: Optional[str] = None) -> int:
    """Add a new category."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO category (name, color, description)
        VALUES (?, ?, ?)
    """, (name, color, description))
    category_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return category_id


def add_category_rule(pattern: str, match_field: str, category_id: int, priority: int = 0) -> int:
    """Add a new category rule."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO category_rule (pattern, match_field, category_id, priority)
        VALUES (?, ?, ?, ?)
    """, (pattern, match_field, category_id, priority))
    rule_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return rule_id


def get_all_category_rules() -> List[Dict[str, Any]]:
    """Get all category rules ordered by priority (highest first)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, pattern, match_field, category_id, priority
        FROM category_rule
        ORDER BY priority DESC
    """)
    rules = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rules


def match_category(process_name: str, window_title: str, url: Optional[str] = None) -> Optional[int]:
    """
    Match activity to a category based on rules.
    Returns category_id or None if no match.
    """
    rules = get_all_category_rules()
    
    for rule in rules:
        field_value = None
        if rule['match_field'] == 'process_name':
            field_value = process_name
        elif rule['match_field'] == 'window_title':
            field_value = window_title
        elif rule['match_field'] == 'url':
            field_value = url
        
        if field_value:
            # Use cached compiled regex pattern
            pattern = rule['pattern']
            if pattern not in _regex_cache:
                _regex_cache[pattern] = re.compile(pattern, re.IGNORECASE)
            
            if _regex_cache[pattern].search(field_value):
                return rule['category_id']
    
    return None


def log_activity(timestamp: datetime, duration_seconds: int, process_name: str, 
                 window_title: str, url: Optional[str] = None, 
                 chrome_profile: Optional[str] = None, 
                 category_id: Optional[int] = None):
    """Log an activity to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # If no category provided, try to match one
    if category_id is None:
        category_id = match_category(process_name, window_title, url)
    
    cursor.execute("""
        INSERT INTO activity_log 
        (timestamp, duration_seconds, process_name, window_title, url, chrome_profile, category_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (timestamp.isoformat(), duration_seconds, process_name, window_title, url, chrome_profile, category_id))
    
    conn.commit()
    conn.close()


def get_categories() -> List[Dict[str, Any]]:
    """Get all categories."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, color, description FROM category ORDER BY name")
    categories = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return categories


def get_category_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get a category by name."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, color, description FROM category WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_activities(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get activities with optional date filtering."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT a.*, c.name as category_name
        FROM activity_log a
        LEFT JOIN category c ON a.category_id = c.id
        WHERE 1=1
    """
    params = []
    
    if start_date:
        query += " AND a.timestamp >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND a.timestamp <= ?"
        params.append(end_date)
    
    query += " ORDER BY a.timestamp DESC"
    
    cursor.execute(query, params)
    activities = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return activities
