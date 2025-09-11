#!/usr/bin/env python3
"""
points_system_refactored.py - Points System with Service Locator Pattern

This module provides tournament points calculation using the service locator pattern
for transparent local/network service access.
"""

import sys
import os
from typing import Dict, Optional, List, Any
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from polymorphic_core.service_locator import get_service
from polymorphic_core.network_service_wrapper import NetworkServiceWrapper
from polymorphic_core import announcer


class PointsSystemRefactored:
    """
    Tournament points calculation system using service locator pattern.
    
    Provides points calculation with 3-method pattern:
    - ask(query): Query points information and calculations
    - tell(format, data): Format points data for output  
    - do(action): Perform points calculations and operations
    """
    
    # The ONLY place where placement points are defined
    # Maximum 8 points per tournament
    PLACEMENT_POINTS: Dict[int, int] = {
        1: 8,   # 1st place: 8 points
        2: 6,   # 2nd place: 6 points  
        3: 4,   # 3rd place: 4 points
        4: 3,   # 4th place: 3 points
        5: 2,   # 5th place: 2 points (5th-6th tied)
        6: 2,   # 6th place: 2 points (5th-6th tied)
        7: 1,   # 7th place: 1 point (7th-8th tied)
        8: 1,   # 8th place: 1 point (7th-8th tied)
    }
    
    def __init__(self, prefer_network: bool = False):
        """Initialize with service locator dependencies"""
        self.prefer_network = prefer_network
        self._logger = None
        self._error_handler = None
        self._config = None
        self._database = None
        
        # Points calculation statistics
        self.stats = {
            'calculations_performed': 0,
            'players_calculated': 0,
            'tournaments_processed': 0,
            'total_points_calculated': 0,
            'errors': 0,
            'last_calculation': None,
            'last_calculation_time': None
        }
    
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
    def database(self):
        """Get database service via service locator"""
        if self._database is None:
            self._database = get_service("database", self.prefer_network)
        return self._database
    
    def ask(self, query: str, **kwargs) -> Any:
        """
        Query points system information using natural language.
        
        Args:
            query: Natural language query about points
            **kwargs: Additional query parameters
            
        Returns:
            Relevant points information
        """
        query_lower = query.lower().strip()
        
        try:
            if "status" in query_lower or "health" in query_lower:
                return self._get_service_status()
            elif "stats" in query_lower or "statistics" in query_lower:
                return self.stats
            elif "points for" in query_lower:
                placement = self._extract_placement_from_query(query)
                if placement:
                    return {"placement": placement, "points": self.get_points_for_placement(placement)}
                else:
                    return {"error": "Could not extract placement from query"}
            elif "points system" in query_lower or "system" in query_lower:
                return self._get_points_system_info()
            elif "player points" in query_lower or "calculate" in query_lower:
                player_id = kwargs.get('player_id')
                if player_id:
                    return self._calculate_player_points(player_id)
                else:
                    return {"error": "Player ID required for points calculation"}
            elif "tournament points" in query_lower:
                tournament_id = kwargs.get('tournament_id')
                if tournament_id:
                    return self._get_tournament_points(tournament_id)
                else:
                    return {"error": "Tournament ID required"}
            elif "top players" in query_lower or "leaderboard" in query_lower:
                limit = kwargs.get('limit', 10)
                return self._get_top_players(limit)
            elif "capabilities" in query_lower or "help" in query_lower:
                return self._get_capabilities()
            else:
                self.logger.warning(f"Unknown points query: {query}")
                return {"error": f"Unknown query: {query}", "suggestions": self._get_capabilities()}
                
        except Exception as e:
            error_msg = f"Points query failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg, {"query": query})
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def tell(self, format_type: str, data: Any = None) -> str:
        """
        Format points data for output.
        
        Args:
            format_type: Output format (discord, json, text, html)
            data: Data to format (uses current stats if None)
            
        Returns:
            Formatted string
        """
        if data is None:
            data = self.stats
            
        try:
            if format_type == "discord":
                return self._format_for_discord(data)
            elif format_type == "json":
                import json
                return json.dumps(data, indent=2, default=str)
            elif format_type == "text" or format_type == "console":
                return self._format_for_text(data)
            elif format_type == "html":
                return self._format_for_html(data)
            else:
                return str(data)
                
        except Exception as e:
            error_msg = f"Points formatting failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg, {"format": format_type, "data": data})
            return f"Error formatting data: {error_msg}"
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform points calculations using natural language.
        
        Args:
            action: Natural language action to perform
            **kwargs: Additional action parameters
            
        Returns:
            Action result
        """
        action_lower = action.lower().strip()
        self.stats['last_calculation'] = action
        self.stats['last_calculation_time'] = datetime.now().isoformat()
        
        try:
            if "calculate points" in action_lower or "calculate" in action_lower:
                placements = kwargs.get('placements', [])
                if placements:
                    return self._calculate_total_points(placements)
                else:
                    return {"error": "Placements list required for calculation"}
            elif "breakdown" in action_lower:
                placements = kwargs.get('placements', [])
                if placements:
                    return self._get_points_breakdown(placements)
                else:
                    return {"error": "Placements list required for breakdown"}
            elif "calculate all players" in action_lower or "recalculate all" in action_lower:
                return self._recalculate_all_player_points()
            elif "update player" in action_lower:
                player_id = kwargs.get('player_id')
                if player_id:
                    return self._update_player_points(player_id)
                else:
                    return {"error": "Player ID required for update"}
            elif "validate system" in action_lower or "validate" in action_lower:
                return self._validate_points_system()
            elif "reset stats" in action_lower:
                return self._reset_statistics()
            elif "test" in action_lower:
                return self._test_points_system()
            else:
                self.logger.warning(f"Unknown points action: {action}")
                return {"error": f"Unknown action: {action}", "suggestions": self._get_action_suggestions()}
                
        except Exception as e:
            error_msg = f"Points action failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg, {"action": action, "kwargs": kwargs})
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def get_points_for_placement(self, placement: int) -> int:
        """
        Get points for a specific placement
        
        Args:
            placement: The placement (1st, 2nd, etc.)
            
        Returns:
            Points earned for that placement
        """
        if placement is None:
            return 0
        return self.PLACEMENT_POINTS.get(placement, 0)
    
    def _calculate_total_points(self, placements: List[int]) -> Dict[str, Any]:
        """Calculate total points from a list of placements"""
        try:
            total = 0
            valid_placements = []
            
            for placement in placements:
                if placement is not None:
                    points = self.get_points_for_placement(placement)
                    total += points
                    if points > 0:
                        valid_placements.append(placement)
            
            self.stats['calculations_performed'] += 1
            self.stats['total_points_calculated'] += total
            
            return {
                "success": True,
                "total_points": total,
                "placements_processed": len(placements),
                "valid_placements": len(valid_placements),
                "placements": valid_placements,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Points calculation failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg, {"placements": placements})
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _get_points_breakdown(self, placements: List[int]) -> Dict[str, Any]:
        """Get detailed breakdown of points from placements"""
        try:
            breakdown = {}
            total = 0
            
            for placement in placements:
                if placement is not None:
                    points = self.get_points_for_placement(placement)
                    if points > 0:
                        key = f"{placement}th_place"
                        breakdown[key] = breakdown.get(key, 0) + 1
                        total += points
            
            self.stats['calculations_performed'] += 1
            
            return {
                "success": True,
                "total_points": total,
                "placements": breakdown,
                "events_count": len(placements),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Points breakdown failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg, {"placements": placements})
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _calculate_player_points(self, player_id: str) -> Dict[str, Any]:
        """Calculate points for a specific player"""
        try:
            if not self.database:
                return {"error": "Database service not available"}
            
            # Get player placements from database
            placements_data = self.database.ask(f"player {player_id} placements")
            
            if not placements_data:
                return {"error": f"No placements found for player {player_id}"}
            
            # Extract placement numbers
            placements = []
            if isinstance(placements_data, list):
                placements = [p.get('placement') for p in placements_data if p.get('placement')]
            elif isinstance(placements_data, dict) and 'placements' in placements_data:
                placements = placements_data['placements']
            
            # Calculate points
            result = self._calculate_total_points(placements)
            result["player_id"] = player_id
            result["tournaments_played"] = len(placements)
            
            self.stats['players_calculated'] += 1
            
            return result
            
        except Exception as e:
            error_msg = f"Player points calculation failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg, {"player_id": player_id})
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _get_tournament_points(self, tournament_id: str) -> Dict[str, Any]:
        """Get points distribution for a tournament"""
        try:
            if not self.database:
                return {"error": "Database service not available"}
            
            # Get tournament placements
            placements_data = self.database.ask(f"tournament {tournament_id} placements")
            
            if not placements_data:
                return {"error": f"No placements found for tournament {tournament_id}"}
            
            # Calculate points for each placement
            points_distribution = []
            total_points_awarded = 0
            
            if isinstance(placements_data, list):
                for placement_data in placements_data:
                    placement = placement_data.get('placement')
                    player_id = placement_data.get('player_id')
                    points = self.get_points_for_placement(placement)
                    
                    points_distribution.append({
                        "placement": placement,
                        "player_id": player_id,
                        "points": points
                    })
                    total_points_awarded += points
            
            self.stats['tournaments_processed'] += 1
            
            return {
                "success": True,
                "tournament_id": tournament_id,
                "total_points_awarded": total_points_awarded,
                "placements_count": len(points_distribution),
                "points_distribution": points_distribution,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Tournament points query failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg, {"tournament_id": tournament_id})
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _get_top_players(self, limit: int = 10) -> Dict[str, Any]:
        """Get top players by points"""
        try:
            if not self.database:
                return {"error": "Database service not available"}
            
            # Get top players from database
            top_players_data = self.database.ask(f"top {limit} players by points")
            
            if not top_players_data:
                return {"error": "No player data found"}
            
            return {
                "success": True,
                "top_players": top_players_data,
                "limit": limit,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Top players query failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg, {"limit": limit})
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _recalculate_all_player_points(self) -> Dict[str, Any]:
        """Recalculate points for all players"""
        try:
            if not self.database:
                return {"error": "Database service not available"}
            
            if self.logger:
                self.logger.info("Starting full recalculation of all player points")
            
            # Get all players
            all_players = self.database.ask("all players")
            
            if not all_players:
                return {"error": "No players found"}
            
            calculated = 0
            failed = 0
            total_points = 0
            
            if isinstance(all_players, list):
                for player in all_players:
                    player_id = player.get('id')
                    if player_id:
                        result = self._calculate_player_points(player_id)
                        if result.get('success'):
                            calculated += 1
                            total_points += result.get('total_points', 0)
                        else:
                            failed += 1
            
            return {
                "success": True,
                "players_calculated": calculated,
                "players_failed": failed,
                "total_points_calculated": total_points,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Full recalculation failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _update_player_points(self, player_id: str) -> Dict[str, Any]:
        """Update points for a specific player"""
        try:
            # Calculate current points
            result = self._calculate_player_points(player_id)
            
            if not result.get('success'):
                return result
            
            # Update in database if available
            if self.database:
                update_result = self.database.do("update player points",
                                                player_id=player_id,
                                                total_points=result['total_points'])
                result["database_update"] = update_result
            
            return result
            
        except Exception as e:
            error_msg = f"Player points update failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg, {"player_id": player_id})
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _validate_points_system(self) -> Dict[str, Any]:
        """Validate the points system configuration"""
        try:
            validation_results = {
                "points_defined": len(self.PLACEMENT_POINTS),
                "max_points": max(self.PLACEMENT_POINTS.values()) if self.PLACEMENT_POINTS else 0,
                "min_points": min(self.PLACEMENT_POINTS.values()) if self.PLACEMENT_POINTS else 0,
                "placement_range": list(self.PLACEMENT_POINTS.keys()),
                "total_points_available": sum(self.PLACEMENT_POINTS.values())
            }
            
            # Check for expected FGC standard
            expected_points = [8, 6, 4, 3, 2, 2, 1, 1]
            actual_points = [self.PLACEMENT_POINTS.get(i+1, 0) for i in range(8)]
            
            validation_results["matches_fgc_standard"] = actual_points == expected_points
            validation_results["expected_points"] = expected_points
            validation_results["actual_points"] = actual_points
            
            return {
                "success": True,
                "validation": validation_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Points system validation failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg)
            return {"error": error_msg}
    
    def _test_points_system(self) -> Dict[str, Any]:
        """Test the points system"""
        try:
            if self.logger:
                self.logger.info("Testing points system...")
            
            test_results = {}
            
            # Test basic calculations
            try:
                test_placements = [1, 2, 3, 4, 5, 6, 7, 8, 9]
                calc_result = self._calculate_total_points(test_placements)
                breakdown_result = self._get_points_breakdown(test_placements)
                
                test_results["basic_calculations"] = {
                    "calculation": calc_result,
                    "breakdown": breakdown_result
                }
            except Exception as e:
                test_results["basic_calculations"] = {"error": str(e)}
            
            # Test service dependencies
            try:
                service_tests = {}
                service_tests["logger"] = self.logger is not None
                service_tests["error_handler"] = self.error_handler is not None
                service_tests["config"] = self.config is not None
                service_tests["database"] = self.database is not None
                test_results["services"] = service_tests
            except Exception as e:
                test_results["services"] = {"error": str(e)}
            
            # Test points validation
            try:
                validation_result = self._validate_points_system()
                test_results["validation"] = validation_result
            except Exception as e:
                test_results["validation"] = {"error": str(e)}
            
            return {
                "success": True,
                "test_results": test_results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Points system test failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg)
            return {"error": error_msg}
    
    def _reset_statistics(self) -> Dict[str, Any]:
        """Reset points calculation statistics"""
        try:
            old_stats = self.stats.copy()
            self.stats = {
                'calculations_performed': 0,
                'players_calculated': 0,
                'tournaments_processed': 0,
                'total_points_calculated': 0,
                'errors': 0,
                'last_calculation': None,
                'last_calculation_time': None
            }
            
            return {
                "success": True,
                "message": "Statistics reset",
                "previous_stats": old_stats,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Statistics reset failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg)
            return {"error": error_msg}
    
    def _get_service_status(self) -> Dict[str, Any]:
        """Get current points service status"""
        try:
            return {
                "status": "running",
                "points_system": self.PLACEMENT_POINTS,
                "stats": self.stats,
                "dependencies": {
                    "logger": self.logger is not None,
                    "error_handler": self.error_handler is not None,
                    "config": self.config is not None,
                    "database": self.database is not None
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Status check failed: {e}"}
    
    def _get_points_system_info(self) -> Dict[str, Any]:
        """Get information about the points system"""
        return {
            "system_name": "FGC Tournament Points System",
            "max_points_per_tournament": max(self.PLACEMENT_POINTS.values()),
            "placement_points": self.PLACEMENT_POINTS,
            "description": self._describe_system(),
            "total_possible_points": sum(self.PLACEMENT_POINTS.values())
        }
    
    def _describe_system(self) -> str:
        """Get a human-readable description of the points system"""
        lines = ["Tournament Points System:"]
        for place, points in sorted(self.PLACEMENT_POINTS.items()):
            if place == 1:
                lines.append(f"  1st place: {points} points")
            elif place == 2:
                lines.append(f"  2nd place: {points} points")
            elif place == 3:
                lines.append(f"  3rd place: {points} points")
            else:
                lines.append(f"  {place}th place: {points} point{'s' if points > 1 else ''}")
        lines.append(f"\nMaximum points per tournament: {max(self.PLACEMENT_POINTS.values())}")
        return "\n".join(lines)
    
    def _extract_placement_from_query(self, query: str) -> Optional[int]:
        """Extract placement number from query string"""
        import re
        # Look for patterns like "points for 1st", "points for 3", etc.
        match = re.search(r'(?:points for|place)\s*(\d+)(?:st|nd|rd|th)?', query.lower())
        if match:
            return int(match.group(1))
        return None
    
    def _get_capabilities(self) -> List[str]:
        """Get list of available capabilities"""
        return [
            "points for <placement> - Get points for specific placement",
            "calculate points - Calculate total points from placements list",
            "breakdown - Get detailed points breakdown",
            "player points - Calculate points for specific player",
            "tournament points - Get points distribution for tournament",
            "top players - Get leaderboard by points",
            "calculate all players - Recalculate all player points",
            "validate system - Validate points system configuration"
        ]
    
    def _get_action_suggestions(self) -> List[str]:
        """Get action suggestions"""
        return self._get_capabilities()
    
    def _format_for_discord(self, data: Any) -> str:
        """Format data for Discord output"""
        if isinstance(data, dict):
            if "error" in data:
                return f"❌ **Points Error:** {data['error']}"
            elif "success" in data and data["success"]:
                if "total_points" in data:
                    return f"🏆 **Points Calculated:** {data['total_points']} points from {data.get('placements_processed', 0)} placements"
                else:
                    return f"✅ **Points Success:** Operation completed"
            elif "calculations_performed" in data or "stats" in data:
                stats = data.get("stats", data)
                return f"""🏆 **Points System Status:**
• Calculations: {stats.get('calculations_performed', 0)}
• Players Calculated: {stats.get('players_calculated', 0)}
• Tournaments Processed: {stats.get('tournaments_processed', 0)}
• Total Points Calculated: {stats.get('total_points_calculated', 0)}
• Errors: {stats.get('errors', 0)}
• Last Calculation: {stats.get('last_calculation', 'None')}"""
            elif "placement" in data and "points" in data:
                placement = data['placement']
                points = data['points']
                suffix = "st" if placement == 1 else "nd" if placement == 2 else "rd" if placement == 3 else "th"
                return f"🏆 **{placement}{suffix} Place:** {points} points"
        return f"🏆 Points: {str(data)}"
    
    def _format_for_text(self, data: Any) -> str:
        """Format data for text/console output"""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"{key}:")
                    for subkey, subvalue in value.items():
                        lines.append(f"  {subkey}: {subvalue}")
                elif isinstance(value, list):
                    lines.append(f"{key}: {len(value)} items")
                    for i, item in enumerate(value[:5]):  # Show first 5 items
                        lines.append(f"  {i+1}: {item}")
                    if len(value) > 5:
                        lines.append(f"  ... and {len(value)-5} more")
                else:
                    lines.append(f"{key}: {value}")
            return "\n".join(lines)
        return str(data)
    
    def _format_for_html(self, data: Any) -> str:
        """Format data for HTML output"""
        if isinstance(data, dict):
            html = "<table border='1'>"
            for key, value in data.items():
                if isinstance(value, dict):
                    html += f"<tr><td><strong>{key}</strong></td><td>"
                    html += "<table border='1'>"
                    for subkey, subvalue in value.items():
                        html += f"<tr><td>{subkey}</td><td>{subvalue}</td></tr>"
                    html += "</table></td></tr>"
                else:
                    html += f"<tr><td><strong>{key}</strong></td><td>{value}</td></tr>"
            html += "</table>"
            return html
        return f"<pre>{str(data)}</pre>"


# Convenience functions for backward compatibility
def get_points(placement: int) -> int:
    """Get points for a placement"""
    return points_system_refactored.get_points_for_placement(placement)


def get_points_dict() -> Dict[int, int]:
    """Get the complete points dictionary"""
    return PointsSystemRefactored.PLACEMENT_POINTS.copy()


def describe() -> str:
    """Describe the points system"""
    return points_system_refactored._describe_system()


# Export the main constant for backward compatibility
PLACEMENT_POINTS = PointsSystemRefactored.PLACEMENT_POINTS


# Announce service capabilities
announcer.announce(
    "Points System (Refactored)",
    [
        "Tournament points calculation with 3-method pattern",
        "ask('points for 1st') - Query points for placements",
        "tell('discord', data) - Format points data for output",
        "do('calculate points') - Perform points calculations",
        "FGC standard points distribution (8-6-4-3-2-2-1-1)",
        "Uses service locator for transparent local/network operation"
    ],
    [
        "points.ask('points for 1st')",
        "points.do('calculate points', placements=[1,2,3])",
        "points.do('player points', player_id='123')",
        "points.tell('discord')"
    ]
)

# Singleton instance
points_system_refactored = PointsSystemRefactored()

# Create network service wrapper for remote access
if __name__ != "__main__":
    try:
        wrapper = NetworkServiceWrapper(
            service=points_system_refactored,
            service_name="points_system_refactored",
            port_range=(9600, 9700)
        )
        # Auto-start network service in background
        wrapper.start_service_thread()
    except Exception as e:
        # Gracefully handle if network service fails
        pass


if __name__ == "__main__":
    # Test the refactored points system
    print("🧪 Testing Refactored Points System")
    
    # Test local-first service
    print("\n1. Testing points system:")
    points_service = PointsSystemRefactored(prefer_network=False)
    
    # Test points for placement
    print("\n2. Testing points queries:")
    points_result = points_service.ask("points for 1st")
    print(f"1st place: {points_service.tell('text', points_result)}")
    
    points_result = points_service.ask("points for 4th")
    print(f"4th place: {points_service.tell('text', points_result)}")
    
    # Test calculation
    print("\n3. Testing calculations:")
    calc_result = points_service.do("calculate points", placements=[1, 3, 5, 7, 2])
    print(f"Calculation: {points_service.tell('text', calc_result)}")
    
    # Test breakdown
    print("\n4. Testing breakdown:")
    breakdown_result = points_service.do("breakdown", placements=[1, 3, 5, 7, 2])
    print(f"Breakdown: {points_service.tell('text', breakdown_result)}")
    
    # Test system info
    print("\n5. Testing system info:")
    system_info = points_service.ask("points system")
    print(f"System: {points_service.tell('text', system_info)}")
    
    print("\n✅ Refactored points system test complete!")
    print("💡 Same code works with local or network services!")
    print("🔥 Points system with service locator pattern!")