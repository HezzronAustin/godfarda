"""Communications Agent specific memory implementation"""

from src.agents.memory_base import BaseMemoryStore, MemoryEntry
from typing import Dict, List, Any, Optional
import json

class CommunicationsMemory(BaseMemoryStore):
    """Memory store specific to Communications Agent with platform-specific capabilities"""
    
    def __init__(self):
        super().__init__("communications")
        
    def store_conversation(self, platform: str, user_id: str, message: str, response: str, metadata: Dict[str, Any] = None):
        """Store a conversation interaction from a specific platform"""
        self.add_memory(
            content=f"User: {message}\nResponse: {response}",
            memory_type="conversation",
            metadata={
                "platform": platform,
                "user_id": user_id,
                **(metadata or {})
            },
            importance=1.0
        )
    
    def get_user_history(self, platform: str, user_id: str, limit: int = 10) -> List[MemoryEntry]:
        """Get conversation history for a specific user on a platform"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                '''
                SELECT * FROM memories 
                WHERE memory_type = 'conversation'
                AND json_extract(metadata, '$.platform') = ?
                AND json_extract(metadata, '$.user_id') = ?
                ORDER BY timestamp DESC LIMIT ?
                ''',
                (platform, user_id, limit)
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
    
    def get_platform_stats(self, platform: str) -> Dict[str, Any]:
        """Get usage statistics for a specific platform"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                '''
                SELECT 
                    COUNT(*) as total_messages,
                    COUNT(DISTINCT json_extract(metadata, '$.user_id')) as unique_users,
                    MIN(timestamp) as first_message,
                    MAX(timestamp) as last_message
                FROM memories 
                WHERE memory_type = 'conversation'
                AND json_extract(metadata, '$.platform') = ?
                ''',
                (platform,)
            )
            stats = cursor.fetchone()
            
        return {
            "total_messages": stats[0],
            "unique_users": stats[1],
            "first_message_timestamp": stats[2],
            "last_message_timestamp": stats[3]
        }
