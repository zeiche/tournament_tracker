#!/usr/bin/env python3
"""
Bonjour Formatter Service - Generic data formatting with service-specific branding
Extracted from twilio service for reuse across all bonjour services
"""

import json
import html
from typing import Dict, Any, Optional, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("services.bonjour_formatter_service")

from polymorphic_core.local_bonjour import local_announcer
from polymorphic_core.service_locator import get_service


class BonjourFormatterService:
    """Generic data formatting service with service-specific branding support"""
    
    def __init__(self):
        self._logger = None
        
        # Service branding configurations
        self.service_configs = {
            'twilio': {
                'emoji': '📞',
                'name': 'Twilio',
                'success_prefix': 'Twilio Success',
                'error_prefix': 'Twilio Error',
                'status_fields': ['calls_made', 'bridges_started', 'services_started', 'errors', 'last_operation']
            },
            'database': {
                'emoji': '🗃️',
                'name': 'Database',
                'success_prefix': 'Database Success',
                'error_prefix': 'Database Error',
                'status_fields': ['queries_executed', 'connections', 'errors', 'last_query']
            },
            'web': {
                'emoji': '🌐',
                'name': 'Web Service',
                'success_prefix': 'Web Success',
                'error_prefix': 'Web Error',
                'status_fields': ['requests_served', 'active_connections', 'errors', 'uptime']
            },
            'media': {
                'emoji': '🎬',
                'name': 'Media Stream',
                'success_prefix': 'Media Success', 
                'error_prefix': 'Media Error',
                'status_fields': ['streams_active', 'total_data', 'errors', 'last_stream']
            },
            'default': {
                'emoji': '⚙️',
                'name': 'Service',
                'success_prefix': 'Success',
                'error_prefix': 'Error',
                'status_fields': ['status', 'errors', 'last_operation']
            }
        }
        
        # Announce to bonjour
        local_announcer.announce("BonjourFormatterService", [
            "I provide generic data formatting across all services",
            "I support discord, html, text, json formatting",
            "I handle service-specific branding and emojis",
            "I format error messages, status data, and generic content",
            "I use the 3-method pattern: ask/tell/do"
        ])
    
    @property
    def logger(self):
        """Get logger service via service locator"""
        if self._logger is None:
            self._logger = get_service("logger", prefer_network=False)
        return self._logger
    
    def ask(self, query: str, **kwargs) -> Any:
        """Query interface for formatter service"""
        query_lower = query.lower().strip()
        
        if 'services' in query_lower or 'supported' in query_lower:
            return list(self.service_configs.keys())
        elif 'formats' in query_lower:
            return ['discord', 'html', 'text', 'json']
        elif 'config' in query_lower:
            service = kwargs.get('service', 'default')
            return self.service_configs.get(service, self.service_configs['default'])
        
        return "Available queries: services, formats, config"
    
    def tell(self, format_type: str, data: Any = None) -> str:
        """Format data for output (meta-formatting)"""
        if data is None:
            data = {
                'service': 'BonjourFormatterService',
                'supported_formats': ['discord', 'html', 'text', 'json'],
                'supported_services': list(self.service_configs.keys())
            }
        
        return self.format_data(data, format_type, service='formatter')
    
    def do(self, action: str, **kwargs) -> Any:
        """Perform formatting actions"""
        action_lower = action.lower().strip()
        
        if 'register service' in action_lower:
            service_name = kwargs.get('service_name')
            config = kwargs.get('config', {})
            if service_name:
                self.service_configs[service_name] = config
                return f"Registered formatting config for {service_name}"
        
        return "Available actions: register service"
    
    def format_data(self, data: Any, format_type: str, service: str = 'default', **kwargs) -> str:
        """
        Main formatting method with service-specific branding
        
        Args:
            data: Data to format
            format_type: Output format (discord, html, text, json)
            service: Service name for branding (twilio, database, etc.)
            **kwargs: Additional formatting options
        """
        try:
            # Get service configuration
            config = self.service_configs.get(service, self.service_configs['default'])
            
            # Route to appropriate formatter
            if format_type == 'discord':
                return self._format_for_discord(data, config, **kwargs)
            elif format_type == 'html':
                return self._format_for_html(data, config, **kwargs)
            elif format_type == 'text':
                return self._format_for_text(data, config, **kwargs)
            elif format_type == 'json':
                return self._format_for_json(data, config, **kwargs)
            else:
                return str(data)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Formatting failed: {e}")
            return f"Format error: {e}"
    
    def format_with_branding(self, data: Any, format_type: str, service: str, **kwargs) -> str:
        """Convenience method for service-specific formatting"""
        return self.format_data(data, format_type, service, **kwargs)
    
    def _format_for_discord(self, data: Any, config: Dict[str, Any], **kwargs) -> str:
        """Format data for Discord output with service branding"""
        emoji = config['emoji']
        service_name = config['name']
        
        if isinstance(data, dict):
            # Handle errors
            if "error" in data:
                return f"❌ **{config['error_prefix']}:** {data['error']}"
            
            # Handle success messages
            elif "success" in data and data["success"]:
                success_msg = data.get('message', 'Operation completed')
                return f"✅ **{config['success_prefix']}:** {success_msg}"
            
            # Handle status/stats data
            elif any(field in data for field in config['status_fields']):
                lines = [f"{emoji} **{service_name} Status:**"]
                for field in config['status_fields']:
                    if field in data:
                        # Format field name nicely
                        display_name = field.replace('_', ' ').title()
                        lines.append(f"• {display_name}: {data[field]}")
                return "\n".join(lines)
            
            # Handle generic dict data
            else:
                lines = [f"{emoji} **{service_name} Data:**"]
                for key, value in data.items():
                    display_key = key.replace('_', ' ').title()
                    lines.append(f"• {display_key}: {value}")
                return "\n".join(lines)
        
        # Handle non-dict data
        return f"{emoji} {service_name}: {str(data)}"
    
    def _format_for_html(self, data: Any, config: Dict[str, Any], **kwargs) -> str:
        """Format data for HTML output"""
        service_name = config['name']
        
        if isinstance(data, dict):
            html_content = f"<h3>{service_name} Data</h3>"
            html_content += "<table border='1' style='border-collapse: collapse;'>"
            
            for key, value in data.items():
                display_key = key.replace('_', ' ').title()
                escaped_value = html.escape(str(value))
                html_content += f"<tr><td><strong>{display_key}</strong></td><td>{escaped_value}</td></tr>"
            
            html_content += "</table>"
            return html_content
        
        return f"<div><strong>{service_name}:</strong> <pre>{html.escape(str(data))}</pre></div>"
    
    def _format_for_text(self, data: Any, config: Dict[str, Any], **kwargs) -> str:
        """Format data for text/console output"""
        service_name = config['name']
        
        if isinstance(data, dict):
            lines = [f"{service_name} Data:"]
            lines.append("=" * (len(service_name) + 6))
            
            for key, value in data.items():
                display_key = key.replace('_', ' ').title()
                lines.append(f"{display_key}: {value}")
            
            return "\n".join(lines)
        
        return f"{service_name}: {str(data)}"
    
    def _format_for_json(self, data: Any, config: Dict[str, Any], **kwargs) -> str:
        """Format data as JSON with service metadata"""
        output = {
            'service': config['name'].lower().replace(' ', '_'),
            'formatted_at': kwargs.get('timestamp'),
            'data': data
        }
        
        return json.dumps(output, indent=2, default=str)
    
    def register_service_config(self, service_name: str, emoji: str, display_name: str, 
                              status_fields: List[str] = None) -> None:
        """Register a new service configuration for formatting"""
        if status_fields is None:
            status_fields = ['status', 'errors', 'last_operation']
        
        self.service_configs[service_name] = {
            'emoji': emoji,
            'name': display_name,
            'success_prefix': f'{display_name} Success',
            'error_prefix': f'{display_name} Error',
            'status_fields': status_fields
        }
        
        if self.logger:
            self.logger.info(f"Registered formatting config for {service_name}")


# Service factory function
def get_formatter_service() -> BonjourFormatterService:
    """Get or create formatter service instance"""
    return BonjourFormatterService()


# Create singleton instance
formatter_service = BonjourFormatterService()


if __name__ == '__main__':
    # Test the formatter service
    print("🎨 Bonjour Formatter Service")
    print("📋 Testing different formats:")
    
    # Test data
    test_data = {
        'calls_made': 5,
        'bridges_started': 2,
        'errors': 0,
        'last_operation': 'start_bridge',
        'success': True
    }
    
    # Test formatting for different services
    for service in ['twilio', 'database', 'web']:
        print(f"\n--- {service.upper()} SERVICE ---")
        print("Discord format:")
        print(formatter_service.format_data(test_data, 'discord', service))
        print("\nText format:")
        print(formatter_service.format_data(test_data, 'text', service))