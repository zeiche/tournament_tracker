#!/usr/bin/env python3
"""
report_service.py - Unified Report Service (Consolidates --console, --heatmap, --stats)

This module consolidates all reporting functionality into a single --report switch
with subcommands for different report types.
"""

import sys
import os
import subprocess
from typing import Optional, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("services.report_service")

from utils.simple_logger import info, warning, error
from polymorphic_core import announcer
from utils.dynamic_switches import announce_switch


class ReportService:
    """Unified service for all tournament reports"""
    
    def generate_console_report(self):
        """Generate console report"""
        try:
            info("Generating console report...")
            subprocess.run([sys.executable, 'tournament_domain/analytics/tournament_report.py'])
        except Exception as e:
            error(f"Console report failed: {e}")
    
    def generate_heatmap(self):
        """Generate heatmap visualization"""
        try:
            info("Generating heatmap...")
            subprocess.run([sys.executable, 'tournament_domain/analytics/tournament_heatmap.py'])
        except Exception as e:
            error(f"Heatmap generation failed: {e}")
    
    def show_stats(self):
        """Show database statistics"""
        try:
            info("Showing database statistics...")
            subprocess.run([sys.executable, 'utils/database_service.py', '--stats'])
        except Exception as e:
            error(f"Stats display failed: {e}")
    
    def generate_all_reports(self):
        """Generate all reports"""
        info("Generating all reports...")
        self.show_stats()
        self.generate_console_report()
        self.generate_heatmap()


# Announce service capabilities
announcer.announce(
    "Unified Report Service",
    [
        "Consolidated reporting for tournaments",
        "Supports: console, heatmap, stats, all",
        "Single --report switch with subcommands"
    ],
    [
        "report.generate_console_report()",
        "report.generate_heatmap()",
        "report.show_stats()"
    ]
)

# Singleton instance
report_service = ReportService()


def start_report_service(args=None):
    """Handler for --report switch with subcommands"""
    
    # Determine report type from arguments
    report_type = "console"  # default
    
    if hasattr(args, 'report') and args.report:
        report_type = args.report
    
    info(f"Starting report generation: {report_type}")
    
    try:
        if report_type == "console":
            report_service.generate_console_report()
        elif report_type == "heatmap":
            report_service.generate_heatmap()
        elif report_type == "stats":
            report_service.show_stats()
        elif report_type == "all":
            report_service.generate_all_reports()
        else:
            warning(f"Unknown report type: {report_type}. Using console.")
            report_service.generate_console_report()
            
    except Exception as e:
        error(f"Report generation failed: {e}")
        return None


announce_switch(
    flag="--report",
    help="START report generation (console|heatmap|stats|all)",
    handler=start_report_service,
    action="store",
    nargs="?",
    const="console",  # Default when no argument provided
    metavar="TYPE"
)