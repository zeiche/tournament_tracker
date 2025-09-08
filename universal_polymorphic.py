#!/usr/bin/env python3
"""
universal_polymorphic.py - Universal Polymorphic Base for ALL Classes

This is the ULTIMATE simplification. Every class in the system inherits from this
and gets the 3-method pattern: ask(), tell(), do()

No more 200+ methods. Just THREE that understand intent.
"""

from typing import Any, Optional, Dict, List, Union
import json
import re
import sys
sys.path.insert(0, 'utils')
from capability_announcer import announcer


class UniversalPolymorphic:
    """
    The universal base for TRUE OOP - just THREE methods.
    
    EVERY class in the system should inherit from this:
    - Services
    - Models  
    - Bridges
    - Handlers
    - Managers
    - Everything!
    """
    
    def __init__(self):
        """Initialize and announce ourselves"""
        # Announce that we exist
        self._announce_existence()
    
    def ask(self, question: Any, **kwargs) -> Any:
        """
        Ask ANYTHING. The object figures out what you want.
        
        Examples:
            service.ask("status")              # Service status
            service.ask("capabilities")        # What can you do
            model.ask("data")                 # Get data
            bridge.ask("connected")           # Connection status
            manager.ask("services")           # List services
        """
        # Convert to string for analysis
        q = str(question).lower()
        
        # Check for property access first
        if hasattr(self, q.replace(' ', '_')):
            attr = getattr(self, q.replace(' ', '_'))
            if not callable(attr):
                return attr
        
        # Common patterns ALL objects understand
        if any(word in q for word in ['status', 'state', 'health']):
            return self._get_status()
        
        if any(word in q for word in ['capability', 'capabilities', 'can', 'able']):
            return self._get_capabilities()
        
        if any(word in q for word in ['help', 'usage', 'how']):
            return self._get_help()
        
        if any(word in q for word in ['config', 'configuration', 'settings']):
            return self._get_config()
        
        if any(word in q for word in ['info', 'information', 'about']):
            return self._get_info()
        
        # Let subclass handle specific questions
        return self._handle_ask(question, **kwargs)
    
    def tell(self, format: str = "default", **kwargs) -> Union[str, Dict]:
        """
        Tell about yourself in any format.
        
        Examples:
            obj.tell()                    # Default format
            obj.tell("json")             # JSON output
            obj.tell("discord")          # Discord formatting
            obj.tell("claude")           # Claude-friendly
            obj.tell("human")            # Human readable
            obj.tell("brief")            # Short summary
        """
        fmt = format.lower()
        
        # Universal formats ALL objects support
        if fmt in ['json', 'data']:
            return self._to_json()
        
        if fmt in ['dict', 'dictionary']:
            return self._to_dict()
        
        if fmt in ['string', 'str', 'text']:
            return str(self)
        
        if fmt in ['brief', 'summary', 'short']:
            return self._brief_summary()
        
        if fmt in ['detailed', 'verbose', 'full']:
            return self._detailed_summary()
        
        if fmt in ['discord', 'chat']:
            return self._format_discord()
        
        if fmt in ['claude', 'ai']:
            return self._format_claude()
        
        if fmt in ['help', 'usage']:
            return self._get_help()
        
        # Let subclass handle specific formats
        return self._handle_tell(format, **kwargs)
    
    def do(self, action: Any, **kwargs) -> Any:
        """
        Do ANY action. Polymorphic action handler.
        
        Examples:
            service.do("start")              # Start service
            service.do("stop")               # Stop service
            model.do("save")                 # Save to database
            bridge.do("connect")             # Connect bridge
            manager.do("restart all")        # Restart everything
        """
        act = str(action).lower()
        
        # Universal actions ALL objects support
        if any(word in act for word in ['announce', 'broadcast']):
            return self._announce_existence()
        
        if any(word in act for word in ['refresh', 'reload']):
            return self._refresh()
        
        if any(word in act for word in ['reset', 'clear']):
            return self._reset()
        
        if any(word in act for word in ['validate', 'check']):
            return self._validate()
        
        if any(word in act for word in ['test', 'ping']):
            return self._test()
        
        # Let subclass handle specific actions
        return self._handle_do(action, **kwargs)
    
    # =========================================================================
    # Protected methods - Override these in subclasses
    # =========================================================================
    
    def _handle_ask(self, question: Any, **kwargs) -> Any:
        """Override to handle specific questions"""
        return f"Don't know how to answer: {question}"
    
    def _handle_tell(self, format: str, **kwargs) -> Any:
        """Override to handle specific formats"""
        return self._to_dict()
    
    def _handle_do(self, action: Any, **kwargs) -> Any:
        """Override to handle specific actions"""
        return f"Don't know how to: {action}"
    
    def _get_status(self) -> Dict:
        """Override to provide status"""
        return {'status': 'active', 'class': self.__class__.__name__}
    
    def _get_capabilities(self) -> List[str]:
        """Override to list capabilities"""
        return [
            "ask('status')",
            "ask('capabilities')",
            "tell('json')",
            "tell('discord')",
            "do('announce')",
            "do('validate')"
        ]
    
    def _get_help(self) -> str:
        """Override to provide help"""
        return f"""
{self.__class__.__name__} - Polymorphic Object

Universal methods:
  ask(question) - Query anything
  tell(format)  - Format output
  do(action)    - Perform action

Try:
  ask('status')
  tell('json')
  do('announce')
"""
    
    def _get_config(self) -> Dict:
        """Override to provide configuration"""
        return {}
    
    def _get_info(self) -> Dict:
        """Override to provide info"""
        return {
            'class': self.__class__.__name__,
            'module': self.__class__.__module__,
            'capabilities': len(self._get_capabilities())
        }
    
    def _to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self._to_dict(), indent=2, default=str)
    
    def _to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = {}
        for attr in dir(self):
            if not attr.startswith('_'):
                value = getattr(self, attr)
                if not callable(value):
                    try:
                        json.dumps(value)  # Test serializability
                        data[attr] = value
                    except:
                        data[attr] = str(value)
        return data
    
    def _brief_summary(self) -> str:
        """Brief summary"""
        return f"{self.__class__.__name__}"
    
    def _detailed_summary(self) -> str:
        """Detailed summary"""
        info = self._get_info()
        status = self._get_status()
        return f"{self.__class__.__name__}\nInfo: {info}\nStatus: {status}"
    
    def _format_discord(self) -> str:
        """Format for Discord"""
        return f"**{self.__class__.__name__}**"
    
    def _format_claude(self) -> Dict:
        """Format for Claude"""
        return {
            'type': self.__class__.__name__,
            'capabilities': self._get_capabilities(),
            'status': self._get_status()
        }
    
    def _announce_existence(self) -> bool:
        """Announce via Bonjour"""
        announcer.announce(
            self.__class__.__name__,
            self._get_capabilities()
        )
        return True
    
    def _refresh(self) -> bool:
        """Refresh/reload"""
        return True
    
    def _reset(self) -> bool:
        """Reset to initial state"""
        return True
    
    def _validate(self) -> Dict:
        """Validate object state"""
        return {'valid': True, 'errors': []}
    
    def _test(self) -> bool:
        """Test functionality"""
        return True
    
    def __str__(self) -> str:
        """String representation"""
        return self._brief_summary()
    
    def __repr__(self) -> str:
        """Developer representation"""
        return f"<{self.__class__.__name__} at {hex(id(self))}>"


# ============================================================================
# Example conversions showing how EVERYTHING becomes polymorphic
# ============================================================================

class PolymorphicService(UniversalPolymorphic):
    """Base for all services"""
    
    def _handle_do(self, action: str, **kwargs):
        """Services can start/stop/restart"""
        if 'start' in action:
            return self._start_service()
        elif 'stop' in action:
            return self._stop_service()
        elif 'restart' in action:
            self._stop_service()
            return self._start_service()
        return super()._handle_do(action, **kwargs)
    
    def _start_service(self):
        """Override in subclass"""
        return True
    
    def _stop_service(self):
        """Override in subclass"""
        return True


class PolymorphicBridge(UniversalPolymorphic):
    """Base for all bridges (Discord, Twilio, etc)"""
    
    def _handle_ask(self, question: str, **kwargs):
        """Bridges can be asked about connections"""
        if 'connected' in question:
            return self._is_connected()
        elif 'messages' in question:
            return self._get_messages()
        return super()._handle_ask(question, **kwargs)
    
    def _handle_do(self, action: str, **kwargs):
        """Bridges can connect/disconnect/send"""
        if 'connect' in action:
            return self._connect()
        elif 'disconnect' in action:
            return self._disconnect()
        elif 'send' in action:
            return self._send_message(kwargs.get('message'))
        return super()._handle_do(action, **kwargs)
    
    def _is_connected(self):
        """Override in subclass"""
        return False
    
    def _connect(self):
        """Override in subclass"""
        return True
    
    def _disconnect(self):
        """Override in subclass"""
        return True
    
    def _send_message(self, message):
        """Override in subclass"""
        return True
    
    def _get_messages(self):
        """Override in subclass"""
        return []


class PolymorphicModel(UniversalPolymorphic):
    """Base for all database models"""
    
    def _handle_do(self, action: str, **kwargs):
        """Models can save/delete/update"""
        if 'save' in action:
            return self._save_to_db(kwargs.get('session'))
        elif 'delete' in action:
            return self._delete_from_db(kwargs.get('session'))
        elif 'update' in action:
            return self._update_in_db(kwargs.get('session'))
        return super()._handle_do(action, **kwargs)
    
    def _save_to_db(self, session):
        """Override in subclass"""
        if session:
            session.add(self)
            return True
        return False
    
    def _delete_from_db(self, session):
        """Override in subclass"""
        if session:
            session.delete(self)
            return True
        return False
    
    def _update_in_db(self, session):
        """Override in subclass"""
        return self._save_to_db(session)


# This is the foundation - EVERYTHING inherits from UniversalPolymorphic!