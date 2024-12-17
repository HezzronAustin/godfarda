"""GodFarda specific memory implementation"""

from src.agents.memory_base import BaseMemoryStore, MemoryEntry
from typing import Dict, List, Any, Optional
import json

class GodFardaMemory(BaseMemoryStore):
    """Memory store specific to GodFarda with additional capabilities"""
    
    def __init__(self):
        super().__init__("godfarda")
        
    def remember_agent_interaction(self, agent_name: str, interaction: str, metadata: Dict[str, Any] = None):
        """Store memory of interaction with a specific agent"""
        self.add_memory(
            content=interaction,
            memory_type="agent_interaction",
            metadata={"agent": agent_name, **(metadata or {})},
            importance=1.0  # Agent interactions are important
        )
    
    def get_agent_history(self, agent_name: str, limit: int = 10) -> List[MemoryEntry]:
        """Get history of interactions with a specific agent"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                '''
                SELECT * FROM memories 
                WHERE memory_type = 'agent_interaction'
                AND json_extract(metadata, '$.agent') = ?
                ORDER BY timestamp DESC LIMIT ?
                ''',
                (agent_name, limit)
            )
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

    def get_relevant_memories(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """Get memories relevant to the current query"""
        with self._get_connection() as conn:
            # For now, just get recent memories
            cursor = conn.execute(
                '''
                SELECT * FROM memories 
                WHERE memory_type = 'conversation'
                ORDER BY timestamp DESC LIMIT ?
                ''',
                (limit,)
            )
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
