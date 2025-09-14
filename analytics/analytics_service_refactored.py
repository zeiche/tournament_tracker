#!/usr/bin/env python3
"""
analytics_service_refactored.py - Unified Analytics Service with Service Locator Pattern

This module consolidates all tournament analytics functionality using the service locator pattern
for transparent local/network service access.
"""

import sys
import os
import json
import subprocess
from typing import Optional, List, Any, Dict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from polymorphic_core.service_locator import get_service
from polymorphic_core.network_service_wrapper import NetworkServiceWrapper
from polymorphic_core import announcer
from utils.dynamic_switches import announce_switch


class AnalyticsServiceRefactored:
    """
    Unified analytics service using service locator pattern.
    
    Provides analytics generation with 3-method pattern:
    - ask(query): Query analytics information and data
    - tell(format, data): Format analytics data for output  
    - do(action): Generate analytics and perform operations
    """
    
    def __init__(self, prefer_network: bool = False):
        """Initialize with service locator dependencies"""
        self.prefer_network = prefer_network
        self._logger = None
        self._error_handler = None
        self._config = None
        self._database = None
        
        # Analytics generation statistics
        self.stats = {
            'heatmaps_generated': 0,
            'reports_generated': 0,
            'player_analyses': 0,
            'advanced_analytics': 0,
            'errors': 0,
            'last_analytics': None,
            'last_analytics_time': None,
            'total_analytics': 0
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
        Query analytics service information using natural language.
        
        Args:
            query: Natural language query about analytics
            **kwargs: Additional query parameters
            
        Returns:
            Relevant analytics information
        """
        query_lower = query.lower().strip()
        
        try:
            if "status" in query_lower or "health" in query_lower:
                return self._get_service_status()
            elif "stats" in query_lower or "statistics" in query_lower:
                return self.stats
            elif "history" in query_lower or "recent" in query_lower:
                return self._get_analytics_history()
            elif "available" in query_lower or "types" in query_lower:
                return self._get_available_analytics()
            elif "last analytics" in query_lower or "latest" in query_lower:
                return self._get_last_analytics_info()
            elif "tournament data" in query_lower or "data" in query_lower:
                return self._get_tournament_data()
            elif "player data" in query_lower or "players" in query_lower:
                return self._get_player_data()
            elif "dependencies" in query_lower:
                return self._check_dependencies()
            elif "capabilities" in query_lower or "help" in query_lower:
                return self._get_capabilities()
            else:
                self.logger.warning(f"Unknown analytics query: {query}")
                return {"error": f"Unknown query: {query}", "suggestions": self._get_capabilities()}
                
        except Exception as e:
            error_msg = f"Analytics query failed: {e}"
            self.error_handler.handle_error(error_msg, {"query": query})
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def tell(self, format_type: str, data: Any = None) -> str:
        """
        Format analytics data for output.
        
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
                return json.dumps(data, indent=2, default=str)
            elif format_type == "text" or format_type == "console":
                return self._format_for_text(data)
            elif format_type == "html":
                return self._format_for_html(data)
            else:
                return str(data)
                
        except Exception as e:
            error_msg = f"Analytics formatting failed: {e}"
            self.error_handler.handle_error(error_msg, {"format": format_type, "data": data})
            return f"Error formatting data: {error_msg}"
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform analytics operations using natural language.
        
        Args:
            action: Natural language action to perform
            **kwargs: Additional action parameters
            
        Returns:
            Action result
        """
        action_lower = action.lower().strip()
        self.stats['last_analytics'] = action
        self.stats['last_analytics_time'] = datetime.now().isoformat()
        
        try:
            if "heatmap" in action_lower:
                if "advanced" in action_lower:
                    return self._generate_advanced_heatmap(**kwargs)
                elif "interactive" in action_lower:
                    return self._generate_interactive_heatmap(**kwargs)
                else:
                    return self._generate_static_heatmap(**kwargs)
            elif "tournament report" in action_lower or "report" in action_lower:
                return self._generate_tournament_report(**kwargs)
            elif "player analysis" in action_lower or "top players" in action_lower:
                return self._generate_player_analysis(**kwargs)
            elif "all analytics" in action_lower or action_lower == "all":
                return self._generate_all_analytics(**kwargs)
            elif "clear history" in action_lower or "reset stats" in action_lower:
                return self._clear_statistics()
            elif "test" in action_lower:
                return self._test_analytics_system()
            elif "install dependencies" in action_lower or "setup" in action_lower:
                return self._install_dependencies()
            else:
                self.logger.warning(f"Unknown analytics action: {action}")
                return {"error": f"Unknown action: {action}", "suggestions": self._get_action_suggestions()}
                
        except Exception as e:
            error_msg = f"Analytics action failed: {e}"
            self.error_handler.handle_error(error_msg, {"action": action, "kwargs": kwargs})
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _generate_static_heatmap(self, **kwargs) -> Dict[str, Any]:
        """Generate static heatmap using tournament_heatmap.py"""
        try:
            self.logger.info("Generating static tournament heatmap...")
            
            output_file = kwargs.get('output_file', 'tournament_heatmap.png')
            dpi = kwargs.get('dpi', 150)
            use_map_background = kwargs.get('use_map_background', True)
            
            result = subprocess.run(
                [sys.executable, 'tournament_domain/analytics/tournament_heatmap.py', 
                 '--output', output_file, '--dpi', str(dpi)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            self.stats['heatmaps_generated'] += 1
            self.stats['total_analytics'] += 1
            
            return {
                "success": True,
                "type": "static_heatmap",
                "output_file": output_file,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
        except subprocess.TimeoutExpired:
            error_msg = "Static heatmap generation timed out"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg, "type": "static_heatmap"}
        except Exception as e:
            error_msg = f"Static heatmap generation failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg, "type": "static_heatmap"}
    
    def _generate_interactive_heatmap(self, **kwargs) -> Dict[str, Any]:
        """Generate interactive heatmap"""
        try:
            self.logger.info("Generating interactive tournament heatmap...")
            
            output_file = kwargs.get('output_file', 'tournament_heatmap_interactive.html')
            
            # Call the interactive heatmap generation
            # This would integrate with the existing tournament_heatmap.py functionality
            if self.database:
                tournaments = self.database.ask("tournaments with coordinates")
                
                if tournaments:
                    # Generate interactive HTML map
                    html_content = self._create_interactive_map(tournaments, output_file)
                    
                    self.stats['heatmaps_generated'] += 1
                    self.stats['total_analytics'] += 1
                    
                    return {
                        "success": True,
                        "type": "interactive_heatmap",
                        "output_file": output_file,
                        "tournament_count": len(tournaments) if isinstance(tournaments, list) else 0,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {"error": "No tournament data found for heatmap"}
            else:
                return {"error": "Database service not available"}
                
        except Exception as e:
            error_msg = f"Interactive heatmap generation failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg, "type": "interactive_heatmap"}
    
    def _generate_advanced_heatmap(self, **kwargs) -> Dict[str, Any]:
        """Generate advanced heatmap using heatmap_advanced.py"""
        try:
            self.logger.info("Generating advanced tournament heatmap...")
            
            result = subprocess.run(
                [sys.executable, 'tournament_domain/analytics/heatmap_advanced.py'],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for advanced analytics
            )
            
            self.stats['advanced_analytics'] += 1
            self.stats['total_analytics'] += 1
            
            return {
                "success": True,
                "type": "advanced_heatmap",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
        except subprocess.TimeoutExpired:
            error_msg = "Advanced heatmap generation timed out"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg, "type": "advanced_heatmap"}
        except Exception as e:
            error_msg = f"Advanced heatmap generation failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg, "type": "advanced_heatmap"}
    
    def _generate_tournament_report(self, **kwargs) -> Dict[str, Any]:
        """Generate tournament report"""
        try:
            self.logger.info("Generating tournament report...")
            
            result = subprocess.run(
                [sys.executable, 'tournament_domain/analytics/tournament_report.py'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            self.stats['reports_generated'] += 1
            self.stats['total_analytics'] += 1
            
            return {
                "success": True,
                "type": "tournament_report",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
        except subprocess.TimeoutExpired:
            error_msg = "Tournament report generation timed out"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg, "type": "tournament_report"}
        except Exception as e:
            error_msg = f"Tournament report generation failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg, "type": "tournament_report"}
    
    def _generate_player_analysis(self, **kwargs) -> Dict[str, Any]:
        """Generate player analysis"""
        try:
            self.logger.info("Generating player analysis...")
            
            limit = kwargs.get('limit', 50)
            
            result = subprocess.run(
                [sys.executable, 'tournament_domain/analytics/show_top_players.py', '--limit', str(limit)],
                capture_output=True,
                text=True,
                timeout=180  # 3 minute timeout
            )
            
            self.stats['player_analyses'] += 1
            self.stats['total_analytics'] += 1
            
            return {
                "success": True,
                "type": "player_analysis",
                "limit": limit,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
        except subprocess.TimeoutExpired:
            error_msg = "Player analysis generation timed out"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg, "type": "player_analysis"}
        except Exception as e:
            error_msg = f"Player analysis generation failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg, "type": "player_analysis"}
    
    def _generate_all_analytics(self, **kwargs) -> Dict[str, Any]:
        """Generate all analytics"""
        try:
            self.logger.info("Generating all analytics...")
            
            results = []
            
            # Generate tournament report first (fastest)
            report_result = self._generate_tournament_report(**kwargs)
            results.append(report_result)
            
            # Generate player analysis
            player_result = self._generate_player_analysis(**kwargs)
            results.append(player_result)
            
            # Generate static heatmap
            heatmap_result = self._generate_static_heatmap(**kwargs)
            results.append(heatmap_result)
            
            # Generate advanced heatmap (slowest)
            advanced_result = self._generate_advanced_heatmap(**kwargs)
            results.append(advanced_result)
            
            # Count successes
            successes = sum(1 for r in results if r.get("success", False))
            errors = len(results) - successes
            
            return {
                "success": successes > 0,
                "type": "all_analytics",
                "total_analytics": len(results),
                "successful": successes,
                "failed": errors,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"All analytics generation failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg, "type": "all_analytics"}
    
    def _create_interactive_map(self, tournaments: List[Dict], output_file: str) -> str:
        """Create interactive HTML map using folium"""
        try:
            # Basic HTML map generation
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Tournament Heatmap</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
</head>
<body>
    <div id="map" style="width: 100%; height: 500px;"></div>
    <script>
        var map = L.map('map').setView([34.0522, -118.2437], 8);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);
        
        var tournaments = {json.dumps(tournaments)};
        tournaments.forEach(function(tournament) {{
            if (tournament.lat && tournament.lng) {{
                L.marker([tournament.lat, tournament.lng])
                    .addTo(map)
                    .bindPopup(tournament.name || 'Unknown Tournament');
            }}
        }});
    </script>
</body>
</html>
"""
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            return html_content
            
        except Exception as e:
            raise Exception(f"Interactive map creation failed: {e}")
    
    def _install_dependencies(self) -> Dict[str, Any]:
        """Install required analytics dependencies"""
        try:
            self.logger.info("Installing analytics dependencies...")
            
            dependencies = [
                'matplotlib',
                'scipy',
                'contextily',
                'folium',
                'numpy'
            ]
            
            results = []
            for dep in dependencies:
                try:
                    result = subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', '--break-system-packages', dep],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    results.append({
                        "dependency": dep,
                        "success": result.returncode == 0,
                        "output": result.stdout if result.returncode == 0 else result.stderr
                    })
                except Exception as e:
                    results.append({
                        "dependency": dep,
                        "success": False,
                        "error": str(e)
                    })
            
            successful = sum(1 for r in results if r["success"])
            
            return {
                "success": successful > 0,
                "total_dependencies": len(dependencies),
                "successful": successful,
                "failed": len(dependencies) - successful,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Dependency installation failed: {e}"
            self.error_handler.handle_error(error_msg)
            return {"error": error_msg}
    
    def _test_analytics_system(self) -> Dict[str, Any]:
        """Test the analytics system"""
        try:
            self.logger.info("Testing analytics system...")
            
            test_results = {}
            
            # Test dependencies
            try:
                dependencies = ['matplotlib', 'scipy', 'numpy', 'folium']
                dep_results = {}
                for dep in dependencies:
                    try:
                        __import__(dep)
                        dep_results[dep] = {"available": True}
                    except ImportError:
                        dep_results[dep] = {"available": False, "error": "Not installed"}
                test_results["dependencies"] = dep_results
            except Exception as e:
                test_results["dependencies"] = {"error": str(e)}
            
            # Test database connectivity
            try:
                if self.database:
                    db_test = self.database.ask("health")
                    test_results["database"] = {"status": "ok", "result": db_test}
                else:
                    test_results["database"] = {"status": "unavailable"}
            except Exception as e:
                test_results["database"] = {"status": "error", "error": str(e)}
            
            # Test file system access
            try:
                test_files = [
                    'tournament_domain/analytics/tournament_heatmap.py',
                    'tournament_domain/analytics/tournament_report.py',
                    'tournament_domain/analytics/show_top_players.py',
                    'tournament_domain/analytics/heatmap_advanced.py'
                ]
                
                file_tests = {}
                for file_path in test_files:
                    file_tests[file_path] = os.path.exists(file_path)
                
                test_results["files"] = file_tests
            except Exception as e:
                test_results["files"] = {"error": str(e)}
            
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
            
            return {
                "success": True,
                "test_results": test_results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Analytics system test failed: {e}"
            self.error_handler.handle_error(error_msg)
            return {"error": error_msg}
    
    def _clear_statistics(self) -> Dict[str, Any]:
        """Clear analytics statistics"""
        try:
            old_stats = self.stats.copy()
            self.stats = {
                'heatmaps_generated': 0,
                'reports_generated': 0,
                'player_analyses': 0,
                'advanced_analytics': 0,
                'errors': 0,
                'last_analytics': None,
                'last_analytics_time': None,
                'total_analytics': 0
            }
            
            return {
                "success": True,
                "message": "Statistics cleared",
                "previous_stats": old_stats,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Statistics clear failed: {e}"
            self.error_handler.handle_error(error_msg)
            return {"error": error_msg}
    
    def _get_service_status(self) -> Dict[str, Any]:
        """Get current analytics service status"""
        try:
            return {
                "status": "running",
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
    
    def _get_analytics_history(self) -> Dict[str, Any]:
        """Get analytics generation history"""
        return {
            "last_analytics": self.stats.get('last_analytics'),
            "last_analytics_time": self.stats.get('last_analytics_time'),
            "total_analytics": self.stats.get('total_analytics', 0),
            "breakdown": {
                "heatmaps_generated": self.stats.get('heatmaps_generated', 0),
                "reports_generated": self.stats.get('reports_generated', 0),
                "player_analyses": self.stats.get('player_analyses', 0),
                "advanced_analytics": self.stats.get('advanced_analytics', 0)
            },
            "errors": self.stats.get('errors', 0)
        }
    
    def _get_available_analytics(self) -> List[Dict[str, str]]:
        """Get list of available analytics types"""
        return [
            {"type": "heatmap", "description": "Static tournament location heatmap"},
            {"type": "interactive heatmap", "description": "Interactive HTML map"},
            {"type": "advanced heatmap", "description": "Advanced heatmap with multiple styles"},
            {"type": "tournament report", "description": "Comprehensive tournament analysis"},
            {"type": "player analysis", "description": "Top players and rankings"},
            {"type": "all analytics", "description": "Generate all analytics"}
        ]
    
    def _get_last_analytics_info(self) -> Dict[str, Any]:
        """Get information about the last generated analytics"""
        return {
            "last_analytics": self.stats.get('last_analytics', 'None'),
            "last_analytics_time": self.stats.get('last_analytics_time', 'Never'),
            "total_analytics": self.stats.get('total_analytics', 0)
        }
    
    def _get_tournament_data(self) -> Dict[str, Any]:
        """Get tournament data for analytics"""
        if self.database:
            try:
                tournaments = self.database.ask("tournaments with coordinates")
                return {
                    "success": True,
                    "data": tournaments,
                    "count": len(tournaments) if isinstance(tournaments, list) else 0
                }
            except Exception as e:
                return {"error": f"Tournament data query failed: {e}"}
        else:
            return {"error": "Database service not available"}
    
    def _get_player_data(self) -> Dict[str, Any]:
        """Get player data for analytics"""
        if self.database:
            try:
                players = self.database.ask("top players")
                return {
                    "success": True,
                    "data": players,
                    "count": len(players) if isinstance(players, list) else 0
                }
            except Exception as e:
                return {"error": f"Player data query failed: {e}"}
        else:
            return {"error": "Database service not available"}
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check analytics dependencies"""
        dependencies = {
            'matplotlib': False,
            'scipy': False,
            'numpy': False,
            'folium': False,
            'contextily': False
        }
        
        for dep in dependencies:
            try:
                __import__(dep)
                dependencies[dep] = True
            except ImportError:
                dependencies[dep] = False
        
        installed_count = sum(dependencies.values())
        
        return {
            "dependencies": dependencies,
            "installed": installed_count,
            "total": len(dependencies),
            "all_installed": installed_count == len(dependencies)
        }
    
    def _get_capabilities(self) -> List[str]:
        """Get list of available capabilities"""
        return [
            "heatmap - Generate static tournament heatmap",
            "interactive heatmap - Generate interactive HTML map",
            "advanced heatmap - Generate advanced heatmap with multiple styles",
            "tournament report - Generate comprehensive tournament analysis",
            "player analysis - Generate top players analysis",
            "all analytics - Generate all analytics",
            "test - Test analytics system",
            "install dependencies - Install required packages"
        ]
    
    def _get_action_suggestions(self) -> List[str]:
        """Get action suggestions"""
        return self._get_capabilities()
    
    def _format_for_discord(self, data: Any) -> str:
        """Format data for Discord output"""
        if isinstance(data, dict):
            if "error" in data:
                return f"❌ **Analytics Error:** {data['error']}"
            elif "success" in data and data["success"]:
                analytics_type = data.get("type", "unknown").replace('_', ' ').title()
                return f"📊 **Analytics Generated:** {analytics_type}"
            elif "stats" in data or "heatmaps_generated" in data:
                stats = data.get("stats", data)
                return f"""📊 **Analytics Service Status:**
• Heatmaps Generated: {stats.get('heatmaps_generated', 0)}
• Reports Generated: {stats.get('reports_generated', 0)}
• Player Analyses: {stats.get('player_analyses', 0)}
• Advanced Analytics: {stats.get('advanced_analytics', 0)}
• Total Analytics: {stats.get('total_analytics', 0)}
• Errors: {stats.get('errors', 0)}
• Last Analytics: {stats.get('last_analytics', 'None')}"""
        return f"📊 Analytics: {str(data)}"
    
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


# Announce service capabilities
announcer.announce(
    "Analytics Service (Refactored)",
    [
        "Tournament analytics with 3-method pattern",
        "ask('tournament data') - Query analytics data and information",
        "tell('discord', data) - Format analytics data for output",
        "do('heatmap') - Generate analytics and perform operations",
        "Consolidated: heatmaps, reports, player analysis, advanced analytics",
        "Uses service locator for transparent local/network operation"
    ],
    [
        "analytics.ask('status')",
        "analytics.do('heatmap')",
        "analytics.do('tournament report')",
        "analytics.tell('discord')"
    ]
)

# Singleton instance
analytics_service_refactored = AnalyticsServiceRefactored()

# Create network service wrapper for remote access
if __name__ != "__main__":
    try:
        wrapper = NetworkServiceWrapper(
            service=analytics_service_refactored,
            service_name="analytics_refactored",
            port_range=(9400, 9500)
        )
        # Auto-start network service in background
        wrapper.start_service_thread()
    except Exception as e:
        # Gracefully handle if network service fails
        pass


def start_analytics_service_refactored(args=None):
    """Handler for --analytics switch with service locator pattern"""
    
    # Determine analytics type from arguments
    analytics_type = "heatmap"  # default
    
    if hasattr(args, 'analytics') and args.analytics:
        analytics_type = args.analytics
    
    analytics_service_refactored.logger.info(f"Starting analytics generation: {analytics_type}")
    
    try:
        if analytics_type == "heatmap":
            result = analytics_service_refactored.do("heatmap")
        elif analytics_type == "interactive":
            result = analytics_service_refactored.do("interactive heatmap")
        elif analytics_type == "advanced":
            result = analytics_service_refactored.do("advanced heatmap")
        elif analytics_type == "report":
            result = analytics_service_refactored.do("tournament report")
        elif analytics_type == "players":
            result = analytics_service_refactored.do("player analysis")
        elif analytics_type == "all":
            result = analytics_service_refactored.do("all analytics")
        else:
            analytics_service_refactored.logger.warning(f"Unknown analytics type: {analytics_type}. Using heatmap.")
            result = analytics_service_refactored.do("heatmap")
        
        # Format result for output
        if result:
            formatted = analytics_service_refactored.tell("text", result)
            print(formatted)
        
        return result
            
    except Exception as e:
        error_msg = f"Analytics generation failed: {e}"
        analytics_service_refactored.error_handler.handle_error(error_msg, {"analytics_type": analytics_type})
        print(f"Error: {error_msg}")
        return None


# Register the refactored switch (commented out for now to avoid conflicts)
announce_switch(
    flag="--analytics",
    help="START analytics generation (heatmap|stats|identify|all)",
    handler=start_analytics_service_refactored,
    action="store",
    nargs="?",
    const="heatmap",
    metavar="TYPE"
)