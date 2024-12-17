"""Base memory management system for AI agents."""

from typing import Dict, List, Any, Optional
import json
import time
from datetime import datetime
import sqlite3
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    """A single memory entry"""
    content: str
    timestamp: float
    memory_type: str
    metadata: Dict[str, Any]
    importance: float = 0.0

class BaseMemoryStore:
    """Base memory management system for AI agents"""
    
    def __init__(self, agent_name: str):
        """Initialize memory store for a specific agent"""
        self.agent_name = agent_name
        self.memory_dir = Path(__file__).parent / agent_name / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.memory_dir / f"{agent_name}_memory.db"
        self._init_db()
        
    def _init_db(self):
        """Initialize SQLite database for storing memories"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    memory_type TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    importance REAL DEFAULT 0.0
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_type ON memories(memory_type)')
    
    def add_memory(self, content: str, memory_type: str, metadata: Dict[str, Any] = None, importance: float = 0.0) -> bool:
        """Add a new memory entry"""
        try:
            if metadata is None:
                metadata = {}
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    'INSERT INTO memories (content, timestamp, memory_type, metadata, importance) VALUES (?, ?, ?, ?, ?)',
                    (content, time.time(), memory_type, json.dumps(metadata), importance)
                )
                return True
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            return False
    
    def get_recent_memories(self, memory_type: Optional[str] = None, limit: int = 10) -> List[MemoryEntry]:
        """Retrieve recent memories, optionally filtered by type"""
        query = 'SELECT * FROM memories'
        params = []
        
        if memory_type:
            query += ' WHERE memory_type = ?'
            params.append(memory_type)
            
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
        return [
            MemoryEntry(
                content=row[1],
                timestamp=row[2],
                memory_type=row[3],
                metadata=json.loads(row[4]),
                importance=row[5]
            )
            for row in rows
        ]
    
    def search_memories(self, query: str, memory_type: Optional[str] = None) -> List[MemoryEntry]:
        """Search memories by content"""
        sql_query = 'SELECT * FROM memories WHERE content LIKE ?'
        params = [f'%{query}%']
        
        if memory_type:
            sql_query += ' AND memory_type = ?'
            params.append(memory_type)
            
        sql_query += ' ORDER BY timestamp DESC'
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(sql_query, params)
            rows = cursor.fetchall()
            
        return [
            MemoryEntry(
                content=row[1],
                timestamp=row[2],
                memory_type=row[3],
                metadata=json.loads(row[4]),
                importance=row[5]
            )
            for row in rows
        ]
    
    def clear_memories(self, memory_type: Optional[str] = None):
        """Clear all memories or memories of a specific type"""
        query = 'DELETE FROM memories'
        params = []
        
        if memory_type:
            query += ' WHERE memory_type = ?'
            params.append(memory_type)
            
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(query, params)
