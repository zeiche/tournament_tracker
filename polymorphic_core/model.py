#!/usr/bin/env python3
"""
polymorphic_model.py - TRUE OOP with just THREE methods
This is the ultimate simplification - objects that understand intent.
"""
from typing import Any, Optional, Dict, List, Union
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from capability_announcer import announcer
import re
import json


class PolymorphicModel:
    """
    The TRUE OOP base - just THREE methods that do EVERYTHING.
    
    Instead of 200+ specific methods, we have:
    - ask(): Query anything about the object
    - tell(): Explain/format the object  
    - do(): Perform any action
    
    These methods are POLYMORPHIC - they figure out what you want.
    """
    
    def ask(self, question: Any, session: Optional[Session] = None) -> Any:
        """
        Ask the object ANYTHING. It figures out what you want.
        
        Examples:
            tournament.ask("winner")           # Returns the winner
            tournament.ask("top 8")            # Returns top 8 placements
            player.ask("win rate")             # Returns win percentage
            player.ask("recent tournaments")   # Returns recent events
            org.ask("total attendance")        # Returns sum of all attendance
        """
        # Announce what we're being asked
        local_announcer.announce(
            f"{self.__class__.__name__}.ask",
            [f"Being asked: {question}"]
        )
        
        # Convert question to string for analysis
        q = str(question).lower()
        
        # Route to appropriate internal method based on question
        # This is where polymorphism happens - we interpret intent
        
        # First, check if it's asking for a property
        for attr in dir(self):
            if not attr.startswith('_'):
                # Check if the attribute name is in the question
                if attr.replace('_', ' ') in q:
                    value = getattr(self, attr, None)
                    if not callable(value):
                        return value
        
        # Check for common patterns
        if any(word in q for word in ['winner', 'first', 'champion']):
            return self._ask_winner(session)
        
        if any(word in q for word in ['top', 'placement', 'standing']):
            # Extract number if present
            import re
            match = re.search(r'\d+', q)
            n = int(match.group()) if match else 8
            return self._ask_top_n(n, session)
        
        if any(word in q for word in ['attendance', 'attendees', 'players']):
            return self._ask_attendance()
        
        if any(word in q for word in ['recent', 'latest', 'last']):
            return self._ask_recent(session)
        
        if any(word in q for word in ['stat', 'metric', 'analytic']):
            return self._ask_statistics()
        
        if any(word in q for word in ['capability', 'can you', 'what can']):
            return self._ask_capabilities()
        
        # If we don't understand, explain ourselves
        return self.tell("help")
    
    def tell(self, format: str = "default", **kwargs) -> Union[str, Dict]:
        """
        Tell about yourself in any format.
        
        Examples:
            tournament.tell()                  # Default explanation
            tournament.tell("discord")         # Format for Discord
            tournament.tell("claude")          # Explain to Claude
            tournament.tell("json")            # Return as JSON
            player.tell("stats")               # Show statistics
            player.tell("brief")               # Quick summary
        """
        # Announce what format is requested
        local_announcer.announce(
            f"{self.__class__.__name__}.tell",
            [f"Format requested: {format}"]
        )
        
        fmt = format.lower()
        
        # Route to appropriate formatter
        if fmt in ["discord", "chat"]:
            return self._tell_discord()
        
        if fmt in ["claude", "ai"]:
            return self._tell_claude()
        
        if fmt in ["json", "data"]:
            return self._tell_json()
        
        if fmt in ["help", "capabilities"]:
            return self._tell_help()
        
        if fmt in ["stats", "statistics"]:
            return self._tell_statistics()
        
        if fmt in ["brief", "summary", "short"]:
            return self._tell_brief()
        
        # Default: comprehensive explanation
        return self._tell_default()
    
    def do(self, action: Any, session: Optional[Session] = None, **kwargs) -> Any:
        """
        Do ANYTHING that needs doing. Polymorphic action handler.
        
        Examples:
            tournament.do("sync")              # Sync from API
            tournament.do("calculate stats")   # Calculate all statistics
            player.do("update")                # Update player info
            player.do("merge", other_player)   # Merge with another player
            org.do("add contact", email="...")  # Add contact info
        """
        # Announce what we're being asked to do
        local_announcer.announce(
            f"{self.__class__.__name__}.do",
            [f"Action requested: {action}"]
        )
        
        act = str(action).lower()
        
        # Route to appropriate action
        if any(word in act for word in ['sync', 'refresh', 'update']):
            return self._do_sync(session, **kwargs)
        
        if any(word in act for word in ['calculate', 'compute', 'analyze']):
            return self._do_calculate(**kwargs)
        
        if any(word in act for word in ['save', 'persist', 'commit']):
            return self._do_save(session)
        
        if any(word in act for word in ['delete', 'remove']):
            return self._do_delete(session)
        
        if any(word in act for word in ['merge', 'combine']):
            return self._do_merge(session, **kwargs)
        
        if any(word in act for word in ['announce', 'broadcast']):
            return self._do_announce()
        
        if any(word in act for word in ['validate', 'check']):
            return self._do_validate()
        
        # Default: explain what actions are available
        return self._do_help()
    
    # =========================================================================
    # Internal methods - these do the actual work
    # Subclasses override these for specific behavior
    # =========================================================================
    
    def _ask_winner(self, session: Optional[Session]) -> Any:
        """Override in subclass to return winner/first place"""
        return None
    
    def _ask_top_n(self, n: int, session: Optional[Session]) -> List:
        """Override in subclass to return top N results"""
        return []
    
    def _ask_attendance(self) -> Any:
        """Override in subclass to return attendance info"""
        return getattr(self, 'num_attendees', None)
    
    def _ask_recent(self, session: Optional[Session]) -> List:
        """Override in subclass to return recent items"""
        return []
    
    def _ask_statistics(self) -> Dict:
        """Override in subclass to return statistics"""
        stats = {}
        for attr in dir(self):
            if not attr.startswith('_') and not callable(getattr(self, attr, None)):
                stats[attr] = getattr(self, attr, None)
        return stats
    
    def _ask_capabilities(self) -> List[str]:
        """Return what this object can do"""
        return [
            f"ask('{example}')" for example in [
                "winner", "top 8", "attendance", "recent", "statistics"
            ]
        ] + [
            f"tell('{format}')" for format in [
                "discord", "claude", "json", "stats", "brief"
            ]
        ] + [
            f"do('{action}')" for action in [
                "sync", "calculate", "save", "announce"
            ]
        ]
    
    def _tell_discord(self) -> str:
        """Format for Discord - override in subclass"""
        return f"**{self.__class__.__name__}** #{getattr(self, 'id', '?')}"
    
    def _tell_claude(self) -> Dict:
        """Explain to Claude - override in subclass"""
        return {
            'type': self.__class__.__name__,
            'id': getattr(self, 'id', None),
            'capabilities': self._ask_capabilities(),
            'data': self._ask_statistics()
        }
    
    def _tell_json(self) -> str:
        """Return as JSON"""
        data = {}
        for attr in dir(self):
            if not attr.startswith('_'):
                value = getattr(self, attr, None)
                if not callable(value):
                    try:
                        json.dumps(value)  # Test if serializable
                        data[attr] = value
                    except:
                        data[attr] = str(value)
        return json.dumps(data, indent=2, default=str)
    
    def _tell_help(self) -> str:
        """Return help/capabilities"""
        return f"""
{self.__class__.__name__} Object - Polymorphic Interface

You can:
  - ask("anything") - Query any aspect
  - tell("format") - Get formatted output
  - do("action") - Perform any action

Examples:
  - ask("winner") - Get the winner
  - ask("top 8") - Get top 8
  - tell("discord") - Format for Discord
  - tell("claude") - Explain to Claude
  - do("sync") - Sync data
  - do("calculate") - Calculate stats
"""
    
    def _tell_statistics(self) -> str:
        """Return statistics - override in subclass"""
        stats = self._ask_statistics()
        return "\n".join(f"{k}: {v}" for k, v in stats.items() if v is not None)
    
    def _tell_brief(self) -> str:
        """Brief summary - override in subclass"""
        return f"{self.__class__.__name__} #{getattr(self, 'id', '?')}"
    
    def _tell_default(self) -> str:
        """Default comprehensive explanation"""
        return self._tell_statistics()
    
    def _do_sync(self, session: Optional[Session], **kwargs) -> bool:
        """Sync/update - override in subclass"""
        return True
    
    def _do_calculate(self, **kwargs) -> Dict:
        """Calculate statistics - override in subclass"""
        return self._ask_statistics()
    
    def _do_save(self, session: Optional[Session]) -> bool:
        """Save to database - override in subclass"""
        if session:
            session.add(self)
            return True
        return False
    
    def _do_delete(self, session: Optional[Session]) -> bool:
        """Delete from database - override in subclass"""
        if session:
            session.delete(self)
            return True
        return False
    
    def _do_merge(self, session: Optional[Session], **kwargs) -> bool:
        """Merge with another object - override in subclass"""
        return False
    
    def _do_announce(self) -> bool:
        """Announce capabilities"""
        local_announcer.announce(
            f"{self.__class__.__name__} Instance",
            self._ask_capabilities(),
            [f"Object #{getattr(self, 'id', '?')} ready"]
        )
        return True
    
    def _do_validate(self) -> Dict:
        """Validate the object - override in subclass"""
        return {'valid': True, 'errors': []}
    
    def _do_help(self) -> str:
        """Return available actions"""
        return """
Available actions:
  - do("sync") - Synchronize data
  - do("calculate") - Calculate statistics
  - do("save") - Save to database
  - do("delete") - Delete from database
  - do("merge", other=...) - Merge with another
  - do("announce") - Announce capabilities
  - do("validate") - Validate data
"""


# This is it! Just THREE methods that handle EVERYTHING polymorphically!