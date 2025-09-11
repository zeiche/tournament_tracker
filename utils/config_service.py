#!/usr/bin/env python3
"""
config_service.py - Centralized configuration management
Follows the 3-method pattern: ask(), tell(), do()
"""
import os
from typing import Any, Dict, List, Optional, Union


class ConfigService:
    """
    Centralized configuration service using 3-method pattern
    """
    
    def __init__(self):
        self._cache = {}
    
    def ask(self, query: str, default: Any = None, **kwargs) -> Any:
        """
        Get configuration values using natural language
        Examples:
            ask("discord token")
            ask("startgg api key") 
            ask("twilio account sid")
            ask("all tokens")
        """
        query = query.lower().strip()
        
        # Handle common configuration queries
        if "discord" in query and "token" in query:
            return os.getenv("DISCORD_BOT_TOKEN", default)
        
        elif "startgg" in query and ("token" in query or "key" in query):
            return os.getenv("STARTGG_API_TOKEN", default)
        
        elif "twilio" in query:
            if "account" in query:
                return os.getenv("TWILIO_ACCOUNT_SID", default)
            elif "token" in query or "auth" in query:
                return os.getenv("TWILIO_AUTH_TOKEN", default)
            elif "phone" in query or "number" in query:
                return os.getenv("TWILIO_PHONE_NUMBER", default)
        
        elif "anthropic" in query or "claude" in query:
            return os.getenv("ANTHROPIC_API_KEY", default)
        
        elif "shopify" in query:
            if "token" in query:
                return os.getenv("SHOPIFY_ACCESS_TOKEN", default)
            elif "domain" in query:
                return os.getenv("SHOPIFY_DOMAIN", default)
        
        elif "all" in query and "token" in query:
            return self._get_all_tokens()
        
        elif "database" in query:
            return "tournament_tracker.db"  # Default database
        
        else:
            # Direct environment variable lookup
            env_var = query.upper().replace(" ", "_")
            return os.getenv(env_var, default)
    
    def tell(self, format: str, data: Any = None) -> str:
        """
        Format configuration for different outputs
        """
        if data is None:
            data = self._get_all_tokens()
        
        if format.lower() in ["json"]:
            import json
            # Mask sensitive values for JSON output
            masked = self._mask_sensitive(data)
            return json.dumps(masked, indent=2)
        
        elif format.lower() in ["discord", "text"]:
            if isinstance(data, dict):
                lines = []
                for key, value in data.items():
                    if value:
                        masked_value = self._mask_value(value)
                        lines.append(f"{key}: {masked_value}")
                    else:
                        lines.append(f"{key}: ❌ Not set")
                return "\n".join(lines)
            return str(data)
        
        else:
            return str(data)
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform configuration actions
        Examples:
            do("validate tokens")
            do("refresh config") 
            do("check discord token")
        """
        action = action.lower().strip()
        
        if "validate" in action:
            return self._validate_config()
        
        elif "refresh" in action or "reload" in action:
            self._cache.clear()
            return "Configuration cache cleared"
        
        elif "check" in action:
            if "discord" in action:
                token = self.ask("discord token")
                return "✅ Discord token set" if token else "❌ Discord token missing"
            elif "startgg" in action:
                token = self.ask("startgg api key")
                return "✅ StartGG token set" if token else "❌ StartGG token missing"
            elif "twilio" in action:
                sid = self.ask("twilio account sid")
                token = self.ask("twilio auth token")
                if sid and token:
                    return "✅ Twilio credentials set"
                else:
                    return "❌ Twilio credentials incomplete"
        
        else:
            return f"Unknown config action: {action}"
    
    def _get_all_tokens(self) -> Dict[str, Optional[str]]:
        """Get all known configuration tokens"""
        return {
            "DISCORD_BOT_TOKEN": os.getenv("DISCORD_BOT_TOKEN"),
            "STARTGG_API_TOKEN": os.getenv("STARTGG_API_TOKEN"),
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
            "TWILIO_ACCOUNT_SID": os.getenv("TWILIO_ACCOUNT_SID"),
            "TWILIO_AUTH_TOKEN": os.getenv("TWILIO_AUTH_TOKEN"),
            "TWILIO_PHONE_NUMBER": os.getenv("TWILIO_PHONE_NUMBER"),
            "SHOPIFY_ACCESS_TOKEN": os.getenv("SHOPIFY_ACCESS_TOKEN"),
            "SHOPIFY_DOMAIN": os.getenv("SHOPIFY_DOMAIN")
        }
    
    def _validate_config(self) -> Dict[str, str]:
        """Validate current configuration"""
        results = {}
        tokens = self._get_all_tokens()
        
        for key, value in tokens.items():
            if value:
                if len(value) > 10:  # Basic length check
                    results[key] = "✅ Valid"
                else:
                    results[key] = "⚠️ Too short"
            else:
                results[key] = "❌ Missing"
        
        return results
    
    def _mask_sensitive(self, data: Dict[str, Optional[str]]) -> Dict[str, str]:
        """Mask sensitive values for safe display"""
        masked = {}
        for key, value in data.items():
            if value:
                masked[key] = self._mask_value(value)
            else:
                masked[key] = "Not set"
        return masked
    
    def _mask_value(self, value: str) -> str:
        """Mask a sensitive value for display"""
        if len(value) <= 8:
            return "***"
        return value[:4] + "***" + value[-4:]


# Global instance
config_service = ConfigService()


# Convenience functions
def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value"""
    return config_service.ask(key, default)

def validate_config() -> Dict[str, str]:
    """Validate all configuration"""
    return config_service.do("validate tokens")

def check_required_tokens() -> bool:
    """Check if required tokens are available"""
    discord = get_config("discord token")
    startgg = get_config("startgg api key") 
    return bool(discord and startgg)