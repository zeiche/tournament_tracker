#!/usr/bin/env python3
"""
conversation_manager.py - Manages Claude conversations with context

This utility:
- Maintains conversation history
- Builds dynamic context from Bonjour
- Manages conversation state
- Handles context windowing
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import json


@dataclass
class ConversationTurn:
    """A single turn in a conversation"""
    timestamp: datetime
    role: str  # 'user' or 'assistant'
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    services_used: List[str] = field(default_factory=list)


@dataclass
class ConversationContext:
    """Context for a conversation"""
    conversation_id: str
    started_at: datetime
    turns: List[ConversationTurn] = field(default_factory=list)
    discovered_services: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    
    def add_turn(self, role: str, content: str, **kwargs):
        """Add a turn to the conversation"""
        turn = ConversationTurn(
            timestamp=datetime.now(),
            role=role,
            content=content,
            **kwargs
        )
        self.turns.append(turn)
        return turn
    
    def get_recent_turns(self, limit: int = 10) -> List[ConversationTurn]:
        """Get recent conversation turns"""
        return self.turns[-limit:] if self.turns else []
    
    def to_messages(self) -> List[Dict[str, str]]:
        """Convert to Claude API message format"""
        return [
            {"role": turn.role, "content": turn.content}
            for turn in self.turns
        ]


class ConversationManager:
    """
    Manages multiple conversations with context and history.
    Integrates with Bonjour for dynamic service awareness.
    """
    
    def __init__(self, max_history: int = 100, max_context_turns: int = 20):
        self.conversations: Dict[str, ConversationContext] = {}
        self.max_history = max_history
        self.max_context_turns = max_context_turns
        self.global_history = deque(maxlen=max_history)
        
    def start_conversation(self, conversation_id: str) -> ConversationContext:
        """Start a new conversation"""
        context = ConversationContext(
            conversation_id=conversation_id,
            started_at=datetime.now()
        )
        self.conversations[conversation_id] = context
        return context
    
    def get_or_create_conversation(self, conversation_id: str) -> ConversationContext:
        """Get existing conversation or create new one"""
        if conversation_id not in self.conversations:
            return self.start_conversation(conversation_id)
        return self.conversations[conversation_id]
    
    def add_interaction(
        self,
        conversation_id: str,
        user_message: str,
        assistant_response: str,
        services_used: Optional[List[str]] = None
    ):
        """Add a complete interaction to a conversation"""
        context = self.get_or_create_conversation(conversation_id)
        
        # Add user turn
        context.add_turn("user", user_message)
        
        # Add assistant turn
        context.add_turn(
            "assistant",
            assistant_response,
            services_used=services_used or []
        )
        
        # Add to global history
        self.global_history.append({
            'conversation_id': conversation_id,
            'timestamp': datetime.now(),
            'user': user_message,
            'assistant': assistant_response
        })
    
    def get_context_for_claude(
        self,
        conversation_id: str,
        include_service_info: bool = True
    ) -> Dict[str, Any]:
        """
        Build context for Claude including conversation history.
        
        Returns:
            Dict with 'messages' and 'context' keys
        """
        context = self.get_or_create_conversation(conversation_id)
        
        # Get recent turns for context
        recent_turns = context.get_recent_turns(self.max_context_turns)
        
        # Build context dict
        claude_context = {
            'messages': [
                {"role": turn.role, "content": turn.content}
                for turn in recent_turns
            ],
            'conversation_metadata': {
                'conversation_id': conversation_id,
                'started_at': context.started_at.isoformat(),
                'turn_count': len(context.turns)
            }
        }
        
        # Add service information if requested
        if include_service_info and context.discovered_services:
            claude_context['discovered_services'] = context.discovered_services
        
        return claude_context
    
    def find_similar_conversations(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find conversations similar to a query.
        Useful for finding relevant context from past conversations.
        """
        similar = []
        query_lower = query.lower()
        
        for conv_id, context in self.conversations.items():
            # Simple keyword matching (could be enhanced with embeddings)
            relevance_score = 0
            
            for turn in context.turns:
                if query_lower in turn.content.lower():
                    relevance_score += 1
            
            if relevance_score > 0:
                similar.append({
                    'conversation_id': conv_id,
                    'relevance_score': relevance_score,
                    'started_at': context.started_at,
                    'turns': len(context.turns)
                })
        
        # Sort by relevance and return top results
        similar.sort(key=lambda x: x['relevance_score'], reverse=True)
        return similar[:limit]
    
    def export_conversation(self, conversation_id: str) -> str:
        """Export a conversation as JSON"""
        if conversation_id not in self.conversations:
            return json.dumps({"error": "Conversation not found"})
        
        context = self.conversations[conversation_id]
        
        export_data = {
            'conversation_id': conversation_id,
            'started_at': context.started_at.isoformat(),
            'turns': [
                {
                    'timestamp': turn.timestamp.isoformat(),
                    'role': turn.role,
                    'content': turn.content,
                    'services_used': turn.services_used
                }
                for turn in context.turns
            ]
        }
        
        return json.dumps(export_data, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        total_turns = sum(len(c.turns) for c in self.conversations.values())
        
        return {
            'total_conversations': len(self.conversations),
            'total_turns': total_turns,
            'average_turns_per_conversation': total_turns / len(self.conversations) if self.conversations else 0,
            'global_history_size': len(self.global_history),
            'active_conversations': [
                {
                    'id': conv_id,
                    'turns': len(context.turns),
                    'started': context.started_at.isoformat()
                }
                for conv_id, context in self.conversations.items()
            ]
        }


# Global conversation manager
conversation_manager = ConversationManager()


if __name__ == "__main__":
    # Test the conversation manager
    print("Testing Conversation Manager")
    print("=" * 50)
    
    # Start a conversation
    manager = ConversationManager()
    
    # Simulate Discord conversation
    discord_conv = manager.get_or_create_conversation("discord_channel_123")
    
    # Add some interactions
    manager.add_interaction(
        "discord_channel_123",
        "What tournaments are happening?",
        "I found 3 upcoming tournaments...",
        services_used=["Database Service", "Start.gg Sync"]
    )
    
    manager.add_interaction(
        "discord_channel_123",
        "Show me the top players",
        "Here are the top 10 players...",
        services_used=["Database Service"]
    )
    
    # Get context for Claude
    context = manager.get_context_for_claude("discord_channel_123")
    print(f"Context messages: {len(context['messages'])}")
    
    # Show statistics
    stats = manager.get_statistics()
    print(f"\nStatistics: {json.dumps(stats, indent=2)}")
    
    # Export conversation
    export = manager.export_conversation("discord_channel_123")
    print(f"\nExported conversation:\n{export}")