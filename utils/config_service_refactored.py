#!/usr/bin/env python3
"""
config_service_refactored.py - REFACTORED Config service using service locator

BEFORE: Direct environment access and minimal dependencies
AFTER: Uses service locator for logger and error handler dependencies

Key changes:
1. Uses service locator for logging and error handling
2. Can be distributed for centralized configuration management
3. Same configuration interface as original
4. Supports network-based config distribution
5. Enhanced validation and monitoring via discovered services

This completes the Phase 1 core services refactoring.
"""
import os
from typing import Any, Dict, List, Optional, Union
import json

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.config_service_refactored")

from polymorphic_core import announcer
from polymorphic_core.service_locator import get_service

class RefactoredConfigService:
    """
    REFACTORED Configuration service using service locator pattern.
    
    This version:
    - Uses service locator for dependencies (logger, error handler)
    - Can operate over network for distributed configuration
    - Enhanced validation and monitoring capabilities
    - Same configuration interface as original
    """
    
    _instance: Optional['RefactoredConfigService'] = None
    
    def __new__(cls, prefer_network: bool = False) -> 'RefactoredConfigService':
        """Singleton pattern with service preference"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.prefer_network = prefer_network
            cls._instance._logger = None
            cls._instance._error_handler = None
            cls._instance._cache = {}
            cls._instance._validation_history = []
            
            # Announce capabilities
            announcer.announce(
                "Config Service (Refactored)",
                [
                    "REFACTORED: Uses service locator for dependencies",
                    "Centralized configuration with 3-method pattern",
                    "ask('discord token') - get config values",
                    "tell('json', config) - format configuration",
                    "do('validate tokens') - validate configuration",
                    "Distributed config management with logging"
                ],
                [
                    "config.ask('discord token')",
                    "config.ask('all tokens')",
                    "config.do('validate tokens')",
                    "config.tell('discord', config_data)"
                ]
            )
        return cls._instance
    
    @property
    def logger(self):
        """Lazy-loaded logger service via service locator"""
        if self._logger is None:
            self._logger = get_service("logger", self.prefer_network)
        return self._logger
    
    @property
    def error_handler(self):
        """Lazy-loaded error handler service via service locator"""
        if self._error_handler is None:
            self._error_handler = get_service("error_handler", self.prefer_network)
        return self._error_handler
    
    def ask(self, query: str, default: Any = None, **kwargs) -> Any:
        """
        Get configuration values using natural language.
        
        Examples:
            ask("discord token")
            ask("startgg api key")
            ask("twilio account sid")
            ask("all tokens")
            ask("config status")
        """
        query_lower = query.lower().strip()
        
        # Log configuration access using discovered logger
        if self.logger:
            try:
                self.logger.info(f"Config access: {query}")
            except:
                pass
        
        try:
            # Handle common configuration queries
            if "discord" in query_lower and "token" in query_lower:
                return self._get_env_var("DISCORD_BOT_TOKEN", default)
            
            elif "startgg" in query_lower and ("token" in query_lower or "key" in query_lower):
                return self._get_env_var("STARTGG_API_TOKEN", default)
            
            elif "twilio" in query_lower:
                if "account" in query_lower:
                    return self._get_env_var("TWILIO_ACCOUNT_SID", default)
                elif "token" in query_lower or "auth" in query_lower:
                    return self._get_env_var("TWILIO_AUTH_TOKEN", default)
                elif "phone" in query_lower or "number" in query_lower:
                    return self._get_env_var("TWILIO_PHONE_NUMBER", default)
            
            elif "anthropic" in query_lower or "claude" in query_lower:
                return self._get_env_var("ANTHROPIC_API_KEY", default)
            
            elif "shopify" in query_lower:
                if "token" in query_lower:
                    return self._get_env_var("SHOPIFY_ACCESS_TOKEN", default)
                elif "domain" in query_lower:
                    return self._get_env_var("SHOPIFY_DOMAIN", default)
            
            elif "all" in query_lower and "token" in query_lower:
                return self._get_all_tokens()
            
            elif "config status" in query_lower or "status" in query_lower:
                return self._get_config_status()
            
            elif "validation history" in query_lower:
                return self._get_validation_history()
            
            elif "database" in query_lower:
                return "tournament_tracker.db"  # Default database
            
            else:
                # Direct environment variable lookup
                env_var = query_lower.upper().replace(" ", "_")
                return self._get_env_var(env_var, default)
                
        except Exception as e:
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "MEDIUM")
                except:
                    pass
            return {"error": f"Config query failed: {str(e)}"}
    
    def tell(self, format_type: str, data: Any = None, **kwargs) -> str:
        """
        Format configuration for different outputs.
        
        Formats: json, discord, text, masked, summary
        """
        if data is None:
            data = self._get_all_tokens()
        
        try:
            if format_type.lower() == "json":
                # Mask sensitive values for JSON output
                masked = self._mask_sensitive(data)
                return json.dumps(masked, indent=2)
            
            elif format_type.lower() in ["discord", "text"]:
                return self._format_discord_text(data)
            
            elif format_type.lower() == "masked":
                return self._format_masked(data)
            
            elif format_type.lower() == "summary":
                return self._format_summary(data)
            
            elif format_type.lower() == "validation":
                return self._format_validation_report(data)
            
            else:
                return str(data)
                
        except Exception as e:
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "LOW")
                except:
                    pass
            return f"Format error: {e}"
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform configuration operations using natural language.
        
        Examples:
            do("validate tokens")
            do("refresh config")
            do("check discord token")
            do("test all connections")
        """
        action_lower = action.lower().strip()
        
        # Log configuration actions
        if self.logger:
            try:
                self.logger.info(f"Config action: {action}")
            except:
                pass
        
        try:
            if "validate tokens" in action_lower or "validate all" in action_lower:
                return self._validate_all_tokens()
            
            elif "refresh config" in action_lower or "reload" in action_lower:
                return self._refresh_config()
            
            elif "check discord" in action_lower:
                return self._validate_discord_token()
            
            elif "check startgg" in action_lower:
                return self._validate_startgg_token()
            
            elif "check twilio" in action_lower:
                return self._validate_twilio_config()
            
            elif "check shopify" in action_lower:
                return self._validate_shopify_config()
            
            elif "test connections" in action_lower or "test all" in action_lower:
                return self._test_all_connections()
            
            elif "clear cache" in action_lower:
                return self._clear_cache()
            
            else:
                return {"error": f"Don't know how to: {action}"}
                
        except Exception as e:
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "HIGH")
                except:
                    pass
            return {"error": f"Config action failed: {str(e)}"}
    
    # Core configuration methods
    def _get_env_var(self, var_name: str, default: Any = None) -> Any:
        """Get environment variable with caching and logging"""
        if var_name in self._cache:
            return self._cache[var_name]
        
        value = os.getenv(var_name, default)
        
        # Cache non-None values
        if value is not None:
            self._cache[var_name] = value
        
        return value
    
    def _get_all_tokens(self) -> Dict[str, Any]:
        """Get all known configuration tokens"""
        tokens = {
            "DISCORD_BOT_TOKEN": self._get_env_var("DISCORD_BOT_TOKEN"),
            "STARTGG_API_TOKEN": self._get_env_var("STARTGG_API_TOKEN"),
            "ANTHROPIC_API_KEY": self._get_env_var("ANTHROPIC_API_KEY"),
            "SHOPIFY_ACCESS_TOKEN": self._get_env_var("SHOPIFY_ACCESS_TOKEN"),
            "SHOPIFY_DOMAIN": self._get_env_var("SHOPIFY_DOMAIN"),
            "TWILIO_ACCOUNT_SID": self._get_env_var("TWILIO_ACCOUNT_SID"),
            "TWILIO_AUTH_TOKEN": self._get_env_var("TWILIO_AUTH_TOKEN"),
            "TWILIO_PHONE_NUMBER": self._get_env_var("TWILIO_PHONE_NUMBER"),
        }
        return tokens
    
    def _get_config_status(self) -> Dict[str, Any]:
        """Get overall configuration status"""
        tokens = self._get_all_tokens()
        status = {
            "total_configs": len(tokens),
            "configured": len([v for v in tokens.values() if v]),
            "missing": len([v for v in tokens.values() if not v]),
            "cache_size": len(self._cache),
            "validation_runs": len(self._validation_history)
        }
        
        status["health"] = "good" if status["configured"] > status["missing"] else "needs_attention"
        
        return status
    
    def _get_validation_history(self) -> Dict[str, Any]:
        """Get validation history"""
        return {
            "history": self._validation_history[-10:],  # Last 10 validations
            "total_validations": len(self._validation_history)
        }
    
    # Validation methods
    def _validate_all_tokens(self) -> Dict[str, Any]:
        """Validate all configuration tokens"""
        results = {}
        tokens = self._get_all_tokens()
        
        for token_name, token_value in tokens.items():
            if token_value:
                # Basic validation - check if it's not empty and has reasonable length
                if len(token_value) > 10:  # Minimum reasonable token length
                    results[token_name] = {"status": "present", "length": len(token_value)}
                else:
                    results[token_name] = {"status": "too_short", "length": len(token_value)}
            else:
                results[token_name] = {"status": "missing", "length": 0}
        
        # Record validation
        validation_record = {
            "timestamp": self._get_timestamp(),
            "results": results,
            "total_checked": len(tokens),
            "passed": len([r for r in results.values() if r["status"] == "present"])
        }
        
        self._validation_history.append(validation_record)
        
        # Trim history
        if len(self._validation_history) > 50:
            self._validation_history = self._validation_history[-50:]
        
        return validation_record
    
    def _validate_discord_token(self) -> Dict[str, Any]:
        """Validate Discord token specifically"""
        token = self._get_env_var("DISCORD_BOT_TOKEN")
        
        if not token:
            return {"status": "missing", "valid": False}
        
        # Basic Discord token validation
        if token.startswith("Bot ") or len(token) > 50:
            return {"status": "present", "valid": True, "format": "likely_valid"}
        else:
            return {"status": "present", "valid": False, "format": "invalid_format"}
    
    def _validate_startgg_token(self) -> Dict[str, Any]:
        """Validate Start.gg token"""
        token = self._get_env_var("STARTGG_API_TOKEN")
        
        if not token:
            return {"status": "missing", "valid": False}
        
        # Basic validation
        if len(token) > 20:
            return {"status": "present", "valid": True}
        else:
            return {"status": "present", "valid": False, "reason": "too_short"}
    
    def _validate_twilio_config(self) -> Dict[str, Any]:
        """Validate Twilio configuration"""
        account_sid = self._get_env_var("TWILIO_ACCOUNT_SID")
        auth_token = self._get_env_var("TWILIO_AUTH_TOKEN")
        phone_number = self._get_env_var("TWILIO_PHONE_NUMBER")
        
        result = {
            "account_sid": {"present": bool(account_sid), "valid": account_sid and account_sid.startswith("AC") if account_sid else False},
            "auth_token": {"present": bool(auth_token), "valid": auth_token and len(auth_token) > 20 if auth_token else False},
            "phone_number": {"present": bool(phone_number), "valid": phone_number and phone_number.startswith("+") if phone_number else False}
        }
        
        result["overall"] = all(r["valid"] for r in result.values())
        
        return result
    
    def _validate_shopify_config(self) -> Dict[str, Any]:
        """Validate Shopify configuration"""
        token = self._get_env_var("SHOPIFY_ACCESS_TOKEN")
        domain = self._get_env_var("SHOPIFY_DOMAIN")
        
        return {
            "access_token": {"present": bool(token), "valid": token and len(token) > 20 if token else False},
            "domain": {"present": bool(domain), "valid": domain and "." in domain if domain else False},
            "overall": bool(token and domain)
        }
    
    def _test_all_connections(self) -> Dict[str, Any]:
        """Test connections to all services (basic checks)"""
        # This would normally make actual API calls, but for safety we'll do basic validation
        results = {
            "discord": self._validate_discord_token(),
            "startgg": self._validate_startgg_token(),
            "twilio": self._validate_twilio_config(),
            "shopify": self._validate_shopify_config()
        }
        
        return {
            "tests": results,
            "timestamp": self._get_timestamp(),
            "overall_health": "good" if all(r.get("valid", r.get("overall", False)) for r in results.values()) else "issues_found"
        }
    
    def _refresh_config(self) -> Dict[str, Any]:
        """Refresh configuration cache"""
        old_cache_size = len(self._cache)
        self._cache.clear()
        
        # Reload all known configs
        tokens = self._get_all_tokens()
        
        return {
            "action": "refresh_config",
            "old_cache_size": old_cache_size,
            "new_cache_size": len(self._cache),
            "reloaded_configs": len(tokens)
        }
    
    def _clear_cache(self) -> Dict[str, Any]:
        """Clear configuration cache"""
        old_size = len(self._cache)
        self._cache.clear()
        
        return {
            "action": "clear_cache",
            "cleared_entries": old_size
        }
    
    # Format methods
    def _format_discord_text(self, data: Dict) -> str:
        """Format for Discord/text output"""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if value:
                    masked_value = self._mask_value(value)
                    lines.append(f"✅ {key}: {masked_value}")
                else:
                    lines.append(f"❌ {key}: Not set")
            return "\n".join(lines)
        return str(data)
    
    def _format_masked(self, data: Dict) -> str:
        """Format with all sensitive data masked"""
        masked = self._mask_sensitive(data)
        return json.dumps(masked, indent=2)
    
    def _format_summary(self, data: Dict) -> str:
        """Format as summary"""
        if isinstance(data, dict):
            if "total_configs" in data:  # Status data
                return f"Config: {data['configured']}/{data['total_configs']} configured, health: {data['health']}"
            else:  # Token data
                configured = len([v for v in data.values() if v])
                total = len(data)
                return f"Configuration: {configured}/{total} tokens configured"
        return str(data)
    
    def _format_validation_report(self, data: Dict) -> str:
        """Format validation results"""
        if "results" in data:
            lines = [f"🔍 **Validation Report ({data['timestamp']}):**"]
            for token, result in data["results"].items():
                status_emoji = {"present": "✅", "missing": "❌", "too_short": "⚠️"}.get(result["status"], "❓")
                lines.append(f"{status_emoji} {token}: {result['status']}")
            lines.append(f"📊 **Summary:** {data['passed']}/{data['total_checked']} passed")
            return "\n".join(lines)
        return str(data)
    
    # Utility methods
    def _mask_sensitive(self, data: Dict) -> Dict:
        """Mask sensitive configuration values"""
        masked = {}
        for key, value in data.items():
            masked[key] = self._mask_value(value) if value else value
        return masked
    
    def _mask_value(self, value: str) -> str:
        """Mask a configuration value for display"""
        if not value:
            return value
        
        if len(value) <= 8:
            return "*" * len(value)
        else:
            return value[:4] + "*" * (len(value) - 8) + value[-4:]
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

# Create service instances
config_service = RefactoredConfigService(prefer_network=False)  # Local-first
config_service_network = RefactoredConfigService(prefer_network=True)  # Network-first

# Backward compatibility function
def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value (backward compatible)"""
    return config_service.ask(key, default)

if __name__ == "__main__":
    # Test the refactored config service
    print("🧪 Testing Refactored Config Service")
    
    # Test local-first service
    print("\n1. Testing local-first config service:")
    config_local = RefactoredConfigService(prefer_network=False)
    
    # Test basic queries
    discord_token = config_local.ask("discord token")
    print(f"Discord token: {config_local.tell('masked', {'DISCORD_BOT_TOKEN': discord_token})}")
    
    # Test validation
    validation = config_local.do("validate tokens")
    print(f"Validation: {config_local.tell('validation', validation)}")
    
    # Test status
    status = config_local.ask("config status")
    print(f"Status: {config_local.tell('summary', status)}")
    
    # Test network-first service
    print("\n2. Testing network-first config service:")
    config_network = RefactoredConfigService(prefer_network=True)
    
    all_tokens = config_network.ask("all tokens")
    print(f"All tokens: {config_network.tell('discord', all_tokens)}")
    
    # Test backward compatibility
    print("\n3. Testing backward compatibility:")
    discord_via_function = get_config("discord token")
    print(f"Discord via function: {'Present' if discord_via_function else 'Missing'}")
    
    print("\n✅ Refactored config service test complete!")
    print("💡 Same configuration interface, but now with service locator and enhanced monitoring!")