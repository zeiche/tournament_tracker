#!/usr/bin/env python3
"""
truly_polymorphic.py - The ULTIMATE simplification: just ONE method
No more ask(), tell(), do() - just call the service and it figures out what you want.
"""
from typing import Any, Optional, Union
import sys
sys.path.append('/home/ubuntu/claude/tournament_tracker')
from polymorphic_core import announcer


class TrulyPolymorphic:
    """
    Base class for services that use just ONE method for everything.
    The method figures out from context what you want.
    """
    
    def __call__(self, request: Any, format: Optional[str] = None) -> Any:
        """
        The ONE method that does EVERYTHING.
        
        Examples:
            service("tournament 123")                    # Get data
            service("tournament 123", "discord")         # Get formatted
            service("tournament 123 as json")            # Alt format syntax  
            service("update tournament 123 name='New'")  # Perform action
            service("delete logs older than 7 days")     # Another action
            service("stats")                             # Get info
        """
        # Convert request to string for parsing
        request_str = str(request).strip()
        
        # Check for format in request string (e.g., "data as json")
        if " as " in request_str and not format:
            parts = request_str.split(" as ", 1)
            request_str = parts[0]
            format = parts[1]
        
        # Detect intent from keywords
        intent = self._detect_intent(request_str)
        
        # Route based on intent
        if intent == "action":
            return self._do_action(request_str)
        elif intent == "query":
            data = self._get_data(request_str)
            if format:
                return self._format_data(data, format)
            return data
        else:
            # Default - try to get data
            data = self._get_data(request_str)
            if format:
                return self._format_data(data, format)
            return data
    
    def _detect_intent(self, request: str) -> str:
        """Detect what the user wants from the request"""
        request_lower = request.lower()
        
        # Action keywords
        action_words = [
            'create', 'update', 'delete', 'remove', 'send', 'call',
            'start', 'stop', 'restart', 'publish', 'sync', 'merge',
            'clean', 'clear', 'reset', 'save', 'submit', 'do'
        ]
        
        # Check for action intent
        for word in action_words:
            if word in request_lower:
                return "action"
        
        # Everything else is a query
        return "query"
    
    def _get_data(self, request: str) -> Any:
        """Get data based on request - override in subclasses"""
        return f"Data for: {request}"
    
    def _do_action(self, request: str) -> Any:
        """Perform action based on request - override in subclasses"""
        return f"Action performed: {request}"
    
    def _format_data(self, data: Any, format: str) -> str:
        """Format data for output"""
        format_lower = format.lower().strip()
        
        if format_lower == "json":
            import json
            return json.dumps(data, default=str, indent=2)
        
        elif format_lower == "discord":
            if isinstance(data, dict):
                lines = [f"**{k}**: {v}" for k, v in data.items()]
                return "\n".join(lines)
            elif isinstance(data, list):
                return "\n".join([f"• {item}" for item in data[:10]])
            return f"```{data}```"
        
        elif format_lower in ["text", "plain", "string"]:
            return str(data)
        
        elif format_lower == "brief":
            s = str(data)
            return s[:200] + "..." if len(s) > 200 else s
        
        # Default - just convert to string
        return str(data)


class PolymorphicDatabase(TrulyPolymorphic):
    """Database service with just ONE method"""
    
    def __init__(self):
        announcer.announce(
            "Truly Polymorphic Database",
            [
                "ONE method for everything!",
                "db('tournament 123') - get data",
                "db('tournament 123', 'json') - get as JSON",
                "db('update tournament 123 name=foo') - update",
                "No more ask(), tell(), do() - just call!"
            ]
        )
    
    def _get_data(self, request: str) -> Any:
        """Get data from database"""
        request_lower = request.lower()
        
        # Parse what they want
        if "tournament" in request_lower:
            # Check for ID
            import re
            match = re.search(r'\d+', request)
            if match:
                return {"id": match.group(), "name": "Tournament", "type": "tournament"}
            return [{"id": 1, "name": "Tournament 1"}, {"id": 2, "name": "Tournament 2"}]
        
        if "player" in request_lower:
            return {"name": "Player", "type": "player"}
        
        if "stats" in request_lower:
            return {
                "tournaments": 100,
                "players": 500,
                "organizations": 20
            }
        
        return {"query": request, "result": "data"}
    
    def _do_action(self, request: str) -> Any:
        """Perform database action"""
        announcer.announce("Database Action", [request])
        
        if "update" in request.lower():
            return "Updated successfully"
        if "delete" in request.lower():
            return "Deleted successfully"
        if "create" in request.lower():
            return "Created successfully"
        
        return f"Action completed: {request}"


class PolymorphicLogger(TrulyPolymorphic):
    """Logger with just ONE method"""
    
    def __init__(self):
        self.logs = []
        announcer.announce(
            "Truly Polymorphic Logger",
            [
                "ONE method for logging and querying!",
                "logger('info: something happened') - log it",
                "logger('errors last hour') - query",
                "logger('errors last hour', 'discord') - formatted query",
                "logger('cleanup old logs') - action"
            ]
        )
    
    def _get_data(self, request: str) -> Any:
        """Get log data"""
        request_lower = request.lower()
        
        # Check if it's a log entry (has level prefix)
        for level in ['debug:', 'info:', 'warning:', 'error:', 'critical:']:
            if request_lower.startswith(level):
                # It's a log entry - store it
                message = request[len(level):].strip()
                log_entry = {"level": level[:-1], "message": message}
                self.logs.append(log_entry)
                return f"Logged: {message}"
        
        # Otherwise it's a query
        if "error" in request_lower:
            return [log for log in self.logs if log.get("level") == "error"]
        
        if "recent" in request_lower:
            return self.logs[-10:]
        
        return self.logs
    
    def _do_action(self, request: str) -> Any:
        """Perform logger action"""
        if "cleanup" in request.lower() or "clear" in request.lower():
            count = len(self.logs)
            self.logs.clear()
            return f"Cleared {count} logs"
        
        return f"Logger action: {request}"


class PolymorphicTwilio(TrulyPolymorphic):
    """Twilio with just ONE method"""
    
    def __init__(self):
        self.phone = "+1234567890"
        announcer.announce(
            "Truly Polymorphic Twilio",
            [
                "ONE method for all telephony!",
                "twilio('send sms to 555-1234: Hello') - send SMS",
                "twilio('recent messages') - get messages",
                "twilio('recent messages', 'discord') - formatted",
                "twilio('call 555-1234') - make call"
            ]
        )
    
    def _get_data(self, request: str) -> Any:
        """Get Twilio data"""
        request_lower = request.lower()
        
        if "message" in request_lower or "sms" in request_lower:
            return [
                {"from": "555-1111", "to": self.phone, "body": "Hello"},
                {"from": "555-2222", "to": self.phone, "body": "Hi there"}
            ]
        
        if "phone" in request_lower:
            return self.phone
        
        if "call" in request_lower:
            return {"active_calls": 0}
        
        return {"service": "twilio", "status": "ready"}
    
    def _do_action(self, request: str) -> Any:
        """Perform Twilio action"""
        request_lower = request.lower()
        
        if "send" in request_lower or "text" in request_lower:
            # Parse phone and message
            import re
            phone_match = re.search(r'[\d-]+', request)
            if phone_match:
                announcer.announce("SMS", [f"Sending to {phone_match.group()}"])
                return f"SMS sent to {phone_match.group()}"
        
        if "call" in request_lower:
            import re
            phone_match = re.search(r'[\d-]+', request)
            if phone_match:
                announcer.announce("Call", [f"Calling {phone_match.group()}"])
                return f"Calling {phone_match.group()}"
        
        return f"Twilio action: {request}"


# Examples showing the ultimate simplicity
if __name__ == "__main__":
    # Create services
    db = PolymorphicDatabase()
    logger = PolymorphicLogger()
    twilio = PolymorphicTwilio()
    
    print("=== ONE METHOD DOES EVERYTHING ===\n")
    
    # Database examples
    print("DATABASE:")
    print(db("tournament 123"))                    # Get data
    print(db("tournament 123", "json"))           # Get as JSON
    print(db("tournament 123 as discord"))        # Alt syntax
    print(db("update tournament 123 name='New'")) # Action
    print()
    
    # Logger examples
    print("LOGGER:")
    print(logger("info: Application started"))     # Log something
    print(logger("error: Something failed"))       # Log error
    print(logger("recent logs"))                   # Query logs
    print(logger("recent logs", "discord"))        # Formatted query
    print(logger("cleanup old logs"))              # Action
    print()
    
    # Twilio examples
    print("TWILIO:")
    print(twilio("phone number"))                  # Get info
    print(twilio("send sms to 555-1234: Hello"))  # Send SMS
    print(twilio("recent messages"))               # Get messages
    print(twilio("recent messages as discord"))    # Formatted
    print(twilio("call 555-1234"))                # Make call
    
    print("\n=== NO MORE ask(), tell(), do() - JUST CALL! ===")