"""
Memory management system for AI agents.

Provides different types of memory storage:
1. Short-term memory (recent conversations)
2. Long-term memory (persistent knowledge)
3. Working memory (current context)
"""

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

class MemoryStore:
    """Memory management system for AI agents"""
    
    def __init__(self, agent_id: str, db_path: str = "memory/agent_memory.db"):
        self.agent_id = agent_id
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize memory storage
        self.short_term: List[MemoryEntry] = []  # Recent memories (last N interactions)
        self.working_memory: Dict[str, Any] = {}  # Current context
        self._init_database()
        
    def _init_database(self):
        """Initialize the SQLite database for long-term memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS long_term_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                content TEXT,
                memory_type TEXT,
                timestamp REAL,
                importance REAL,
                metadata TEXT,
                embedding TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_associations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INTEGER,
                associated_memory_id INTEGER,
                association_type TEXT,
                strength REAL,
                FOREIGN KEY (memory_id) REFERENCES long_term_memory(id),
                FOREIGN KEY (associated_memory_id) REFERENCES long_term_memory(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    async def add_memory(self, content: str, memory_type: str, metadata: Dict[str, Any], 
                        importance: float = 0.0) -> None:
        """Add a new memory entry"""
        timestamp = time.time()
        entry = MemoryEntry(content, timestamp, memory_type, metadata, importance)
        
        # Add to short-term memory
        if memory_type == "conversation":
            self.short_term.append(entry)
            # Keep only last 10 conversations in short-term
            if len(self.short_term) > 10:
                self._consolidate_memory()
                
        # Add to long-term memory if important enough
        if importance > 0.3:
            self._store_long_term(entry)
            
    def _consolidate_memory(self):
        """Consolidate short-term memories into long-term storage"""
        if not self.short_term:
            return
            
        # Analyze short-term memories for patterns and importance
        consolidated = self._analyze_short_term()
        
        # Store important consolidated memories
        if consolidated.importance > 0.3:
            self._store_long_term(consolidated)
            
        # Clear old short-term memories
        self.short_term = self.short_term[-5:]  # Keep only last 5 interactions
        
    def _analyze_short_term(self) -> MemoryEntry:
        """Analyze short-term memories to create consolidated memory"""
        # Combine recent interactions into a summary
        conversations = [m.content for m in self.short_term]
        summary = "\n".join(conversations[-5:])  # Last 5 conversations
        
        # Calculate importance based on interaction patterns
        importance = min(len(self.short_term) * 0.1, 0.8)  # More interactions = more important
        
        return MemoryEntry(
            content=summary,
            timestamp=time.time(),
            memory_type="consolidated",
            metadata={"source": "short_term_consolidation"},
            importance=importance
        )
        
    def _store_long_term(self, entry: MemoryEntry):
        """Store a memory in long-term storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO long_term_memory 
            (agent_id, content, memory_type, timestamp, importance, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            self.agent_id,
            entry.content,
            entry.memory_type,
            entry.timestamp,
            entry.importance,
            json.dumps(entry.metadata)
        ))
        
        conn.commit()
        conn.close()
        
    async def get_relevant_memories(self, context: str, limit: int = 5) -> List[MemoryEntry]:
        """Retrieve memories relevant to the current context"""
        # First, check short-term memory
        relevant_short = [
            m for m in self.short_term 
            if self._calculate_relevance(m.content, context) > 0.5
        ]
        
        # Then, check long-term memory
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent and important memories
        cursor.execute('''
            SELECT content, timestamp, memory_type, importance, metadata
            FROM long_term_memory
            WHERE agent_id = ?
            ORDER BY importance DESC, timestamp DESC
            LIMIT ?
        ''', (self.agent_id, limit))
        
        long_term = [
            MemoryEntry(
                content=row[0],
                timestamp=row[1],
                memory_type=row[2],
                importance=row[3],
                metadata=json.loads(row[4])
            )
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        # Combine and sort by relevance
        all_memories = relevant_short + long_term
        all_memories.sort(
            key=lambda x: (
                self._calculate_relevance(x.content, context),
                x.importance
            ),
            reverse=True
        )
        
        return all_memories[:limit]
        
    def _calculate_relevance(self, memory: str, context: str) -> float:
        """Calculate relevance score between memory and context"""
        # Simple word overlap for now - can be enhanced with embeddings
        memory_words = set(memory.lower().split())
        context_words = set(context.lower().split())
        overlap = len(memory_words.intersection(context_words))
        return overlap / max(len(memory_words), len(context_words))
        
    def update_working_memory(self, key: str, value: Any):
        """Update working memory with new information"""
        self.working_memory[key] = {
            'value': value,
            'timestamp': time.time()
        }
        
    def get_working_memory(self, key: str) -> Optional[Any]:
        """Get value from working memory"""
        if key in self.working_memory:
            return self.working_memory[key]['value']
        return None
        
    def clear_working_memory(self):
        """Clear working memory"""
        self.working_memory = {}
