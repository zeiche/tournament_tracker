#!/usr/bin/env python3
"""
Enhanced Database Context Provider
Provides comprehensive tournament data context for Claude
"""

from typing import Dict, Any, List, Optional
from database import get_session
from tournament_models import Tournament, Organization, Player, TournamentPlacement
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
import re

class EnhancedDatabaseContext:
    """Provides rich, comprehensive database context for all queries"""
    
    @classmethod
    def get_comprehensive_context(cls, query: str) -> Dict[str, Any]:
        """
        Get ALL relevant database information for any query.
        This ensures Claude has maximum context to answer questions.
        """
        context = {
            'query': query,
            'database_info': {}
        }
        
        with get_session() as session:
            # 1. OVERALL STATISTICS
            context['database_info']['statistics'] = {
                'total_tournaments': session.query(Tournament).count(),
                'total_organizations': session.query(Organization).count(),
                'total_players': session.query(Player).count(),
                'total_placements_recorded': session.query(TournamentPlacement).count(),
                'tournaments_with_standings': session.query(
                    func.count(func.distinct(TournamentPlacement.tournament_id))
                ).scalar()
            }
            
            # 2. RECENT TOURNAMENTS WITH DETAILS
            recent_tournaments = session.query(Tournament).order_by(
                desc(Tournament.start_at)
            ).limit(20).all()
            
            context['database_info']['recent_tournaments'] = []
            for t in recent_tournaments:
                tournament_info = {
                    'id': t.id,
                    'name': t.name,
                    'date': datetime.fromtimestamp(t.start_at).strftime('%Y-%m-%d') if t.start_at else 'Unknown',
                    'attendees': t.num_attendees or 0,
                    'venue': t.venue_name or 'Unknown',
                    'city': t.city or 'Unknown',
                    'organization': None
                }
                
                # Get organization (check if attribute exists)
                if hasattr(t, 'normalized_contact') and t.normalized_contact:
                    org = session.query(Organization).filter(
                        Organization.normalized_key == t.normalized_contact
                    ).first()
                    if org:
                        tournament_info['organization'] = org.display_name
                
                # Get top 8 for this tournament if available
                placements = session.query(TournamentPlacement).filter(
                    TournamentPlacement.tournament_id == t.id,
                    TournamentPlacement.placement <= 8
                ).order_by(TournamentPlacement.placement).all()
                
                if placements:
                    tournament_info['top_8'] = []
                    for p in placements:
                        player = session.query(Player).filter(Player.id == p.player_id).first()
                        tournament_info['top_8'].append({
                            'placement': p.placement,
                            'player': player.gamer_tag if player else 'Unknown',
                            'event': p.event_name or 'Singles'
                        })
                
                context['database_info']['recent_tournaments'].append(tournament_info)
            
            # 3. TOP PLAYERS BY VARIOUS METRICS
            # Players by tournament count
            player_tournament_counts = session.query(
                Player.gamer_tag,
                func.count(func.distinct(TournamentPlacement.tournament_id)).label('tournaments'),
                func.count(TournamentPlacement.id).label('total_placements')
            ).join(
                TournamentPlacement
            ).group_by(
                Player.id
            ).order_by(
                desc('tournaments')
            ).limit(20).all()
            
            context['database_info']['top_players_by_participation'] = [
                {
                    'player': p[0],
                    'tournaments_entered': p[1],
                    'total_placements': p[2]
                }
                for p in player_tournament_counts if p[0]
            ]
            
            # Players by wins (1st places)
            winners = session.query(
                Player.gamer_tag,
                func.count(TournamentPlacement.id).label('wins')
            ).join(
                TournamentPlacement
            ).filter(
                TournamentPlacement.placement == 1
            ).group_by(
                Player.id
            ).order_by(
                desc('wins')
            ).limit(20).all()
            
            context['database_info']['top_players_by_wins'] = [
                {'player': w[0], 'first_place_finishes': w[1]}
                for w in winners if w[0]
            ]
            
            # Players by top 3 finishes
            podium_finishers = session.query(
                Player.gamer_tag,
                func.count(TournamentPlacement.id).label('podiums')
            ).join(
                TournamentPlacement
            ).filter(
                TournamentPlacement.placement <= 3
            ).group_by(
                Player.id
            ).order_by(
                desc('podiums')
            ).limit(20).all()
            
            context['database_info']['top_players_by_podiums'] = [
                {'player': p[0], 'top_3_finishes': p[1]}
                for p in podium_finishers if p[0]
            ]
            
            # 4. ORGANIZATIONS WITH TOURNAMENT DATA
            # Just get organization counts for now
            org_data = session.query(
                Organization.display_name,
                Organization.id
            ).limit(15).all()
            
            context['database_info']['top_organizations'] = [
                {
                    'name': o[0],
                    'id': o[1]
                }
                for o in org_data if o[0]
            ]
            
            # 5. VENUE STATISTICS
            venue_stats = session.query(
                Tournament.venue_name,
                Tournament.city,
                func.count(Tournament.id).label('events'),
                func.sum(Tournament.num_attendees).label('total_attendance')
            ).filter(
                Tournament.venue_name.isnot(None)
            ).group_by(
                Tournament.venue_name,
                Tournament.city
            ).order_by(
                desc('events')
            ).limit(15).all()
            
            context['database_info']['top_venues'] = [
                {
                    'venue': v[0],
                    'city': v[1] or 'Unknown',
                    'events_hosted': v[2],
                    'total_attendance': v[3] or 0
                }
                for v in venue_stats
            ]
            
            # 6. EVENT/GAME STATISTICS
            event_stats = session.query(
                TournamentPlacement.event_name,
                func.count(func.distinct(TournamentPlacement.tournament_id)).label('tournaments'),
                func.count(func.distinct(TournamentPlacement.player_id)).label('unique_players')
            ).filter(
                TournamentPlacement.event_name.isnot(None)
            ).group_by(
                TournamentPlacement.event_name
            ).order_by(
                desc('tournaments')
            ).all()
            
            context['database_info']['games_and_events'] = [
                {
                    'event_name': e[0],
                    'tournaments_with_event': e[1],
                    'unique_players': e[2]
                }
                for e in event_stats
            ]
            
            # 7. SPECIFIC QUERY HANDLING
            query_lower = query.lower()
            
            # If asking about specific tournament
            if 'top 8' in query_lower or 'top-8' in query_lower or 'standings' in query_lower:
                # Try to find tournament name in query
                # Get the most recent tournament with standings
                recent_with_standings = session.query(Tournament).join(
                    TournamentPlacement
                ).group_by(Tournament.id).order_by(
                    desc(Tournament.start_at)
                ).limit(5).all()
                
                context['database_info']['tournaments_with_standings'] = []
                for t in recent_with_standings:
                    standings = session.query(TournamentPlacement).filter(
                        TournamentPlacement.tournament_id == t.id
                    ).order_by(TournamentPlacement.placement).limit(8).all()
                    
                    if standings:
                        tournament_standings = {
                            'tournament_name': t.name,
                            'date': datetime.fromtimestamp(t.start_at).strftime('%Y-%m-%d') if t.start_at else 'Unknown',
                            'standings': []
                        }
                        
                        for s in standings:
                            player = session.query(Player).filter(Player.id == s.player_id).first()
                            tournament_standings['standings'].append({
                                'placement': s.placement,
                                'player': player.gamer_tag if player else 'Unknown',
                                'event': s.event_name or 'Singles'
                            })
                        
                        context['database_info']['tournaments_with_standings'].append(tournament_standings)
            
            # If asking about specific player
            player_patterns = [
                r'show player\s+(\w+)',  # "show player west"
                r'player\s+(\w+)',        # "player west"
                r'\b(\w+)\b.*player',     # "west player"
                r'about\s+(\w+)',         # "about west"
            ]
            for pattern in player_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    player_name = match.group(1)
                    # Search for player
                    players = session.query(Player).filter(
                        Player.gamer_tag.ilike(f'%{player_name}%')
                    ).limit(5).all()
                    
                    context['database_info']['player_search_results'] = []
                    for player in players:
                        placements = session.query(TournamentPlacement).filter(
                            TournamentPlacement.player_id == player.id
                        ).order_by(TournamentPlacement.placement).limit(10).all()
                        
                        player_info = {
                            'gamer_tag': player.gamer_tag,
                            'recent_placements': []
                        }
                        
                        for p in placements:
                            tournament = session.query(Tournament).filter(
                                Tournament.id == p.tournament_id
                            ).first()
                            if tournament:
                                player_info['recent_placements'].append({
                                    'tournament': tournament.name,
                                    'placement': p.placement,
                                    'event': p.event_name or 'Singles'
                                })
                        
                        context['database_info']['player_search_results'].append(player_info)
                    break
            
            # 8. ATTENDANCE TRENDS
            attendance_by_month = session.query(
                func.strftime('%Y-%m', func.datetime(Tournament.start_at, 'unixepoch')).label('month'),
                func.count(Tournament.id).label('tournament_count'),
                func.sum(Tournament.num_attendees).label('total_attendance')
            ).filter(
                Tournament.start_at.isnot(None)
            ).group_by('month').order_by(desc('month')).limit(12).all()
            
            context['database_info']['monthly_trends'] = [
                {
                    'month': m[0],
                    'tournaments': m[1],
                    'total_attendance': m[2] or 0
                }
                for m in attendance_by_month
            ]
        
        return context