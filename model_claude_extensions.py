#!/usr/bin/env python3
"""
model_claude_extensions.py - Extend existing models with Claude-aware methods
These are mixins that add Claude-specific functionality to our EXISTING models
"""
from typing import Dict, List, Any, Optional
from capability_announcer import announcer


class ClaudeAwareMixin:
    """
    Mixin that makes models Claude-aware.
    Add this to existing SQLAlchemy models to give them Claude capabilities.
    """
    
    def explain_to_claude(self) -> Dict[str, Any]:
        """
        Model explains itself to Claude in a way Claude can understand.
        Override in each model for specific explanation.
        """
        return {
            'type': self.__class__.__name__,
            'id': getattr(self, 'id', None),
            'capabilities': self.get_claude_capabilities(),
            'current_state': self.get_current_state(),
            'example_questions': self.get_example_questions()
        }
    
    def get_claude_capabilities(self) -> List[str]:
        """
        List what this object can do for Claude.
        Override in each model.
        """
        # Introspect to find available methods
        capabilities = []
        for attr_name in dir(self):
            if attr_name.startswith('get_') or attr_name.startswith('calculate_'):
                # This is a capability
                method = getattr(self, attr_name)
                if callable(method) and hasattr(method, '__doc__'):
                    capabilities.append(method.__doc__ or attr_name)
        return capabilities
    
    def get_example_questions(self) -> List[str]:
        """
        Provide example questions Claude can answer about this object.
        Override for specific examples.
        """
        return [
            f"Tell me about this {self.__class__.__name__}",
            f"What can this {self.__class__.__name__} do?",
            f"Show me the details"
        ]
    
    def get_current_state(self) -> Dict[str, Any]:
        """
        Get current state of this object for Claude's context.
        """
        state = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):  # Skip private attributes
                state[key] = value
        return state
    
    def answer_claude_question(self, question: str, session=None) -> Any:
        """
        Model tries to answer Claude's question about itself.
        """
        question_lower = question.lower()
        
        # Try to match question to capabilities
        if "can you" in question_lower or "what can" in question_lower:
            return self.get_claude_capabilities()
        
        if "explain" in question_lower or "tell me about" in question_lower:
            return self.explain_to_claude()
        
        if "example" in question_lower:
            return self.get_example_questions()
        
        # Try to call matching methods
        for method_name in dir(self):
            if method_name.startswith('get_') or method_name.startswith('calculate_'):
                if method_name[4:].replace('_', ' ') in question_lower:
                    method = getattr(self, method_name)
                    if callable(method):
                        try:
                            # Call with session if needed
                            import inspect
                            sig = inspect.signature(method)
                            if 'session' in sig.parameters and session:
                                return method(session)
                            else:
                                return method()
                        except:
                            pass
        
        return self.explain_to_claude()
    
    def announce_to_claude(self):
        """
        Model announces itself to Claude using Bonjour-style discovery.
        """
        announcer.announce(
            f"{self.__class__.__name__} Instance",
            self.get_claude_capabilities(),
            self.get_example_questions()
        )


class TournamentClaudeExtension(ClaudeAwareMixin):
    """
    Claude-aware extensions specifically for Tournament model.
    """
    
    def get_claude_capabilities(self) -> List[str]:
        """Tournament-specific capabilities for Claude"""
        return [
            f"Show attendance: {self.num_attendees} players",
            f"Get top 8 placements",
            f"Calculate growth metrics",
            f"Show venue: {self.venue_name}",
            f"Check if major tournament: {self.is_major}",
            f"Days since tournament: {self.days_ago}",
            "Get geographic coordinates",
            "Show all player standings"
        ]
    
    def get_example_questions(self) -> List[str]:
        """Tournament-specific example questions"""
        return [
            f"Who won {self.name}?",
            f"How many people attended {self.name}?",
            f"Where was {self.name} held?",
            f"Show top 8 for {self.name}",
            f"Is {self.name} a major?",
            f"When was {self.name}?"
        ]
    
    def format_for_discord(self) -> str:
        """Format tournament for Discord output"""
        return (
            f"**{self.name}**\n"
            f"📅 {self.date}\n"
            f"📍 {self.venue_name}\n"
            f"👥 {self.num_attendees} players\n"
            f"🎮 {self.game_name}"
        )


class PlayerClaudeExtension(ClaudeAwareMixin):
    """
    Claude-aware extensions for Player model.
    """
    
    def get_claude_capabilities(self) -> List[str]:
        """Player-specific capabilities"""
        caps = [
            f"Current points: {self.points}",
            f"Win rate: {self.win_rate:.1f}%",
            f"Consistency score: {self.consistency_score:.2f}",
            "Show tournament history",
            "Calculate performance trend",
            "Get recent placements",
            "Show head-to-head records"
        ]
        if self.ranking:
            caps.insert(0, f"Current ranking: #{self.ranking}")
        return caps
    
    def get_example_questions(self) -> List[str]:
        """Player-specific example questions"""
        return [
            f"How is {self.gamertag} doing?",
            f"Show {self.gamertag}'s recent results",
            f"What's {self.gamertag}'s win rate?",
            f"Where does {self.gamertag} rank?",
            f"Show {self.gamertag}'s tournament history"
        ]
    
    def format_for_discord(self) -> str:
        """Format player for Discord"""
        output = f"**{self.gamertag}**"
        if self.real_name:
            output += f" ({self.real_name})"
        output += f"\n🏆 Rank #{self.ranking} | {self.points} pts"
        output += f"\n📊 Win rate: {self.win_rate:.1f}%"
        return output


class OrganizationClaudeExtension(ClaudeAwareMixin):
    """
    Claude-aware extensions for Organization model.
    """
    
    def get_claude_capabilities(self) -> List[str]:
        """Organization-specific capabilities"""
        return [
            f"Total events hosted: {self.total_events}",
            f"Total attendance: {self.total_attendance}",
            f"Average attendance: {self.average_attendance:.1f}",
            "Show tournament schedule",
            "Get contact information",
            "Calculate growth rate",
            "Show venue locations",
            "List upcoming events"
        ]
    
    def get_example_questions(self) -> List[str]:
        """Organization-specific example questions"""
        return [
            f"How many events has {self.display_name} hosted?",
            f"What's the average attendance for {self.display_name}?",
            f"Show {self.display_name}'s upcoming tournaments",
            f"How do I contact {self.display_name}?",
            f"Where does {self.display_name} host events?"
        ]
    
    def format_for_discord(self) -> str:
        """Format organization for Discord"""
        return (
            f"**{self.display_name}**\n"
            f"📊 {self.total_events} events hosted\n"
            f"👥 {self.total_attendance} total attendance\n"
            f"📈 {self.average_attendance:.1f} average attendance"
        )


def extend_existing_models():
    """
    Monkey-patch our existing models with Claude awareness.
    This adds Claude methods to the EXISTING models without modifying them.
    """
    try:
        from tournament_models import Tournament, Player, Organization
        
        # Add Claude awareness to existing models
        Tournament.__bases__ += (TournamentClaudeExtension,)
        Player.__bases__ += (PlayerClaudeExtension,)
        Organization.__bases__ += (OrganizationClaudeExtension,)
        
        # Announce that models are Claude-aware
        announcer.announce(
            "Model Extension System",
            ["Extended existing models with Claude awareness"],
            ["Models can now explain themselves to Claude"]
        )
        
        return True
    except Exception as e:
        announcer.announce(
            "Model Extension Error",
            [f"Failed to extend models: {e}"]
        )
        return False


# Auto-extend when imported
extend_existing_models()