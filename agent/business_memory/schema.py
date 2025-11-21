"""
Business memory database schema.

PHASE 7.3: Stores structured information about user's business
learned from conversations.

Database Tables:
    - company_info: Company details (name, industry, size, etc.)
    - team_members: People and their roles
    - projects: Active and past projects
    - preferences: User preferences and settings
    - integrations: Integration credentials (encrypted)
    - facts: Generic facts with full-text search
    - relationships: Connections between entities
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class MemoryDatabase:
    """
    SQLite database for business memory.

    Provides structured storage for business knowledge
    with support for relationships and full-text search.
    """

    def __init__(self, db_path: str = "data/business_memory.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Connect with check_same_thread=False for async usage
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access

        self._init_schema()

    def _init_schema(self):
        """Initialize database schema with all tables"""
        cursor = self.conn.cursor()

        # Company information table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Team members table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                role TEXT,
                department TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active',
                path TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # User preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, key)
            )
        """)

        # Integration credentials table (encrypted)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS integrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL UNIQUE,
                credentials_encrypted TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Generic facts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                fact TEXT NOT NULL,
                confidence REAL DEFAULT 0.8,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)

        # Relationships table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity1_type TEXT NOT NULL,
                entity1_id INTEGER NOT NULL,
                relationship_type TEXT NOT NULL,
                entity2_type TEXT NOT NULL,
                entity2_id INTEGER NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Full-text search virtual table for facts
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts
            USING fts5(category, fact, content='facts', content_rowid='id')
        """)

        # Indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_team_email ON team_members(email)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_preferences_category ON preferences(category)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category)
        """)

        self.conn.commit()

    # ══════════════════════════════════════════════════════════════════════
    # Company Info Methods
    # ══════════════════════════════════════════════════════════════════════

    def store_company_info(self, key: str, value: str, confidence: float = 1.0, source: str = None):
        """Store company information"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO company_info (key, value, confidence, source)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                confidence = excluded.confidence,
                updated_at = CURRENT_TIMESTAMP
        """, (key, value, confidence, source))
        self.conn.commit()

    def get_company_info(self, key: str = None) -> Dict[str, Any]:
        """Get company information"""
        cursor = self.conn.cursor()
        if key:
            cursor.execute("SELECT key, value, confidence FROM company_info WHERE key = ?", (key,))
            row = cursor.fetchone()
            return dict(row) if row else None
        else:
            cursor.execute("SELECT key, value, confidence FROM company_info")
            return {row['key']: {'value': row['value'], 'confidence': row['confidence']} for row in cursor.fetchall()}

    # ══════════════════════════════════════════════════════════════════════
    # Team Members Methods
    # ══════════════════════════════════════════════════════════════════════

    def store_team_member(self, name: str, email: str = None, role: str = None, department: str = None, metadata: Dict = None):
        """Store team member"""
        cursor = self.conn.cursor()
        metadata_json = json.dumps(metadata) if metadata else None

        if email:
            cursor.execute("""
                INSERT INTO team_members (name, email, role, department, metadata)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    name = excluded.name,
                    role = excluded.role,
                    department = excluded.department,
                    metadata = excluded.metadata,
                    updated_at = CURRENT_TIMESTAMP
            """, (name, email, role, department, metadata_json))
        else:
            cursor.execute("""
                INSERT INTO team_members (name, email, role, department, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (name, email, role, department, metadata_json))

        self.conn.commit()
        return cursor.lastrowid

    def get_team_members(self, department: str = None) -> List[Dict[str, Any]]:
        """Get team members"""
        cursor = self.conn.cursor()

        if department:
            cursor.execute("""
                SELECT id, name, email, role, department, metadata
                FROM team_members
                WHERE department = ?
            """, (department,))
        else:
            cursor.execute("""
                SELECT id, name, email, role, department, metadata
                FROM team_members
            """)

        members = []
        for row in cursor.fetchall():
            member = dict(row)
            if member['metadata']:
                member['metadata'] = json.loads(member['metadata'])
            members.append(member)

        return members

    # ══════════════════════════════════════════════════════════════════════
    # Preferences Methods
    # ══════════════════════════════════════════════════════════════════════

    def store_preference(self, category: str, key: str, value: str, confidence: float = 1.0):
        """Store user preference"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO preferences (category, key, value, confidence)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(category, key) DO UPDATE SET
                value = excluded.value,
                confidence = excluded.confidence,
                updated_at = CURRENT_TIMESTAMP
        """, (category, key, value, confidence))
        self.conn.commit()

    def get_preferences(self, category: str = None) -> Dict[str, Any]:
        """Get preferences"""
        cursor = self.conn.cursor()

        if category:
            cursor.execute("""
                SELECT key, value, confidence FROM preferences WHERE category = ?
            """, (category,))
        else:
            cursor.execute("SELECT category, key, value, confidence FROM preferences")

        if category:
            return {row['key']: {'value': row['value'], 'confidence': row['confidence']} for row in cursor.fetchall()}
        else:
            prefs = {}
            for row in cursor.fetchall():
                cat = row['category']
                if cat not in prefs:
                    prefs[cat] = {}
                prefs[cat][row['key']] = {'value': row['value'], 'confidence': row['confidence']}
            return prefs

    # ══════════════════════════════════════════════════════════════════════
    # Facts Methods
    # ══════════════════════════════════════════════════════════════════════

    def store_fact(self, category: str, fact: str, confidence: float = 0.8, source: str = None):
        """Store a fact"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO facts (category, fact, confidence, source)
            VALUES (?, ?, ?, ?)
        """, (category, fact, confidence, source))

        # Update FTS index
        fact_id = cursor.lastrowid
        cursor.execute("""
            INSERT INTO facts_fts (rowid, category, fact)
            VALUES (?, ?, ?)
        """, (fact_id, category, fact))

        self.conn.commit()
        return fact_id

    def search_facts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Full-text search for facts"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT f.id, f.category, f.fact, f.confidence, f.created_at
            FROM facts f
            JOIN facts_fts ON facts_fts.rowid = f.id
            WHERE facts_fts MATCH ?
            ORDER BY f.confidence DESC, f.created_at DESC
            LIMIT ?
        """, (query, limit))

        return [dict(row) for row in cursor.fetchall()]

    def get_facts_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all facts in a category"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, category, fact, confidence, created_at
            FROM facts
            WHERE category = ?
            ORDER BY confidence DESC, created_at DESC
        """, (category,))

        return [dict(row) for row in cursor.fetchall()]

    # ══════════════════════════════════════════════════════════════════════
    # Data Management
    # ══════════════════════════════════════════════════════════════════════

    def export_all_data(self) -> Dict[str, Any]:
        """
        Export all data for GDPR compliance.

        Returns all stored business knowledge in JSON format.
        """
        return {
            "company_info": self.get_company_info(),
            "team_members": self.get_team_members(),
            "preferences": self.get_preferences(),
            "facts": self._get_all_facts(),
            "export_timestamp": datetime.now().isoformat()
        }

    def _get_all_facts(self) -> List[Dict[str, Any]]:
        """Get all facts"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, category, fact, confidence, created_at FROM facts")
        return [dict(row) for row in cursor.fetchall()]

    def clear_all_data(self):
        """Clear all data (GDPR right to be forgotten)"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM company_info")
        cursor.execute("DELETE FROM team_members")
        cursor.execute("DELETE FROM projects")
        cursor.execute("DELETE FROM preferences")
        cursor.execute("DELETE FROM integrations")
        cursor.execute("DELETE FROM facts")
        cursor.execute("DELETE FROM facts_fts")
        cursor.execute("DELETE FROM relationships")
        self.conn.commit()

    def close(self):
        """Close database connection"""
        self.conn.close()


__all__ = ["MemoryDatabase"]
