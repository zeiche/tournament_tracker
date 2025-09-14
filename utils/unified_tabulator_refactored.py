#!/usr/bin/env python3
"""
unified_tabulator_refactored.py - Service locator-based universal tabulation system

This module provides universal tabulation using service discovery for dependencies.
ALL ranking/tabulation should use this refactored version.

Key features:
- Uses service locator for all dependencies (database, logger, error handler, config)
- 3-method polymorphic pattern (ask/tell/do)
- Distributed tabulation support via network services
- Backward compatibility with existing tabulation functions
- Enhanced error handling and monitoring
"""
from typing import Any, List, Tuple, Optional, Callable, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from dataclasses import dataclass, field
from enum import Enum
import json

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.unified_tabulator_refactored")
import time
from polymorphic_core import announcer
from polymorphic_core.service_locator import get_service
from polymorphic_core.network_service_wrapper import NetworkServiceWrapper

# Announce service capabilities
announcer.announce(
    "Unified Tabulator Service",
    [
        "Universal tabulation system for ANY ranking type",
        "Player rankings by tournament points with SQL optimization", 
        "Organization rankings by attendance and event count",
        "Custom ranking with flexible scoring functions",
        "Proper tie handling and rank assignment",
        "Multiple output formats (text, markdown, html, json)",
        "Service locator-based dependencies for distributed operation",
        "Enhanced monitoring and statistics tracking",
        "Backward compatibility with existing tabulation functions"
    ],
    [
        "tabulator.ask('player rankings limit 50')",
        "tabulator.tell('json', ranking_data)",
        "tabulator.do('tabulate players by points')",
        "UnifiedTabulator.tabulate(items, score_func)",
        "get_player_rankings(session, limit=50)"
    ]
)


class RankingType(Enum):
    """Types of rankings we support"""
    PLAYER_POINTS = "player_points"
    ORG_ATTENDANCE = "org_attendance"
    ORG_EVENT_COUNT = "org_event_count"
    CUSTOM = "custom"


@dataclass
class RankedItem:
    """A ranked item with all necessary metadata"""
    rank: int
    item: Any
    score: float
    tie: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON/API responses"""
        result = {
            'rank': self.rank,
            'score': self.score,
            'tie': self.tie
        }
        if self.metadata:
            result.update(self.metadata)
        return result


class UnifiedTabulatorService:
    """
    Service locator-based universal tabulator for distributed ranking operations.
    
    This is the SINGLE SOURCE OF TRUTH for:
    - Calculating scores across network services
    - Sorting items with distributed data
    - Assigning ranks with proper tie handling
    - Formatting output for various consumers
    
    Uses service locator pattern for all dependencies to enable:
    - Distributed tabulation across multiple machines
    - Network-based database access
    - Centralized logging and error handling
    - Configuration-driven behavior
    """
    
    def __init__(self, prefer_network: bool = False):
        """Initialize with service locator dependencies"""
        self.prefer_network = prefer_network
        
        # Lazy-loaded service dependencies
        self._database = None
        self._logger = None
        self._error_handler = None
        self._config = None
        self._points_system = None
        
        # Statistics tracking
        self.stats = {
            'tabulations_performed': 0,
            'items_ranked': 0,
            'formats_generated': 0,
            'errors_encountered': 0,
            'last_operation': None,
            'start_time': time.time()
        }
        
        # Announce service initialization
        announcer.announce(
            "UnifiedTabulatorService", 
            [f"Initialized with prefer_network={prefer_network}"],
            [f"tabulator.ask('stats')", f"tabulator.do('rank players')"]
        )
    
    @property
    def database(self):
        """Get database service via service locator"""
        if self._database is None:
            self._database = get_service("database", self.prefer_network)
        return self._database
    
    @property
    def logger(self):
        """Get logger service via service locator"""
        if self._logger is None:
            self._logger = get_service("logger", self.prefer_network)
        return self._logger
    
    @property
    def error_handler(self):
        """Get error handler service via service locator"""
        if self._error_handler is None:
            self._error_handler = get_service("error_handler", self.prefer_network)
        return self._error_handler
    
    @property
    def config(self):
        """Get config service via service locator"""
        if self._config is None:
            self._config = get_service("config", self.prefer_network)
        return self._config
    
    @property
    def points_system(self):
        """Get points system service via service locator"""
        if self._points_system is None:
            self._points_system = get_service("points_system", self.prefer_network)
        return self._points_system
    
    def ask(self, query: str, **kwargs) -> Any:
        """
        Query tabulator for rankings or information using natural language.
        
        Supported queries:
        - "player rankings" / "player points" / "top players" - Player rankings by points
        - "org attendance" / "organization attendance" - Org rankings by attendance
        - "org events" / "organization events" - Org rankings by event count
        - "stats" / "statistics" - Service statistics
        - "formats" / "supported formats" - Available output formats
        - "ranking types" - Available ranking types
        """
        try:
            query_lower = query.lower().strip()
            self.logger.info(f"Tabulator query: {query}")
            
            # Player rankings
            if any(term in query_lower for term in ["player", "points", "top players"]):
                limit = kwargs.get('limit', 50)
                event_filter = kwargs.get('event_filter')
                
                # Get database session
                with self.database.get_session() as session:
                    result = self.tabulate_player_points(session, limit, event_filter)
                    self.stats['tabulations_performed'] += 1
                    self.stats['items_ranked'] += len(result)
                    self.stats['last_operation'] = f"player_points_limit_{limit}"
                    
                    self.logger.info(f"Generated player rankings: {len(result)} players")
                    return result
            
            # Organization attendance rankings  
            elif "org" in query_lower and "attendance" in query_lower:
                limit = kwargs.get('limit')
                
                with self.database.get_session() as session:
                    result = self.tabulate_org_attendance(session, limit)
                    self.stats['tabulations_performed'] += 1
                    self.stats['items_ranked'] += len(result)
                    self.stats['last_operation'] = f"org_attendance_limit_{limit}"
                    
                    self.logger.info(f"Generated org attendance rankings: {len(result)} orgs")
                    return result
            
            # Organization event count rankings
            elif "org" in query_lower and "event" in query_lower:
                limit = kwargs.get('limit')
                
                with self.database.get_session() as session:
                    result = self.tabulate_org_events(session, limit)
                    self.stats['tabulations_performed'] += 1
                    self.stats['items_ranked'] += len(result)
                    self.stats['last_operation'] = f"org_events_limit_{limit}"
                    
                    self.logger.info(f"Generated org event rankings: {len(result)} orgs")
                    return result
            
            # Statistics
            elif any(term in query_lower for term in ["stats", "statistics", "metrics"]):
                uptime = time.time() - self.stats['start_time']
                return {
                    **self.stats,
                    'uptime_seconds': round(uptime, 2),
                    'uptime_minutes': round(uptime / 60, 2),
                    'service_type': 'UnifiedTabulatorService',
                    'prefer_network': self.prefer_network
                }
            
            # Supported formats
            elif any(term in query_lower for term in ["format", "output", "export"]):
                return {
                    'supported_formats': ['text', 'markdown', 'html', 'json'],
                    'description': 'Available output formats for ranking data',
                    'usage': 'tabulator.tell("format_name", ranking_data)'
                }
            
            # Ranking types
            elif "type" in query_lower or "ranking" in query_lower:
                return {
                    'ranking_types': [e.value for e in RankingType],
                    'description': 'Available ranking types',
                    'usage': 'Specify in ask() queries or use tabulate_* methods'
                }
            
            else:
                self.logger.warning(f"Unknown tabulator query: {query}")
                return {
                    'error': 'Unknown query',
                    'supported_queries': [
                        'player rankings', 'org attendance', 'org events',
                        'stats', 'formats', 'ranking types'
                    ],
                    'example': 'tabulator.ask("player rankings limit 25")'
                }
        
        except Exception as e:
            self.stats['errors_encountered'] += 1
            self.error_handler.handle_error(e, {"query": query, "kwargs": kwargs})
            return {'error': str(e), 'type': 'tabulator_query_error'}
    
    def tell(self, format: str, data: Any = None) -> str:
        """
        Format tabulator data for various outputs.
        
        Supported formats:
        - "text" - Plain text ranking list
        - "markdown" - Markdown table format  
        - "html" - HTML table format
        - "json" - JSON data format
        - "discord" - Discord-optimized text format
        - "stats" - Statistics summary
        """
        try:
            format_lower = format.lower().strip()
            self.logger.info(f"Formatting tabulator data as: {format}")
            
            # Handle stats format (no data needed)
            if format_lower in ["stats", "statistics"]:
                stats = self.ask("stats")
                lines = ["📊 Unified Tabulator Statistics:", ""]
                lines.append(f"• Tabulations performed: {stats['tabulations_performed']}")
                lines.append(f"• Items ranked: {stats['items_ranked']}")
                lines.append(f"• Formats generated: {stats['formats_generated']}")
                lines.append(f"• Errors encountered: {stats['errors_encountered']}")
                lines.append(f"• Last operation: {stats['last_operation'] or 'None'}")
                lines.append(f"• Uptime: {stats['uptime_minutes']} minutes")
                lines.append(f"• Network mode: {'Yes' if self.prefer_network else 'No'}")
                return "\n".join(lines)
            
            # Require data for other formats
            if data is None:
                return f"Error: No data provided for {format} formatting"
            
            # Handle ranking data
            if isinstance(data, list) and data and isinstance(data[0], RankedItem):
                result = self.format_rankings(data, format_lower)
                self.stats['formats_generated'] += 1
                return result
            
            # Handle raw data that needs conversion
            elif isinstance(data, list):
                # Try to convert to RankedItem format
                if data and isinstance(data[0], dict):
                    ranked_items = []
                    for i, item in enumerate(data, 1):
                        ranked_items.append(RankedItem(
                            rank=item.get('rank', i),
                            item=item,
                            score=item.get('score', 0),
                            tie=item.get('tie', False),
                            metadata=item
                        ))
                    result = self.format_rankings(ranked_items, format_lower)
                    self.stats['formats_generated'] += 1
                    return result
            
            # JSON fallback for any data
            if format_lower == "json":
                if hasattr(data, 'to_dict'):
                    result = json.dumps(data.to_dict(), indent=2)
                else:
                    result = json.dumps(data, indent=2, default=str)
                self.stats['formats_generated'] += 1
                return result
            
            # Default string representation
            self.stats['formats_generated'] += 1
            return str(data)
        
        except Exception as e:
            self.stats['errors_encountered'] += 1
            self.error_handler.handle_error(e, {"format": format, "data_type": type(data).__name__})
            return f"Error formatting as {format}: {str(e)}"
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform tabulation actions using natural language.
        
        Supported actions:
        - "rank players" / "tabulate players" - Generate player rankings
        - "rank orgs by attendance" - Generate org attendance rankings  
        - "rank orgs by events" - Generate org event rankings
        - "custom ranking" - Perform custom tabulation (requires items and score_func)
        - "reset stats" - Reset statistics
        - "clear cache" - Clear any cached data
        """
        try:
            action_lower = action.lower().strip()
            self.logger.info(f"Performing tabulator action: {action}")
            
            # Player rankings
            if any(term in action_lower for term in ["rank players", "tabulate players", "player points"]):
                limit = kwargs.get('limit', 50)
                event_filter = kwargs.get('event_filter')
                
                with self.database.get_session() as session:
                    result = self.tabulate_player_points(session, limit, event_filter)
                    self.stats['tabulations_performed'] += 1
                    self.stats['items_ranked'] += len(result)
                    self.stats['last_operation'] = f"do_player_rankings_{limit}"
                    
                    self.logger.info(f"Action completed: ranked {len(result)} players")
                    return {
                        'action': action,
                        'result': f"Ranked {len(result)} players by points",
                        'data': result
                    }
            
            # Organization attendance rankings
            elif "org" in action_lower and "attendance" in action_lower:
                limit = kwargs.get('limit')
                
                with self.database.get_session() as session:
                    result = self.tabulate_org_attendance(session, limit)
                    self.stats['tabulations_performed'] += 1
                    self.stats['items_ranked'] += len(result)
                    self.stats['last_operation'] = f"do_org_attendance_{limit}"
                    
                    self.logger.info(f"Action completed: ranked {len(result)} orgs by attendance")
                    return {
                        'action': action,
                        'result': f"Ranked {len(result)} organizations by attendance",
                        'data': result
                    }
            
            # Organization event rankings
            elif "org" in action_lower and "event" in action_lower:
                limit = kwargs.get('limit')
                
                with self.database.get_session() as session:
                    result = self.tabulate_org_events(session, limit)
                    self.stats['tabulations_performed'] += 1
                    self.stats['items_ranked'] += len(result)
                    self.stats['last_operation'] = f"do_org_events_{limit}"
                    
                    self.logger.info(f"Action completed: ranked {len(result)} orgs by events")
                    return {
                        'action': action,
                        'result': f"Ranked {len(result)} organizations by event count",
                        'data': result
                    }
            
            # Custom ranking
            elif "custom" in action_lower:
                items = kwargs.get('items', [])
                score_func = kwargs.get('score_func')
                
                if not items or not score_func:
                    return {
                        'error': 'Custom ranking requires items and score_func parameters',
                        'usage': 'tabulator.do("custom ranking", items=data, score_func=lambda x: x.score)'
                    }
                
                result = self.tabulate(
                    items=items,
                    score_func=score_func,
                    limit=kwargs.get('limit'),
                    metadata_func=kwargs.get('metadata_func')
                )
                
                self.stats['tabulations_performed'] += 1
                self.stats['items_ranked'] += len(result)
                self.stats['last_operation'] = f"do_custom_ranking_{len(items)}"
                
                self.logger.info(f"Action completed: custom ranking of {len(result)} items")
                return {
                    'action': action,
                    'result': f"Custom ranked {len(result)} items",
                    'data': result
                }
            
            # Reset statistics
            elif "reset" in action_lower and "stats" in action_lower:
                old_stats = self.stats.copy()
                self.stats = {
                    'tabulations_performed': 0,
                    'items_ranked': 0,
                    'formats_generated': 0,
                    'errors_encountered': 0,
                    'last_operation': None,
                    'start_time': time.time()
                }
                
                self.logger.info("Tabulator statistics reset")
                return {
                    'action': action,
                    'result': 'Statistics reset',
                    'previous_stats': old_stats,
                    'new_stats': self.stats
                }
            
            # Clear cache
            elif "clear" in action_lower and "cache" in action_lower:
                # Reset service dependencies to force fresh connections
                self._database = None
                self._logger = None
                self._error_handler = None
                self._config = None
                self._points_system = None
                
                self.logger.info("Tabulator cache cleared")
                return {
                    'action': action,
                    'result': 'Service dependencies cache cleared'
                }
            
            else:
                self.logger.warning(f"Unknown tabulator action: {action}")
                return {
                    'error': 'Unknown action',
                    'supported_actions': [
                        'rank players', 'rank orgs by attendance', 'rank orgs by events',
                        'custom ranking', 'reset stats', 'clear cache'
                    ],
                    'example': 'tabulator.do("rank players", limit=25)'
                }
        
        except Exception as e:
            self.stats['errors_encountered'] += 1
            self.error_handler.handle_error(e, {"action": action, "kwargs": kwargs})
            return {'error': str(e), 'type': 'tabulator_action_error'}
    
    def tabulate(self, 
                 items: List[Any],
                 score_func: Callable[[Any], float],
                 sort_desc: bool = True,
                 limit: Optional[int] = None,
                 metadata_func: Optional[Callable[[Any], Dict]] = None) -> List[RankedItem]:
        """
        Universal tabulation method for ANY ranking type.
        
        Args:
            items: List of objects to rank (players, orgs, etc.)
            score_func: Function that returns score for an item
            sort_desc: Sort descending (True) or ascending (False)
            limit: Maximum number of items to return
            metadata_func: Optional function to generate metadata for each item
            
        Returns:
            List of RankedItem objects with proper ranking
            
        Example:
            # Rank players by points
            tabulate(players, lambda p: p.total_points, limit=50)
            
            # Rank orgs by attendance
            tabulate(orgs, lambda o: o.total_attendance, limit=20)
        """
        try:
            start_time = time.time()
            
            # Calculate scores for all items
            scored_items = []
            for item in items:
                try:
                    score = score_func(item)
                    metadata = metadata_func(item) if metadata_func else {}
                    scored_items.append((score, item, metadata))
                except Exception as e:
                    self.logger.warning(f"Error scoring item {item}: {e}")
                    continue
            
            # Sort by score
            scored_items.sort(key=lambda x: x[0], reverse=sort_desc)
            
            # Apply limit if specified
            if limit:
                scored_items = scored_items[:limit]
            
            # Assign ranks with proper tie handling
            ranked_items = []
            prev_score = None
            prev_rank = 0
            ties_count = 0
            
            for i, (score, item, metadata) in enumerate(scored_items, 1):
                if score != prev_score:
                    # New score, update rank
                    rank = i
                    prev_rank = i
                    ties_count = 0
                    is_tie = False
                else:
                    # Same score as previous = tie
                    rank = prev_rank
                    ties_count += 1
                    is_tie = True
                    # Mark previous item as tie too
                    if ranked_items and ranked_items[-1].score == score:
                        ranked_items[-1].tie = True
                
                ranked_items.append(RankedItem(
                    rank=rank,
                    item=item,
                    score=score,
                    tie=is_tie,
                    metadata=metadata
                ))
                prev_score = score
            
            duration = time.time() - start_time
            self.logger.info(f"Tabulated {len(ranked_items)} items in {duration:.3f}s")
            
            return ranked_items
        
        except Exception as e:
            self.error_handler.handle_error(e, {
                "items_count": len(items),
                "sort_desc": sort_desc,
                "limit": limit
            })
            return []
    
    def tabulate_player_points(self, session: Session, limit: int = 50, 
                               event_filter: Optional[str] = None) -> List[RankedItem]:
        """
        Tabulate players by tournament points using SQL aggregation.
        
        This replaces BOTH:
        - database_service.get_player_rankings()
        - polymorphic_queries._get_top_players()
        """
        try:
            from database.tournament_models import Player, TournamentPlacement
            
            # Get points case expression from points system service
            points_case = self.points_system.get_sql_case_expression()
            
            # Build efficient SQL query with aggregation
            query = session.query(
                Player,
                func.sum(points_case).label('total_points'),
                func.count(TournamentPlacement.id).label('event_count'),
                func.sum(case(
                    (TournamentPlacement.placement == 1, 1),
                    else_=0
                )).label('first_places'),
                func.sum(case(
                    (TournamentPlacement.placement <= 3, 1),
                    else_=0
                )).label('top_3s')
            ).join(TournamentPlacement).group_by(Player.id)
            
            # Apply event filter if specified
            if event_filter:
                query = query.filter(TournamentPlacement.event_name.ilike(f'%{event_filter}%'))
            
            # Execute query
            results = query.all()
            
            # Create score and metadata functions
            def score_func(result):
                # Result is a Row object with named attributes
                return float(result.total_points or 0)
            
            def metadata_func(result):
                # Access by attribute name rather than unpacking
                return {
                    'player_id': result.Player.id,
                    'gamer_tag': result.Player.gamer_tag,
                    'name': result.Player.name,
                    'total_points': int(result.total_points or 0),
                    'tournament_count': result.event_count,
                    'first_places': int(result.first_places or 0),
                    'top_3_finishes': int(result.top_3s or 0),
                    'avg_points': round(float(result.total_points or 0) / result.event_count, 2) if result.event_count > 0 else 0
                }
            
            # Use unified tabulation
            return self.tabulate(
                items=results,
                score_func=score_func,
                metadata_func=metadata_func,
                sort_desc=True,
                limit=limit
            )
        
        except Exception as e:
            self.error_handler.handle_error(e, {
                "operation": "tabulate_player_points",
                "limit": limit,
                "event_filter": event_filter
            })
            return []
    
    def tabulate_org_attendance(self, session: Session, limit: Optional[int] = None) -> List[RankedItem]:
        """
        Tabulate organizations by total attendance.
        
        Replaces database_service.get_attendance_rankings()
        """
        try:
            from database.tournament_models import Organization, Tournament
            
            # Get all organizations with their tournaments
            orgs = session.query(Organization).all()
            
            # Calculate attendance for each org
            org_data = []
            for org in orgs:
                # Use the relationship directly (org.tournaments)
                tournaments = org.tournaments if hasattr(org, 'tournaments') else []
                total_attendance = sum(t.num_attendees or 0 for t in tournaments)
                event_count = len(tournaments)
                
                if event_count > 0:  # Only include orgs with events
                    org_data.append({
                        'org': org,
                        'attendance': total_attendance,
                        'events': event_count,
                        'avg_attendance': round(total_attendance / event_count, 1)
                    })
            
            def score_func(data):
                return float(data['attendance'])
            
            def metadata_func(data):
                return {
                    'org_id': data['org'].id,
                    'display_name': data['org'].display_name,
                    'total_attendance': data['attendance'],
                    'tournament_count': data['events'],
                    'avg_attendance': data['avg_attendance']
                }
            
            return self.tabulate(
                items=org_data,
                score_func=score_func,
                metadata_func=metadata_func,
                sort_desc=True,
                limit=limit
            )
        
        except Exception as e:
            self.error_handler.handle_error(e, {
                "operation": "tabulate_org_attendance",
                "limit": limit
            })
            return []
    
    def tabulate_org_events(self, session: Session, limit: Optional[int] = None) -> List[RankedItem]:
        """
        Tabulate organizations by number of events hosted.
        """
        try:
            from database.tournament_models import Organization
            
            orgs = session.query(Organization).all()
            
            # Build org data with event counts
            org_data = []
            for org in orgs:
                tournaments = org.tournaments if hasattr(org, 'tournaments') else []
                if tournaments:
                    org_data.append({
                        'org': org,
                        'event_count': len(tournaments),
                        'total_attendance': sum(t.num_attendees or 0 for t in tournaments)
                    })
            
            def score_func(data):
                return float(data['event_count'])
            
            def metadata_func(data):
                return {
                    'org_id': data['org'].id,
                    'display_name': data['org'].display_name,
                    'tournament_count': data['event_count'],
                    'total_attendance': data['total_attendance']
                }
            
            return self.tabulate(
                items=org_data,
                score_func=score_func,
                metadata_func=metadata_func,
                sort_desc=True,
                limit=limit
            )
        
        except Exception as e:
            self.error_handler.handle_error(e, {
                "operation": "tabulate_org_events", 
                "limit": limit
            })
            return []
    
    def tabulate_custom(self, items: List[Any], score_attr: str, 
                       limit: Optional[int] = None, **kwargs) -> List[RankedItem]:
        """
        Tabulate items using a custom attribute as score.
        
        Args:
            items: List of objects to rank
            score_attr: Name of attribute to use as score
            limit: Maximum number of results
            **kwargs: Additional metadata to include
            
        Example:
            # Rank tournaments by attendance
            tabulate_custom(tournaments, 'num_attendees', limit=10)
        """
        try:
            def score_func(item):
                return float(getattr(item, score_attr, 0))
            
            def metadata_func(item):
                meta = {}
                for key, value in kwargs.items():
                    if callable(value):
                        meta[key] = value(item)
                    else:
                        meta[key] = getattr(item, value, None)
                return meta
            
            return self.tabulate(
                items=items,
                score_func=score_func,
                metadata_func=metadata_func if kwargs else None,
                sort_desc=True,
                limit=limit
            )
        
        except Exception as e:
            self.error_handler.handle_error(e, {
                "operation": "tabulate_custom",
                "score_attr": score_attr,
                "items_count": len(items),
                "limit": limit
            })
            return []
    
    def format_rankings(self, ranked_items: List[RankedItem], 
                       format_type: str = "text") -> str:
        """
        Format rankings for display.
        
        Args:
            ranked_items: List of RankedItem objects
            format_type: "text", "markdown", "html", "json", "discord"
            
        Returns:
            Formatted string representation
        """
        try:
            if format_type == "text":
                lines = []
                for item in ranked_items:
                    tie_marker = "T" if item.tie else " "
                    lines.append(f"{item.rank:3d}{tie_marker} Score: {item.score:8.1f}")
                return "\n".join(lines)
            
            elif format_type == "discord":
                lines = []
                for item in ranked_items:
                    tie_marker = " 🤝" if item.tie else ""
                    lines.append(f"`{item.rank:2d}.` **{item.score:.1f}** points{tie_marker}")
                return "\n".join(lines)
            
            elif format_type == "markdown":
                lines = ["| Rank | Score | Tie |", "|------|-------|-----|"]
                for item in ranked_items:
                    tie = "Yes" if item.tie else "No"
                    lines.append(f"| {item.rank} | {item.score:.1f} | {tie} |")
                return "\n".join(lines)
            
            elif format_type == "html":
                rows = []
                for item in ranked_items:
                    tie_class = ' class="tie"' if item.tie else ''
                    rows.append(f"<tr{tie_class}><td>{item.rank}</td><td>{item.score:.1f}</td></tr>")
                return f"<table><thead><tr><th>Rank</th><th>Score</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"
            
            elif format_type == "json":
                return json.dumps([item.to_dict() for item in ranked_items], indent=2)
            
            else:
                return str(ranked_items)
        
        except Exception as e:
            self.error_handler.handle_error(e, {
                "operation": "format_rankings",
                "format_type": format_type,
                "items_count": len(ranked_items)
            })
            return f"Error formatting as {format_type}: {str(e)}"


# Global service instance with network service wrapper
_tabulator_service = UnifiedTabulatorService()

# Create network wrapper for remote access
tabulator_wrapper = NetworkServiceWrapper(
    service=_tabulator_service,
    service_name="UnifiedTabulator",
    capabilities=[
        "Universal tabulation system for ANY ranking type",
        "Player rankings by tournament points with SQL optimization", 
        "Organization rankings by attendance and event count",
        "Custom ranking with flexible scoring functions",
        "Proper tie handling and rank assignment",
        "Multiple output formats (text, markdown, html, json)",
        "Service locator-based dependencies for distributed operation"
    ]
)

# Expose service methods for direct access
def ask(query: str, **kwargs) -> Any:
    """Query tabulator service using natural language"""
    return _tabulator_service.ask(query, **kwargs)

def tell(format: str, data: Any = None) -> str:
    """Format tabulator data for various outputs"""
    return _tabulator_service.tell(format, data)

def do(action: str, **kwargs) -> Any:
    """Perform tabulation actions using natural language"""
    return _tabulator_service.do(action, **kwargs)

# Direct access to the class for complex usage
UnifiedTabulator = UnifiedTabulatorService


# Convenience functions for backward compatibility
def get_player_rankings(session: Session, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Drop-in replacement for database_service.get_player_rankings()
    """
    try:
        # Use service instance directly for backward compatibility
        ranked = _tabulator_service.tabulate_player_points(session, limit)
        return [item.metadata for item in ranked]
    except Exception as e:
        _tabulator_service.error_handler.handle_error(e, {
            "operation": "get_player_rankings_compatibility",
            "limit": limit
        })
        return []


def get_attendance_rankings(session: Session, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Drop-in replacement for database_service.get_attendance_rankings()
    """
    try:
        ranked = _tabulator_service.tabulate_org_attendance(session, limit)
        results = []
        for item in ranked:
            meta = item.metadata.copy()
            meta['rank'] = item.rank
            results.append(meta)
        return results
    except Exception as e:
        _tabulator_service.error_handler.handle_error(e, {
            "operation": "get_attendance_rankings_compatibility",
            "limit": limit
        })
        return []


if __name__ == "__main__":
    # Test the refactored unified tabulator
    print("Refactored Unified Tabulator Test")
    print("=" * 50)
    
    # Test service methods
    tabulator = UnifiedTabulatorService()
    
    # Test statistics
    stats = tabulator.ask("stats")
    print(f"\nInitial stats: {stats}")
    
    # Test with sample data
    test_items = [
        {'name': 'Player A', 'points': 100},
        {'name': 'Player B', 'points': 85},
        {'name': 'Player C', 'points': 85},  # Tie
        {'name': 'Player D', 'points': 70},
        {'name': 'Player E', 'points': 70},  # Tie
        {'name': 'Player F', 'points': 50},
    ]
    
    ranked = tabulator.tabulate(
        items=test_items,
        score_func=lambda x: x['points'],
        metadata_func=lambda x: {'name': x['name']}
    )
    
    print("\n🏆 Test Rankings:")
    for item in ranked:
        tie = " (TIE)" if item.tie else ""
        print(f"Rank {item.rank}: {item.metadata['name']} - {item.score} points{tie}")
    
    # Test formatting
    print("\n📋 Formatted as Markdown:")
    markdown_output = tabulator.tell("markdown", ranked)
    print(markdown_output)
    
    print("\n💬 Formatted as Discord:")
    discord_output = tabulator.tell("discord", ranked)
    print(discord_output)
    
    # Test service statistics after operations
    final_stats = tabulator.ask("stats")
    print(f"\n📊 Final stats: {final_stats}")
    
    print("\n✅ Refactored Unified Tabulator test complete!")