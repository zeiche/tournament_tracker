#!/usr/bin/env python3
"""
polymorphic_storage.py - Polymorphic storage service that accepts ANY data
Announces via Bonjour, stores objects/files/data polymorphically
Has its own database table, uses existing database functions
"""

from capability_announcer import announcer
from capability_discovery import register_capability
from database import get_session, Base
from sqlalchemy import Column, Integer, String, Text, LargeBinary, DateTime
from sqlalchemy.sql import func
from datetime import datetime
import os
import json
import tempfile
from typing import Any, Optional, Dict

class StorageContent(Base):
    """Storage table - ONLY table this service can access"""
    __tablename__ = 'storage_content'
    
    id = Column(Integer, primary_key=True)
    content_type = Column(String(50))  # 'audio', 'text', 'json', 'binary', etc.
    source = Column(String(100))  # Who stored it (e.g., 'discord_voice')
    content_metadata = Column(Text)  # JSON metadata about the content
    file_path = Column(String(500))  # Path if stored as file
    content_blob = Column(LargeBinary)  # Small content stored directly
    created_at = Column(DateTime, server_default=func.now())
    
    def tell(self, format: str = "brief") -> str:
        """Polymorphic tell method"""
        if format == "brief":
            return f"Storage #{self.id}: {self.content_type} from {self.source}"
        elif format == "full":
            meta = json.loads(self.content_metadata) if self.content_metadata else {}
            return f"Storage #{self.id}\nType: {self.content_type}\nSource: {self.source}\nMetadata: {meta}\nStored: {self.created_at}"
        return str(self)
    
    def ask(self, question: str) -> Any:
        """Polymorphic ask method"""
        if "path" in question.lower():
            return self.file_path
        elif "type" in question.lower():
            return self.content_type
        elif "when" in question.lower():
            return self.created_at
        elif "metadata" in question.lower():
            return json.loads(self.content_metadata) if self.content_metadata else {}
        return None
    
    def do(self, action: str) -> Any:
        """Polymorphic do method"""
        if action == "delete":
            if self.file_path and os.path.exists(self.file_path):
                os.remove(self.file_path)
            return True
        elif action == "read":
            if self.file_path and os.path.exists(self.file_path):
                with open(self.file_path, 'rb') as f:
                    return f.read()
            return self.content_blob
        return None

class PolymorphicStorage:
    """Storage service that accepts ANY type of data polymorphically"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Announce capabilities
        announcer.announce(
            "PolymorphicStorage",
            [
                "I store ANY type of content polymorphically",
                "I accept audio, text, binary, JSON, anything",
                "I announce when content is stored",
                "I provide storage IDs for retrieval",
                "I use my own database table",
                "Methods: store(content, type, source, metadata)",
                "I figure out how to store based on content type"
            ]
        )
        
        # Create storage directory
        self.storage_dir = "/home/ubuntu/claude/tournament_tracker/storage"
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Create table if needed
        self._ensure_table()
    
    def _ensure_table(self):
        """Ensure our storage table exists"""
        from database import engine
        Base.metadata.create_all(bind=engine, tables=[StorageContent.__table__])
        announcer.announce("PolymorphicStorage", ["Storage table ready"])
    
    def store(self, content: Any, content_type: str = None, source: str = None, metadata: Dict = None) -> int:
        """
        Store ANY content polymorphically
        Returns storage ID for retrieval
        """
        # Figure out content type if not provided
        if not content_type:
            if isinstance(content, bytes):
                content_type = "binary"
            elif isinstance(content, str):
                content_type = "text"
            elif isinstance(content, dict):
                content_type = "json"
            else:
                content_type = "unknown"
        
        # Announce storage event
        announcer.announce(
            "STORAGE_EVENT",
            [
                f"STORING: {content_type}",
                f"SOURCE: {source or 'unknown'}",
                f"SIZE: {len(content) if hasattr(content, '__len__') else 'unknown'}"
            ]
        )
        
        with get_session() as session:
            storage = StorageContent()
            storage.content_type = content_type
            storage.source = source or "unknown"
            storage.content_metadata = json.dumps(metadata) if metadata else None
            
            # Decide how to store based on size and type
            if isinstance(content, bytes) and len(content) > 10000:
                # Large binary - store as file
                file_path = os.path.join(
                    self.storage_dir,
                    f"{content_type}_{datetime.now().timestamp()}.dat"
                )
                with open(file_path, 'wb') as f:
                    f.write(content)
                storage.file_path = file_path
                
                announcer.announce(
                    "STORAGE_FILE",
                    [f"Stored as file: {file_path}"]
                )
            elif isinstance(content, str) and len(content) > 10000:
                # Large text - store as file
                file_path = os.path.join(
                    self.storage_dir,
                    f"{content_type}_{datetime.now().timestamp()}.txt"
                )
                with open(file_path, 'w') as f:
                    f.write(content)
                storage.file_path = file_path
            else:
                # Small content - store in database
                if isinstance(content, str):
                    storage.content_blob = content.encode()
                elif isinstance(content, dict):
                    storage.content_blob = json.dumps(content).encode()
                elif isinstance(content, bytes):
                    storage.content_blob = content
                else:
                    storage.content_blob = str(content).encode()
            
            session.add(storage)
            session.commit()
            storage_id = storage.id
            
            announcer.announce(
                "STORAGE_COMPLETE",
                [
                    f"STORED_ID: {storage_id}",
                    f"TYPE: {content_type}",
                    f"RETRIEVAL: storage.retrieve({storage_id})"
                ]
            )
            
            return storage_id
    
    def retrieve(self, storage_id: int) -> Optional[Any]:
        """Retrieve stored content by ID"""
        with get_session() as session:
            storage = session.query(StorageContent).filter_by(id=storage_id).first()
            if storage:
                return storage.do("read")
        return None
    
    def list_recent(self, limit: int = 10) -> list:
        """List recent stored items"""
        with get_session() as session:
            items = session.query(StorageContent)\
                          .order_by(StorageContent.created_at.desc())\
                          .limit(limit)\
                          .all()
            return [item.tell("brief") for item in items]
    
    def accept_audio(self, audio_data: bytes, user_id: int, guild_id: int) -> int:
        """Special method for audio storage"""
        metadata = {
            "user_id": user_id,
            "guild_id": guild_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store as WAV file
        file_path = os.path.join(
            self.storage_dir,
            f"voice_{user_id}_{datetime.now().timestamp()}.wav"
        )
        
        with open(file_path, 'wb') as f:
            f.write(audio_data)
        
        # Store reference in database
        storage_id = self.store(
            audio_data,
            content_type="audio/wav",
            source=f"discord_voice_{user_id}",
            metadata=metadata
        )
        
        announcer.announce(
            "AUDIO_STORED",
            [
                f"Audio from user {user_id} stored",
                f"Storage ID: {storage_id}",
                f"File: {file_path}"
            ]
        )
        
        return storage_id

# Global instance
_storage_instance = PolymorphicStorage()

def get_storage():
    """Get the global storage instance"""
    return _storage_instance

# Register with capability discovery
try:
    register_capability("storage", get_storage)
    announcer.announce("PolymorphicStorage", ["Registered as discoverable capability"])
except ImportError:
    pass

# Listen for storage requests via announcements
def listen_for_storage_requests():
    """This would listen for STORE_REQUEST announcements"""
    # In a real implementation, this would subscribe to announcements
    pass