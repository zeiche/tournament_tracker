#!/usr/bin/env python3
"""
report_service_refactored.py - Unified Report Service with Service Locator Pattern

This module consolidates all reporting functionality using the service locator pattern
for transparent local/network service access.
"""

import sys
import os
import subprocess
from typing import Optional, List, Any, Dict
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from polymorphic_core.service_locator import get_service
from polymorphic_core.network_service_wrapper import NetworkServiceWrapper
from polymorphic_core import announcer
from utils.dynamic_switches import announce_switch


class ReportServiceRefactored:
    """
    Unified report service using service locator pattern.
    
    Provides report generation with 3-method pattern:
    - ask(query): Query report information and status
    - tell(format, data): Format report data for output  
    - do(action): Generate reports and perform operations
    """
    
    def __init__(self, prefer_network: bool = False):
        """Initialize with service locator dependencies"""
        self.prefer_network = prefer_network
        self._logger = None
        self._error_handler = None
        self._config = None
        self._database = None
        
        # Report generation statistics
        self.stats = {
            'console_reports': 0,
            'heatmaps_generated': 0,
            'stats_queries': 0,
            'all_reports': 0,
            'errors': 0,
            'last_report': None,
            'last_report_time': None,
            'total_reports': 0
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
        Query report service information using natural language.
        
        Args:
            query: Natural language query about reports
            **kwargs: Additional query parameters
            
        Returns:
            Relevant report information
        """
        query_lower = query.lower().strip()
        
        try:
            if "status" in query_lower or "health" in query_lower:
                return self._get_service_status()
            elif "stats" in query_lower or "statistics" in query_lower:
                return self.stats
            elif "history" in query_lower or "recent" in query_lower:
                return self._get_report_history()
            elif "available" in query_lower or "types" in query_lower:
                return self._get_available_reports()
            elif "last report" in query_lower or "latest" in query_lower:
                return self._get_last_report_info()
            elif "database stats" in query_lower or "db stats" in query_lower:
                return self._get_database_statistics()
            elif "capabilities" in query_lower or "help" in query_lower:
                return self._get_capabilities()
            else:
                self.logger.warning(f"Unknown report query: {query}")
                return {"error": f"Unknown query: {query}", "suggestions": self._get_capabilities()}
                
        except Exception as e:
            error_msg = f"Report query failed: {e}"
            self.error_handler.handle_error(error_msg, {"query": query})
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def tell(self, format_type: str, data: Any = None) -> str:
        """
        Format report data for output.
        
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
            error_msg = f"Report formatting failed: {e}"
            self.error_handler.handle_error(error_msg, {"format": format_type, "data": data})
            return f"Error formatting data: {error_msg}"
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform report operations using natural language.
        
        Args:
            action: Natural language action to perform
            **kwargs: Additional action parameters
            
        Returns:
            Action result
        """
        action_lower = action.lower().strip()
        self.stats['last_report'] = action
        self.stats['last_report_time'] = datetime.now().isoformat()
        
        try:
            if "console report" in action_lower or action_lower == "console":
                return self._generate_console_report()
            elif "heatmap" in action_lower:
                return self._generate_heatmap()
            elif "stats" in action_lower and "show" in action_lower:
                return self._show_stats()
            elif "database stats" in action_lower or "db stats" in action_lower:
                return self._get_database_statistics()
            elif "all reports" in action_lower or action_lower == "all":
                return self._generate_all_reports()
            elif "clear history" in action_lower or "reset stats" in action_lower:
                return self._clear_statistics()
            elif "test" in action_lower:
                return self._test_report_system()
            else:
                self.logger.warning(f"Unknown report action: {action}")
                return {"error": f"Unknown action: {action}", "suggestions": self._get_action_suggestions()}
                
        except Exception as e:
            error_msg = f"Report action failed: {e}"
            self.error_handler.handle_error(error_msg, {"action": action, "kwargs": kwargs})
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _generate_console_report(self) -> Dict[str, Any]:
        """Generate console report"""
        try:
            self.logger.info("Generating console report...")
            
            # Try to run the report script
            result = subprocess.run(
                [sys.executable, 'tournament_domain/analytics/tournament_report.py'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            self.stats['console_reports'] += 1
            self.stats['total_reports'] += 1
            
            return {
                "success": True,
                "type": "console_report",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
        except subprocess.TimeoutExpired:
            error_msg = "Console report generation timed out"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg, "type": "console_report"}
        except Exception as e:
            error_msg = f"Console report generation failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg, "type": "console_report"}
    
    def _generate_heatmap(self) -> Dict[str, Any]:
        """Generate heatmap visualization"""
        try:
            self.logger.info("Generating heatmap...")
            
            result = subprocess.run(
                [sys.executable, 'tournament_domain/analytics/tournament_heatmap.py'],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout for heatmap
            )
            
            self.stats['heatmaps_generated'] += 1
            self.stats['total_reports'] += 1
            
            return {
                "success": True,
                "type": "heatmap",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
        except subprocess.TimeoutExpired:
            error_msg = "Heatmap generation timed out"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg, "type": "heatmap"}
        except Exception as e:
            error_msg = f"Heatmap generation failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg, "type": "heatmap"}
    
    def _show_stats(self) -> Dict[str, Any]:
        """Show database statistics"""
        try:
            self.logger.info("Showing database statistics...")
            
            result = subprocess.run(
                [sys.executable, 'utils/database_service.py', '--stats'],
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            self.stats['stats_queries'] += 1
            self.stats['total_reports'] += 1
            
            return {
                "success": True,
                "type": "database_stats",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
        except subprocess.TimeoutExpired:
            error_msg = "Database stats query timed out"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg, "type": "database_stats"}
        except Exception as e:
            error_msg = f"Database stats failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg, "type": "database_stats"}
    
    def _generate_all_reports(self) -> Dict[str, Any]:
        """Generate all reports"""
        try:
            self.logger.info("Generating all reports...")
            
            results = []
            
            # Generate stats first (fastest)
            stats_result = self._show_stats()
            results.append(stats_result)
            
            # Generate console report
            console_result = self._generate_console_report()
            results.append(console_result)
            
            # Generate heatmap (slowest)
            heatmap_result = self._generate_heatmap()
            results.append(heatmap_result)
            
            self.stats['all_reports'] += 1
            
            # Count successes
            successes = sum(1 for r in results if r.get("success", False))
            errors = len(results) - successes
            
            return {
                "success": successes > 0,
                "type": "all_reports",
                "total_reports": len(results),
                "successful": successes,
                "failed": errors,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"All reports generation failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg, "type": "all_reports"}
    
    def _get_database_statistics(self) -> Dict[str, Any]:
        """Get database statistics via service locator"""
        try:
            if self.database:
                # Use database service to get stats
                db_stats = self.database.ask("statistics")
                return {
                    "success": True,
                    "database_stats": db_stats,
                    "source": "service_locator",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Fallback to direct script execution
                return self._show_stats()
        except Exception as e:
            error_msg = f"Database statistics retrieval failed: {e}"
            self.error_handler.handle_error(error_msg)
            return {"error": error_msg, "type": "database_stats"}
    
    def _test_report_system(self) -> Dict[str, Any]:
        """Test the report system"""
        try:
            self.logger.info("Testing report system...")
            
            test_results = {}
            
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
                    'tournament_domain/analytics/tournament_report.py',
                    'tournament_domain/analytics/tournament_heatmap.py',
                    'utils/database_service.py'
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
                test_results["services"] = service_tests
            except Exception as e:
                test_results["services"] = {"error": str(e)}
            
            return {
                "success": True,
                "test_results": test_results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Report system test failed: {e}"
            self.error_handler.handle_error(error_msg)
            return {"error": error_msg}
    
    def _clear_statistics(self) -> Dict[str, Any]:
        """Clear report statistics"""
        try:
            old_stats = self.stats.copy()
            self.stats = {
                'console_reports': 0,
                'heatmaps_generated': 0,
                'stats_queries': 0,
                'all_reports': 0,
                'errors': 0,
                'last_report': None,
                'last_report_time': None,
                'total_reports': 0
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
        """Get current report service status"""
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
    
    def _get_report_history(self) -> Dict[str, Any]:
        """Get report generation history"""
        return {
            "last_report": self.stats.get('last_report'),
            "last_report_time": self.stats.get('last_report_time'),
            "total_reports": self.stats.get('total_reports', 0),
            "breakdown": {
                "console_reports": self.stats.get('console_reports', 0),
                "heatmaps_generated": self.stats.get('heatmaps_generated', 0),
                "stats_queries": self.stats.get('stats_queries', 0),
                "all_reports": self.stats.get('all_reports', 0)
            },
            "errors": self.stats.get('errors', 0)
        }
    
    def _get_available_reports(self) -> List[Dict[str, str]]:
        """Get list of available report types"""
        return [
            {"type": "console", "description": "Tournament console report"},
            {"type": "heatmap", "description": "Tournament heatmap visualization"},
            {"type": "stats", "description": "Database statistics"},
            {"type": "all", "description": "Generate all reports"},
            {"type": "database_stats", "description": "Database statistics via service locator"}
        ]
    
    def _get_last_report_info(self) -> Dict[str, Any]:
        """Get information about the last generated report"""
        return {
            "last_report": self.stats.get('last_report', 'None'),
            "last_report_time": self.stats.get('last_report_time', 'Never'),
            "total_reports": self.stats.get('total_reports', 0)
        }
    
    def _get_capabilities(self) -> List[str]:
        """Get list of available capabilities"""
        return [
            "console - Generate console report",
            "heatmap - Generate heatmap visualization",
            "stats - Show database statistics",
            "all - Generate all reports",
            "test - Test report system",
            "clear history - Clear statistics"
        ]
    
    def _get_action_suggestions(self) -> List[str]:
        """Get action suggestions"""
        return self._get_capabilities()
    
    def _format_for_discord(self, data: Any) -> str:
        """Format data for Discord output"""
        if isinstance(data, dict):
            if "error" in data:
                return f"❌ **Report Error:** {data['error']}"
            elif "success" in data and data["success"]:
                report_type = data.get("type", "unknown")
                return f"✅ **Report Generated:** {report_type.replace('_', ' ').title()}"
            elif "stats" in data or "console_reports" in data:
                stats = data.get("stats", data)
                return f"""📊 **Report Service Status:**
• Console Reports: {stats.get('console_reports', 0)}
• Heatmaps: {stats.get('heatmaps_generated', 0)}
• Stats Queries: {stats.get('stats_queries', 0)}
• All Reports: {stats.get('all_reports', 0)}
• Total Reports: {stats.get('total_reports', 0)}
• Errors: {stats.get('errors', 0)}
• Last Report: {stats.get('last_report', 'None')}"""
        return f"📊 Report: {str(data)}"
    
    def _format_for_text(self, data: Any) -> str:
        """Format data for text/console output"""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"{key}:")
                    for subkey, subvalue in value.items():
                        lines.append(f"  {subkey}: {subvalue}")
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
    "Report Service (Refactored)",
    [
        "Report generation with 3-method pattern",
        "ask('status') - Query report status and information",
        "tell('discord', data) - Format report data for output",
        "do('console report') - Generate reports and perform operations",
        "Supports: console, heatmap, stats, all",
        "Uses service locator for transparent local/network operation"
    ],
    [
        "report.ask('status')",
        "report.do('console report')",
        "report.do('heatmap')",
        "report.tell('discord')"
    ]
)

# Singleton instance
report_service_refactored = ReportServiceRefactored()

# Create network service wrapper for remote access
if __name__ != "__main__":
    try:
        wrapper = NetworkServiceWrapper(
            service=report_service_refactored,
            service_name="report_refactored",
            port_range=(9100, 9200)
        )
        # Auto-start network service in background
        wrapper.start_service_thread()
    except Exception as e:
        # Gracefully handle if network service fails
        pass


def start_report_service_refactored(args=None):
    """Handler for --report switch with service locator pattern"""
    
    # Determine report type from arguments
    report_type = "console"  # default
    
    if hasattr(args, 'report') and args.report:
        report_type = args.report
    
    report_service_refactored.logger.info(f"Starting report generation: {report_type}")
    
    try:
        if report_type == "console":
            result = report_service_refactored.do("console report")
        elif report_type == "heatmap":
            result = report_service_refactored.do("heatmap")
        elif report_type == "stats":
            result = report_service_refactored.do("stats")
        elif report_type == "all":
            result = report_service_refactored.do("all reports")
        else:
            report_service_refactored.logger.warning(f"Unknown report type: {report_type}. Using console.")
            result = report_service_refactored.do("console report")
        
        # Format result for output
        if result:
            formatted = report_service_refactored.tell("text", result)
            print(formatted)
        
        return result
            
    except Exception as e:
        error_msg = f"Report generation failed: {e}"
        report_service_refactored.error_handler.handle_error(error_msg, {"report_type": report_type})
        print(f"Error: {error_msg}")
        return None


# Register the refactored switch (commented out for now to avoid conflicts)
# announce_switch(
#     flag="--report-refactored",
#     help="START report generation (refactored with service locator)",
#     handler=start_report_service_refactored,
#     action="store",
#     nargs="?",
#     const="console",
#     metavar="TYPE"
# )