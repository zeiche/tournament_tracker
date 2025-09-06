#!/usr/bin/env python3
"""
capability_discovery.py - Models self-report their capabilities to Claude
Each model/module announces what it can do when loaded.
"""
import inspect
import sys
from typing import Dict, List, Any

class CapabilityRegistry:
    """
    Registry where modules/models report their capabilities.
    Claude can query this to know what's available.
    """
    def __init__(self):
        self.capabilities = {}
        self.models = {}
        self.methods = {}
        self.services = {}  # For discoverable services
        
    def register_model(self, model_class):
        """
        Model self-registers its capabilities.
        Introspects the model to find useful methods.
        """
        model_name = model_class.__name__
        
        # Get all public methods and properties
        capabilities = []
        
        for name, method in inspect.getmembers(model_class):
            # Skip private/magic methods
            if name.startswith('_'):
                continue
                
            # Check if it's a property
            if isinstance(inspect.getattr_static(model_class, name), property):
                doc = inspect.getattr_static(model_class, name).fget.__doc__
                capabilities.append({
                    'type': 'property',
                    'name': name,
                    'doc': doc or f"Property: {name}"
                })
            
            # Check if it's a method
            elif callable(getattr(model_class, name, None)):
                doc = method.__doc__
                sig = None
                try:
                    sig = str(inspect.signature(method))
                except:
                    pass
                    
                capabilities.append({
                    'type': 'method',
                    'name': name,
                    'signature': sig,
                    'doc': doc or f"Method: {name}"
                })
        
        self.models[model_name] = {
            'class': model_class,
            'capabilities': capabilities,
            'doc': model_class.__doc__
        }
        
        return self
    
    def register_function(self, func, category: str = "general"):
        """
        Register standalone functions and their capabilities.
        """
        if category not in self.capabilities:
            self.capabilities[category] = []
            
        self.capabilities[category].append({
            'name': func.__name__,
            'doc': func.__doc__ or "No description",
            'signature': str(inspect.signature(func)) if hasattr(inspect, 'signature') else None
        })
        
        return self
    
    def get_context_for_claude(self) -> str:
        """
        Generate a context string that tells Claude what's available.
        This is what gets injected into Claude's system prompt.
        """
        context_parts = []
        
        # Describe available models
        if self.models:
            context_parts.append("=== Available Data Models ===")
            for model_name, info in self.models.items():
                context_parts.append(f"\n{model_name}:")
                if info['doc']:
                    context_parts.append(f"  {info['doc'].strip()}")
                
                # List key capabilities
                properties = [c for c in info['capabilities'] if c['type'] == 'property']
                methods = [c for c in info['capabilities'] if c['type'] == 'method']
                
                if properties:
                    context_parts.append(f"  Properties: {', '.join(p['name'] for p in properties[:5])}")
                
                if methods:
                    important_methods = [m for m in methods if not m['name'].startswith('from_')]
                    context_parts.append(f"  Methods: {', '.join(m['name'] for m in important_methods[:5])}")
        
        # Describe available functions
        if self.capabilities:
            context_parts.append("\n=== Available Functions ===")
            for category, funcs in self.capabilities.items():
                context_parts.append(f"\n{category}:")
                for func in funcs[:3]:  # Limit to avoid overwhelming
                    context_parts.append(f"  - {func['name']}: {func['doc'].split('.')[0] if func['doc'] else 'Available'}")
        
        return "\n".join(context_parts)
    
    def discover_models(self):
        """
        Auto-discover and register models from tournament_models.
        """
        try:
            import tournament_models
            
            # Find all SQLAlchemy models
            for name, obj in inspect.getmembers(tournament_models):
                if inspect.isclass(obj) and hasattr(obj, '__tablename__'):
                    self.register_model(obj)
                    
        except ImportError:
            pass
            
        return self
    
    def discover_queries(self):
        """
        Auto-discover query functions.
        """
        try:
            import polymorphic_queries
            
            # Register the main query function
            if hasattr(polymorphic_queries, 'query'):
                self.register_function(
                    polymorphic_queries.query,
                    category="queries"
                )
                
        except ImportError:
            pass
            
        return self
    
    def register_service(self, service_name: str, service_getter):
        """
        Register a discoverable service.
        service_getter should be a function that returns the service instance.
        """
        self.services[service_name] = service_getter
        return self


# Global registry instance
capability_registry = CapabilityRegistry()


def register_capability(service_name: str, service_getter):
    """Register a service for discovery by other modules."""
    capability_registry.register_service(service_name, service_getter)


def discover_capability(service_name: str):
    """Discover and get a registered service by name."""
    if service_name in capability_registry.services:
        return capability_registry.services[service_name]()
    return None


def discover_all_capabilities() -> str:
    """
    Discover all available capabilities and return context for Claude.
    This is the main function Discord bot calls before talking to Claude.
    """
    # Clear and rediscover
    global capability_registry
    capability_registry = CapabilityRegistry()
    
    # Auto-discover everything
    capability_registry.discover_models()
    capability_registry.discover_queries()
    
    # Try to get current database stats
    stats_context = ""
    try:
        from database import get_session
        with get_session() as session:
            from tournament_models import Tournament, Player, Organization
            
            tournament_count = session.query(Tournament).count()
            player_count = session.query(Player).count()
            org_count = session.query(Organization).count()
            
            stats_context = f"""
Current Database Stats:
  - {tournament_count} tournaments tracked
  - {player_count} players in database
  - {org_count} organizations/venues
"""
    except:
        stats_context = "\nDatabase not currently accessible."
    
    # Build full context
    full_context = f"""You are a tournament tracker assistant for the SoCal FGC.
{capability_registry.get_context_for_claude()}
{stats_context}

When users ask questions, use your knowledge of these models and their capabilities to provide helpful information."""
    
    return full_context


if __name__ == "__main__":
    # Test the discovery
    context = discover_all_capabilities()
    print(context)