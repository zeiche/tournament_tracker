#!/usr/bin/env python3
"""
tournament_models_simplified.py - Tournament models with just THREE methods
This shows how to extend existing models with the polymorphic approach.
"""
from typing import Any, Optional, List, Dict
from sqlalchemy.orm import Session
from polymorphic_model import PolymorphicModel
from capability_announcer import announcer


class TournamentPolymorphic(PolymorphicModel):
    """
    Tournament-specific implementation of the 3-method pattern.
    This would be mixed into the existing Tournament model.
    """
    
    def _ask_winner(self, session: Optional[Session]) -> Any:
        """Get the tournament winner"""
        if hasattr(self, 'placements') and self.placements:
            # Find placement with position 1
            for placement in self.placements:
                if placement.placement == 1:
                    return placement.player
        
        if session and hasattr(self, 'id'):
            # Query for winner
            from tournament_models import TournamentPlacement
            winner = session.query(TournamentPlacement).filter_by(
                tournament_id=self.id,
                placement=1
            ).first()
            return winner.player if winner else None
        
        return None
    
    def _ask_top_n(self, n: int, session: Optional[Session]) -> List:
        """Get top N placements"""
        if hasattr(self, 'placements') and self.placements:
            # Sort by placement and return top N
            sorted_placements = sorted(self.placements, key=lambda x: x.placement)
            return sorted_placements[:n]
        
        if session and hasattr(self, 'id'):
            from tournament_models import TournamentPlacement
            return session.query(TournamentPlacement).filter_by(
                tournament_id=self.id
            ).order_by(TournamentPlacement.placement).limit(n).all()
        
        return []
    
    def _ask_attendance(self) -> Any:
        """Get tournament attendance"""
        return getattr(self, 'num_attendees', 0)
    
    def _ask_recent(self, session: Optional[Session]) -> List:
        """Get recent related items (recent players, etc)"""
        # For a tournament, "recent" might mean recent similar tournaments
        if session:
            from tournament_models import Tournament
            return session.query(Tournament).filter(
                Tournament.venue_name == self.venue_name,
                Tournament.id != self.id
            ).order_by(Tournament.date.desc()).limit(5).all()
        return []
    
    def _ask_statistics(self) -> Dict:
        """Get tournament statistics"""
        stats = {
            'name': getattr(self, 'name', None),
            'date': getattr(self, 'date', None),
            'attendance': getattr(self, 'num_attendees', 0),
            'venue': getattr(self, 'venue_name', None),
            'game': getattr(self, 'game_name', None),
            'is_major': getattr(self, 'is_major', False),
            'days_ago': getattr(self, 'days_ago', None),
        }
        
        # Add calculated stats
        if hasattr(self, 'num_attendees'):
            if self.num_attendees > 100:
                stats['size_category'] = 'Major'
            elif self.num_attendees > 50:
                stats['size_category'] = 'Regional'
            else:
                stats['size_category'] = 'Local'
        
        return stats
    
    def _tell_discord(self) -> str:
        """Format tournament for Discord"""
        return f"""**{getattr(self, 'name', 'Tournament')}**
📅 {getattr(self, 'date', 'Unknown date')}
📍 {getattr(self, 'venue_name', 'Unknown venue')}
👥 {getattr(self, 'num_attendees', 0)} players
🎮 {getattr(self, 'game_name', 'Unknown game')}"""
    
    def _tell_claude(self) -> Dict:
        """Explain tournament to Claude"""
        return {
            'type': 'Tournament',
            'name': getattr(self, 'name', None),
            'capabilities': [
                'ask("winner") - Get tournament winner',
                'ask("top 8") - Get top 8 placements',
                'ask("attendance") - Get player count',
                'tell("discord") - Format for Discord',
                'do("sync") - Sync from start.gg'
            ],
            'current_data': self._ask_statistics(),
            'examples': [
                f'tournament.ask("who won")',
                f'tournament.tell("discord")',
                f'tournament.do("calculate stats")'
            ]
        }
    
    def _tell_brief(self) -> str:
        """Brief tournament summary"""
        return f"{getattr(self, 'name', 'Tournament')} ({getattr(self, 'num_attendees', 0)} players)"
    
    def _do_sync(self, session: Optional[Session], **kwargs) -> bool:
        """Sync tournament from start.gg"""
        # This would call the existing sync logic
        announcer.announce(
            "Tournament Sync",
            [f"Syncing {getattr(self, 'name', 'tournament')} from start.gg"]
        )
        # Call existing sync method if available
        if hasattr(self, '_sync_from_api'):
            return self._sync_from_api(session)
        return True
    
    def _do_calculate(self, **kwargs) -> Dict:
        """Calculate all tournament statistics"""
        stats = self._ask_statistics()
        
        # Add growth calculation if we have previous tournament
        if 'previous' in kwargs:
            prev = kwargs['previous']
            if hasattr(prev, 'num_attendees') and hasattr(self, 'num_attendees'):
                growth = ((self.num_attendees - prev.num_attendees) / prev.num_attendees) * 100
                stats['growth_percentage'] = growth
        
        return stats


class PlayerPolymorphic(PolymorphicModel):
    """
    Player-specific implementation of the 3-method pattern.
    """
    
    def _ask_winner(self, session: Optional[Session]) -> Any:
        """For a player, 'winner' might mean tournaments they won"""
        if session and hasattr(self, 'id'):
            from tournament_models import TournamentPlacement
            wins = session.query(TournamentPlacement).filter_by(
                player_id=self.id,
                placement=1
            ).all()
            return [win.tournament for win in wins]
        return []
    
    def _ask_top_n(self, n: int, session: Optional[Session]) -> List:
        """Get player's top N placements"""
        if hasattr(self, 'placements'):
            sorted_placements = sorted(self.placements, key=lambda x: x.placement)
            return sorted_placements[:n]
        
        if session and hasattr(self, 'id'):
            from tournament_models import TournamentPlacement
            return session.query(TournamentPlacement).filter_by(
                player_id=self.id
            ).order_by(TournamentPlacement.placement).limit(n).all()
        
        return []
    
    def _ask_recent(self, session: Optional[Session]) -> List:
        """Get player's recent tournaments"""
        if session and hasattr(self, 'id'):
            from tournament_models import TournamentPlacement, Tournament
            recent = session.query(TournamentPlacement).join(Tournament).filter(
                TournamentPlacement.player_id == self.id
            ).order_by(Tournament.date.desc()).limit(5).all()
            return [r.tournament for r in recent]
        return []
    
    def _ask_statistics(self) -> Dict:
        """Get player statistics"""
        stats = {
            'gamertag': getattr(self, 'gamertag', None),
            'real_name': getattr(self, 'real_name', None),
            'points': getattr(self, 'points', 0),
            'ranking': getattr(self, 'ranking', None),
            'win_rate': getattr(self, 'win_rate', 0),
            'consistency_score': getattr(self, 'consistency_score', 0),
        }
        
        # Add calculated stats
        if hasattr(self, 'placements'):
            stats['tournaments_entered'] = len(self.placements)
            stats['wins'] = sum(1 for p in self.placements if p.placement == 1)
            stats['top_3s'] = sum(1 for p in self.placements if p.placement <= 3)
        
        return stats
    
    def _tell_discord(self) -> str:
        """Format player for Discord"""
        output = f"**{getattr(self, 'gamertag', 'Player')}**"
        if hasattr(self, 'real_name') and self.real_name:
            output += f" ({self.real_name})"
        
        if hasattr(self, 'ranking'):
            output += f"\n🏆 Rank #{self.ranking}"
        
        if hasattr(self, 'points'):
            output += f" | {self.points} pts"
        
        if hasattr(self, 'win_rate'):
            output += f"\n📊 Win rate: {self.win_rate:.1f}%"
        
        return output
    
    def _tell_claude(self) -> Dict:
        """Explain player to Claude"""
        return {
            'type': 'Player',
            'gamertag': getattr(self, 'gamertag', None),
            'capabilities': [
                'ask("wins") - Get tournaments won',
                'ask("recent") - Get recent tournaments',
                'ask("statistics") - Get all stats',
                'tell("discord") - Format for Discord',
                'do("update stats") - Recalculate statistics'
            ],
            'current_data': self._ask_statistics(),
            'examples': [
                f'player.ask("recent tournaments")',
                f'player.ask("win rate")',
                f'player.tell("discord")'
            ]
        }


class OrganizationPolymorphic(PolymorphicModel):
    """
    Organization-specific implementation of the 3-method pattern.
    """
    
    def _ask_attendance(self) -> Any:
        """Get total attendance across all tournaments"""
        if hasattr(self, 'tournaments'):
            return sum(t.num_attendees for t in self.tournaments if t.num_attendees)
        return getattr(self, 'total_attendance', 0)
    
    def _ask_recent(self, session: Optional[Session]) -> List:
        """Get organization's recent tournaments"""
        if hasattr(self, 'tournaments'):
            sorted_tournaments = sorted(self.tournaments, key=lambda x: x.date, reverse=True)
            return sorted_tournaments[:5]
        
        if session and hasattr(self, 'id'):
            from tournament_models import Tournament
            return session.query(Tournament).filter_by(
                organization_id=self.id
            ).order_by(Tournament.date.desc()).limit(5).all()
        
        return []
    
    def _ask_statistics(self) -> Dict:
        """Get organization statistics"""
        stats = {
            'name': getattr(self, 'display_name', None),
            'total_events': getattr(self, 'total_events', 0),
            'total_attendance': self._ask_attendance(),
        }
        
        # Calculate average attendance
        if stats['total_events'] > 0:
            stats['average_attendance'] = stats['total_attendance'] / stats['total_events']
        
        # Add contact info if available
        if hasattr(self, 'contacts'):
            stats['contact_count'] = len(self.contacts)
        
        return stats
    
    def _tell_discord(self) -> str:
        """Format organization for Discord"""
        stats = self._ask_statistics()
        return f"""**{stats.get('name', 'Organization')}**
📊 {stats.get('total_events', 0)} events hosted
👥 {stats.get('total_attendance', 0)} total attendance
📈 {stats.get('average_attendance', 0):.1f} average attendance"""
    
    def _tell_claude(self) -> Dict:
        """Explain organization to Claude"""
        return {
            'type': 'Organization',
            'name': getattr(self, 'display_name', None),
            'capabilities': [
                'ask("recent") - Get recent tournaments',
                'ask("total attendance") - Get total attendance',
                'ask("statistics") - Get all stats',
                'tell("discord") - Format for Discord',
                'do("add contact", email="...") - Add contact'
            ],
            'current_data': self._ask_statistics(),
            'examples': [
                f'org.ask("recent tournaments")',
                f'org.ask("average attendance")',
                f'org.do("add contact", email="info@org.com")'
            ]
        }


# ============================================================================
# How to integrate with existing models
# ============================================================================

def simplify_existing_models():
    """
    This shows how to add the 3-method pattern to EXISTING models
    without removing their current methods.
    """
    try:
        from tournament_models import Tournament, Player, Organization
        
        # Add the polymorphic base to existing models
        # This gives them ask(), tell(), do() while keeping existing methods
        Tournament.__bases__ += (TournamentPolymorphic,)
        Player.__bases__ += (PlayerPolymorphic,)
        Organization.__bases__ += (OrganizationPolymorphic,)
        
        # Announce the simplification
        announcer.announce(
            "Model Simplification",
            [
                "Models now have 3 polymorphic methods",
                "ask(question) - Query anything",
                "tell(format) - Format for output",
                "do(action) - Perform actions"
            ],
            [
                'tournament.ask("winner")',
                'player.tell("discord")',
                'org.do("calculate stats")'
            ]
        )
        
        return True
        
    except Exception as e:
        announcer.announce(
            "Simplification Error",
            [f"Could not simplify models: {e}"]
        )
        return False


# Auto-simplify when imported
if __name__ != "__main__":
    simplify_existing_models()