#!/usr/bin/env python3
"""
Process Management Guide - Self-documenting Bonjour service
Announces the proven pattern for adding process management to services
"""

from . import announcer

class ProcessManagementGuide:
    """Self-documenting guide for implementing process management"""
    
    def __init__(self):
        # Announce the proven template pattern
        announcer.announce(
            "ProcessManagementGuide",
            [
                "PROVEN PATTERN: Add self-management to existing services",
                "STEP 1: Add imports - polymorphic_core.process_management.BaseProcessManager",
                "STEP 2: Create [ServiceName]ProcessManager(BaseProcessManager) class",
                "STEP 3: Set SERVICE_NAME, PROCESSES[], PORTS[] class variables", 
                "STEP 4: Create global _[service]_process_manager instance",
                "STEP 5: Update go.py to import and use the process manager",
                "FALLBACK: Keep existing hardcoded patterns as backup"
            ]
        )
        
        # Announce next service analysis
        announcer.announce(
            "NextService_Discord",
            [
                "TARGET: bonjour_discord.py (main Discord service file)",
                "PROCESSES: ['bonjour_discord.py'] (single process)",
                "PORTS: [] (Discord uses WebSocket, no specific ports)", 
                "GO_PY_FLAGS: --discord-bot, --restart-services",
                "CURRENT_PATTERNS: kill_pattern('discord'), kill_pattern('polymorphic_discord')",
                "INTEGRATION: Add DiscordProcessManager to bonjour_discord.py"
            ]
        )
        
        # Announce service after Discord
        announcer.announce(
            "NextService_WebEditor", 
            [
                "TARGET: services/web_editor.py (main web editor file)",
                "PROCESSES: ['services/web_editor.py'] (single process)",
                "PORTS: [8081] (from advertisements)",
                "GO_PY_FLAGS: --edit-contacts, --restart-services", 
                "CURRENT_PATTERNS: kill_pattern('web_editor'), kill_pattern('editor_service')",
                "INTEGRATION: Add WebEditorProcessManager to services/web_editor.py"
            ]
        )
        
        # Announce validation commands
        announcer.announce(
            "ValidationCommands",
            [
                "TEST_ANNOUNCEMENTS: python3 go.py --advertisements | grep ProcessManager",
                "TEST_STARTUP: python3 go.py --[service-flag]", 
                "VERIFY_PROCESSES: ps aux | grep [service] | grep -v grep",
                "TEST_CLEANUP: import service; service._manager.cleanup_processes()",
                "INTEGRATION_TEST: python3 go.py --restart-services"
            ]
        )

# Create instance to announce capabilities
_guide = ProcessManagementGuide()