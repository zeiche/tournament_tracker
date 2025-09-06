#!/usr/bin/env python3
"""
message_handler.py - Pure Message Handler
Handles messages from any source (Discord, CLI, web, etc.)
This is the ONLY place where message logic should exist.
"""
import sys
import logging

# Add path for imports
if '/home/ubuntu/claude/tournament_tracker' not in sys.path:
    sys.path.append('/home/ubuntu/claude/tournament_tracker')

# Simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageHandler:
    """Pure message handler - processes messages and returns responses"""
    
    def __init__(self):
        """Initialize handler"""
        self.query_handler = None
        self._load_query_handler()
    
    def _load_query_handler(self):
        """Try to load the polymorphic query handler"""
        try:
            from polymorphic_queries import query as pq
            self.query_handler = pq
            logger.info("Query handler loaded successfully")
        except ImportError as e:
            logger.warning(f"Query handler not available: {e}")
            self.query_handler = None
    
    def process_message(self, content: str, context: dict = None) -> str:
        """
        Process a message and return response.
        
        Args:
            content: The message content
            context: Optional context (user, channel, etc.)
        
        Returns:
            Response string
        """
        if not content or not content.strip():
            return "Please provide a message."
        
        content = content.strip()
        
        # Simple built-in commands
        if content.lower() == "ping":
            return "pong!"
        elif content.lower() == "help":
            return self._get_help_text()
        elif content.lower() == "status":
            return self._get_status()
        
        # Use query handler if available
        if self.query_handler:
            try:
                result = self.query_handler(content)
                if result:
                    return str(result)
                else:
                    return "No results found for your query."
            except Exception as e:
                logger.error(f"Query error: {e}")
                return f"Error processing query: {str(e)[:200]}"
        else:
            # Fallback mode
            return f"Query system not available. Echo: {content}"
    
    def _get_help_text(self) -> str:
        """Get help text"""
        help_text = """Available commands:
- ping: Check if bot is responsive
- help: Show this help message
- status: Show bot status
- show player [name]: Show player information
- show top [N] players: Show top N players
- recent tournaments: Show recent tournaments
- show tournament [name]: Show tournament details
- show organization [name]: Show organization details

Examples:
- show player west
- show top 10 players
- recent tournaments
- show tournament evo 2024
"""
        return help_text
    
    def _get_status(self) -> str:
        """Get status information"""
        status = "Bot Status:\n"
        status += f"- Message handler: ✅ Active\n"
        status += f"- Query system: {'✅ Loaded' if self.query_handler else '❌ Not available'}\n"
        
        # Try to get database status
        try:
            from database_service import database_service
            with get_session() as session:
                from tournament_models import Tournament, Player
                tournament_count = session.query(Tournament).count()
                player_count = session.query(Player).count()
                status += f"- Database: ✅ Connected\n"
                status += f"  - Tournaments: {tournament_count}\n"
                status += f"  - Players: {player_count}\n"
        except Exception as e:
            status += f"- Database: ❌ Error: {e}\n"
        
        return status


# Global instance
message_handler = MessageHandler()


# Convenience function
def handle_message(content: str, context: dict = None) -> str:
    """Process a message and return response"""
    return message_handler.process_message(content, context)


# CLI testing
if __name__ == "__main__":
    print("Message Handler Test Mode")
    print("Type 'quit' to exit")
    print("-" * 40)
    
    while True:
        try:
            message = input("> ").strip()
            if message.lower() in ('quit', 'exit'):
                break
            
            response = handle_message(message)
            print(response)
            print("-" * 40)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
            print("-" * 40)