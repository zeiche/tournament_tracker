#!/usr/bin/env python3
"""
Ollama Bonjour Service - Complete integration of Ollama with Bonjour
This is Claude's little brother - works offline, understands services
"""

import json
import logging
import requests
import subprocess
import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add parent for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from polymorphic_core import announcer

# Import services to trigger their announcements
try:
    from utils import database_service
except: pass
try:
    from services import startgg_sync
except: pass
try:
    from utils import tournament_operations
except: pass
try:
    from services import web_editor
except: pass
try:
    from models import tournament_models
except: pass

logger = logging.getLogger('ollama_bonjour')

class OllamaBonjour:
    """
    Complete Ollama integration with Bonjour service discovery
    """
    
    def __init__(self, model='mistral', auto_start=True):
        """
        Initialize Ollama with Bonjour integration
        
        Args:
            model: Model to use (mistral, llama2, phi, etc.)
            auto_start: Try to start Ollama if not running
        """
        self.model = model
        self.base_url = 'http://localhost:11434'
        self.api_generate = f"{self.base_url}/api/generate"
        self.api_models = f"{self.base_url}/api/tags"
        
        # Service memory - stores all discovered services
        self.service_memory = {}
        self.announcement_history = []
        
        # Check Ollama availability - truly non-blocking
        self.available = False
        if auto_start:
            try:
                # Quick check with very short timeout
                response = requests.get(self.api_models, timeout=0.1)
                if response.status_code == 200:
                    self.available = True
            except:
                pass  # Ollama not available, continue anyway
        
        # Announce ourselves
        self._announce()
        
        # Subscribe to all Bonjour announcements
        self._subscribe_to_bonjour()
        
        logger.info(f"Ollama Bonjour initialized with model: {model}")
    
    def _setup_ollama(self, auto_start: bool) -> bool:
        """Setup Ollama service"""
        try:
            # Check if running
            response = requests.get(self.api_models, timeout=2)
            if response.status_code == 200:
                logger.info("Ollama is running")
                self._ensure_model()
                return True
        except:
            if auto_start:
                return self._start_ollama()
        return False
    
    def _start_ollama(self) -> bool:
        """Try to start Ollama service - but be polymorphic about it"""
        try:
            logger.info("Checking if Ollama can be started...")
            
            # First check if ollama command exists
            result = subprocess.run(['which', 'ollama'], 
                                  capture_output=True, text=True, timeout=1)
            if result.returncode != 0:
                logger.warning("Ollama not installed - running in simulation mode")
                return False
            
            # Try to start in background, but with timeout
            logger.info("Attempting to start Ollama service...")
            proc = subprocess.Popen(['timeout', '3', 'ollama', 'serve'], 
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
            
            # Give it a moment
            import time
            time.sleep(2)
            
            # Check if it started
            try:
                if requests.get(self.api_models, timeout=1).status_code == 200:
                    logger.info("Ollama started successfully")
                    self._ensure_model()
                    return True
            except:
                pass
                
            logger.warning("Ollama didn't start - will work in limited mode")
        except Exception as e:
            logger.warning(f"Ollama unavailable: {e} - continuing anyway")
        return False
    
    def _ensure_model(self):
        """Ensure model is available"""
        try:
            response = requests.get(self.api_models)
            if response.status_code == 200:
                models = [m['name'].split(':')[0] for m in response.json().get('models', [])]
                if self.model not in models:
                    logger.info(f"Pulling {self.model} model...")
                    subprocess.run(['ollama', 'pull', self.model], 
                                 capture_output=True, timeout=300)
        except Exception as e:
            logger.warning(f"Could not ensure model: {e}")
    
    def _announce(self):
        """Announce via Bonjour"""
        status = "✅ Running" if self.available else "⚠️ Not available"
        
        announcer.announce("Ollama Bonjour", [
            f"Ollama Intelligence - Claude's little brother ({status})",
            f"Model: {self.model} - Completely offline",
            "I understand ALL Bonjour service announcements",
            "I remember every service that announces itself",
            "I can explain how services work together",
            "ask('how to sync?') - Natural language questions",
            "tell('discord', answer) - Format responses",
            "do('analyze services') - Understand service landscape",
            f"Memory: {len(self.service_memory)} services discovered",
            "I am your offline guide to all services"
        ])
    
    def _subscribe_to_bonjour(self):
        """Subscribe to and process all Bonjour announcements"""
        # Process existing announcements
        for announcement in announcer.announcements:
            self._process_announcement(announcement)
        
        # Set up listener for new announcements (would need event system)
        logger.info(f"Subscribed to Bonjour - tracking {len(self.service_memory)} services")
    
    def _process_announcement(self, announcement: Dict):
        """Process a Bonjour announcement"""
        service_name = announcement.get('service', 'Unknown')
        capabilities = announcement.get('capabilities', [])
        
        # Skip ourselves
        if service_name == "Ollama Bonjour":
            return
        
        # Store in memory with timestamp
        self.service_memory[service_name] = {
            'capabilities': capabilities,
            'first_seen': self.service_memory.get(service_name, {}).get('first_seen', datetime.now()),
            'last_seen': datetime.now(),
            'announcement_count': self.service_memory.get(service_name, {}).get('announcement_count', 0) + 1
        }
        
        # Keep history
        self.announcement_history.append({
            'service': service_name,
            'timestamp': datetime.now(),
            'capabilities_count': len(capabilities)
        })
        
        # Limit history size
        if len(self.announcement_history) > 1000:
            self.announcement_history = self.announcement_history[-500:]
        
        logger.debug(f"Processed announcement from {service_name}")
    
    def _build_context(self, query: str) -> str:
        """Build context for Ollama based on query and known services"""
        # Find relevant services based on query keywords
        query_lower = query.lower()
        relevant_services = {}
        
        for service_name, data in self.service_memory.items():
            # Check if service might be relevant
            service_text = f"{service_name} {' '.join(data['capabilities'])}".lower()
            
            # Score relevance
            relevance = 0
            for word in query_lower.split():
                if len(word) > 2 and word in service_text:
                    relevance += 1
            
            if relevance > 0 or len(self.service_memory) < 10:
                relevant_services[service_name] = data
        
        # Build context
        context = "You are an intelligent service router. Here are the available services:\n\n"
        
        for service_name, data in relevant_services.items():
            context += f"**{service_name}**\n"
            # Include most important capabilities
            for cap in data['capabilities'][:5]:
                context += f"  - {cap}\n"
            context += f"  - Seen {data['announcement_count']} times\n"
            context += "\n"
        
        return context
    
    def _query_ollama(self, prompt: str) -> str:
        """Send query to Ollama"""
        if not self.available:
            return self._fallback_response(prompt)
        
        try:
            payload = {
                'model': self.model,
                'prompt': prompt,
                'temperature': 0.7,
                'stream': False
            }
            
            response = requests.post(self.api_generate, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json().get('response', '')
        except Exception as e:
            logger.error(f"Ollama query failed: {e}")
        
        return self._fallback_response(prompt)
    
    def _execute_command(self, service_name: str, method: str, params: str = None) -> Any:
        """Actually execute a command on a service and return real data"""
        try:
            # Import the actual service instance (not the module)
            if 'database' in service_name.lower():
                from utils.database_service import database_service
                service = database_service
            elif 'sync' in service_name.lower():
                from services.startgg_sync import startgg_sync
                service = startgg_sync
            elif 'editor' in service_name.lower() or 'web' in service_name.lower():
                from services.web_editor import web_editor
                service = web_editor
            elif 'operation' in service_name.lower():
                from utils.tournament_operations import tournament_operations
                service = tournament_operations
            else:
                return f"Service {service_name} not available for execution"
            
            # Execute the method
            if method == 'ask':
                result = service.ask(params) if params else service.ask('')
            elif method == 'tell':
                # For tell, we need data - just show format options
                result = "Tell formats: json, discord, text, html"
            elif method == 'do':
                result = service.do(params) if params else service.do('')
            else:
                result = f"Unknown method: {method}"
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute {service_name}.{method}('{params}'): {e}")
            return f"Error executing command: {e}"
    
    def _fallback_response(self, query: str) -> Any:
        """Fallback when Ollama isn't available - NOW WITH EXECUTION"""
        query_lower = query.lower()
        
        # Player queries - EXECUTE AND RETURN DATA
        if 'player' in query_lower or ('top' in query_lower and ('8' in query_lower or '50' in query_lower or 'rank' in query_lower)):
            # Determine how many players
            if '50' in query_lower:
                return self._execute_command('database', 'ask', 'top 50 players')
            elif '8' in query_lower:
                return self._execute_command('database', 'ask', 'top 8 players')
            else:
                return self._execute_command('database', 'ask', 'top 10 players')
        
        # Tournament queries - GET REAL DATA
        if 'tournament' in query_lower:
            if 'recent' in query_lower:
                return self._execute_command('database', 'ask', 'recent tournaments')
            elif 'next' in query_lower or 'upcoming' in query_lower:
                return self._execute_command('database', 'ask', 'upcoming tournaments')
            else:
                # Try to extract tournament ID
                import re
                match = re.search(r'\d+', query)
                if match:
                    return self._execute_command('database', 'ask', f'tournament {match.group()}')
                return self._execute_command('database', 'ask', 'tournaments')
        
        # Organization queries - GET REAL DATA
        if 'org' in query_lower or 'organization' in query_lower:
            if 'rank' in query_lower or 'top' in query_lower:
                return self._execute_command('database', 'ask', 'top organizations')
            return self._execute_command('database', 'ask', 'organizations')
        
        # Sync queries - ACTUALLY SYNC
        if 'sync' in query_lower:
            if 'now' in query_lower or 'run' in query_lower or 'start' in query_lower:
                return self._execute_command('sync', 'do', 'sync tournaments')
            else:
                return "Ready to sync. Say 'sync now' to start syncing."
        
        # Stats queries - GET REAL STATS
        if 'stat' in query_lower or 'count' in query_lower:
            return self._execute_command('database', 'ask', 'stats')
        
        # Service listing - still informational
        if 'service' in query_lower:
            services = list(self.service_memory.keys())
            return f"Available services ({len(services)}): {', '.join(services[:10])}"
        
        # Help - show what can be done
        if 'help' in query_lower or query_lower == '?':
            return """I can execute these commands:
• 'show top 8 players' - Shows actual player rankings
• 'recent tournaments' - Shows real tournament data
• 'show organizations' - Lists actual organizations  
• 'tournament 123' - Shows specific tournament
• 'sync now' - Starts actual sync
• 'stats' - Shows database statistics
            
I return REAL DATA, not just instructions!"""
        
        # Default - try to be smart
        return f"I can execute commands for you. Try: 'show top 8 players' or 'recent tournaments'"
    
    def ask(self, query: str) -> str:
        """
        Natural language query about services
        
        Args:
            query: Natural language question
            
        Returns:
            Answer based on known services
        """
        # Build context with relevant services
        context = self._build_context(query)
        
        # Create prompt
        prompt = f"""{context}

User Question: {query}

Based on the available services, provide a helpful answer. Be specific about which service to use and how.
If you mention a service method, show the exact syntax like: service.method('parameters')
Keep your response concise and practical."""
        
        # Query Ollama
        response = self._query_ollama(prompt)
        
        # Update our announcement to show we're active
        if len(self.announcement_history) % 10 == 0:
            self._announce()
        
        return response
    
    def tell(self, format: str, data: Any = None) -> str:
        """
        Format data for output
        
        Args:
            format: Output format (json, discord, text, html)
            data: Data to format
            
        Returns:
            Formatted string
        """
        if format == 'json':
            if isinstance(data, str):
                return json.dumps({'response': data})
            return json.dumps(data, default=str, indent=2)
        
        elif format == 'discord':
            if isinstance(data, dict):
                return f"```json\n{json.dumps(data, indent=2)}\n```"
            return f"**{data}**"
        
        elif format == 'html':
            if isinstance(data, dict):
                html = "<div class='ollama-response'>"
                for key, value in data.items():
                    html += f"<p><strong>{key}:</strong> {value}</p>"
                html += "</div>"
                return html
            return f"<p>{data}</p>"
        
        else:
            return str(data)
    
    def do(self, action: str) -> Any:
        """
        Perform an action
        
        Args:
            action: Natural language action description
            
        Returns:
            Result of action
        """
        action_lower = action.lower()
        
        if 'analyze' in action_lower:
            # Analyze service landscape
            analysis = {
                'total_services': len(self.service_memory),
                'total_announcements': len(self.announcement_history),
                'service_categories': {},
                'most_active': None,
                'recommendations': []
            }
            
            # Categorize services
            for service_name in self.service_memory:
                category = self._categorize_service(service_name)
                if category not in analysis['service_categories']:
                    analysis['service_categories'][category] = []
                analysis['service_categories'][category].append(service_name)
            
            # Find most active
            if self.service_memory:
                most_active = max(self.service_memory.items(), 
                                key=lambda x: x[1]['announcement_count'])
                analysis['most_active'] = most_active[0]
            
            # Add recommendations
            if 'database' not in str(self.service_memory).lower():
                analysis['recommendations'].append("No database service found - data persistence may be an issue")
            if 'sync' not in str(self.service_memory).lower():
                analysis['recommendations'].append("No sync service found - consider starting sync service")
            
            return analysis
        
        elif 'discover' in action_lower or 'refresh' in action_lower:
            # Re-discover services
            self._subscribe_to_bonjour()
            return f"Refreshed - found {len(self.service_memory)} services"
        
        elif 'memory' in action_lower or 'history' in action_lower:
            # Show memory stats
            return {
                'services_tracked': len(self.service_memory),
                'announcements_seen': len(self.announcement_history),
                'oldest_service': min(self.service_memory.items(), 
                                     key=lambda x: x[1]['first_seen'])[0] if self.service_memory else None,
                'newest_service': max(self.service_memory.items(),
                                     key=lambda x: x[1]['first_seen'])[0] if self.service_memory else None
            }
        
        elif 'help' in action_lower:
            return """I can:
- ask('question') - Answer questions about services
- tell('format', data) - Format responses
- do('analyze') - Analyze service landscape
- do('refresh') - Re-discover services
- do('memory') - Show memory statistics"""
        
        else:
            # Try to understand as a goal and suggest actions
            return self._suggest_actions_for_goal(action)
    
    def _categorize_service(self, service_name: str) -> str:
        """Categorize a service based on its name"""
        name_lower = service_name.lower()
        
        if 'database' in name_lower or 'db' in name_lower:
            return 'Data'
        elif 'sync' in name_lower or 'api' in name_lower:
            return 'Integration'
        elif 'audio' in name_lower or 'voice' in name_lower:
            return 'Audio'
        elif 'visual' in name_lower or 'graph' in name_lower:
            return 'Visualization'
        elif 'editor' in name_lower or 'web' in name_lower:
            return 'Web'
        elif 'model' in name_lower:
            return 'Core'
        else:
            return 'Other'
    
    def _suggest_actions_for_goal(self, goal: str) -> List[Dict[str, str]]:
        """Suggest actions to achieve a goal"""
        suggestions = []
        goal_lower = goal.lower()
        
        # Match goal to services
        for service_name, data in self.service_memory.items():
            service_text = f"{service_name} {' '.join(data['capabilities'])}".lower()
            
            # Check if service might help with goal
            if any(word in service_text for word in goal_lower.split() if len(word) > 3):
                # Find relevant capability
                for cap in data['capabilities']:
                    if 'ask(' in cap or 'do(' in cap or 'tell(' in cap:
                        suggestions.append({
                            'service': service_name,
                            'action': cap,
                            'reason': f"This service can help with {goal}"
                        })
                        break
        
        if not suggestions:
            suggestions.append({
                'service': 'Unknown',
                'action': 'Start relevant service first',
                'reason': f"No service found for: {goal}"
            })
        
        return suggestions[:3]  # Return top 3 suggestions


# Singleton instance
_instance = None

def get_ollama_bonjour(model='mistral'):
    """Get or create the Ollama Bonjour service instance"""
    global _instance
    if _instance is None:
        _instance = OllamaBonjour(model=model)
    return _instance

if __name__ == "__main__":
    # Run as standalone service
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'  # Simpler format for interactive mode
    )
    
    print("\n" + "="*60)
    print("🤖 Ollama Bonjour - Claude's Little Brother")
    print("="*60)
    
    service = get_ollama_bonjour()
    
    print(f"\n📊 Status:")
    print(f"  Model: {service.model}")
    print(f"  Ollama: {'✅ Running' if service.available else '⚠️ Not Available (install: curl -fsSL https://ollama.ai/install.sh | sh)'}")
    print(f"  Services discovered: {len(service.service_memory)}")
    
    if service.service_memory:
        print(f"\n📡 Discovered Services:")
        for name in list(service.service_memory.keys())[:5]:
            print(f"  - {name}")
        if len(service.service_memory) > 5:
            print(f"  ... and {len(service.service_memory) - 5} more")
    
    # Polymorphic mode detection - check if we have stdin
    import sys
    import select
    import time
    
    # Check if stdin is available (not in background)
    has_stdin = sys.stdin.isatty()
    
    if not has_stdin:
        # Running in background - become a service
        print("\n🔧 Running in service mode (no stdin detected)")
        print("📡 Ollama Bonjour is now listening for announcements...")
        print("✨ Service will process Bonjour events polymorphically")
        
        # Just keep running and processing announcements
        try:
            while True:
                time.sleep(10)  # Keep alive, processing happens via callbacks
        except KeyboardInterrupt:
            print("\n👋 Ollama Bonjour service shutting down")
            sys.exit(0)
    
    # Interactive mode (only if we have stdin)
    print("\n💬 Ask me anything about services! Examples:")
    print("  - 'What services are available?'")
    print("  - 'How do I sync tournaments?'")
    print("  - 'Show me the database service'")
    print("  - 'analyze' (analyze service landscape)")
    print("  - 'quit' to exit\n")
    
    while True:
        try:
            query = input("🤖 > ")
            if query.lower() in ['quit', 'exit', 'q']:
                break
            elif query.lower() in ['help', '?']:
                print("\nI understand natural language! Try asking:")
                print("  - Questions about specific services")
                print("  - How to accomplish tasks")
                print("  - Service relationships")
                print("  - 'analyze' for service analysis")
                print("  - 'memory' for memory stats\n")
                continue
            
            # Handle special commands
            if query.lower() == 'analyze':
                response = service.do("analyze services")
                print(f"\n📊 Service Analysis:")
                if isinstance(response, dict):
                    for key, value in response.items():
                        if key != 'service_categories':
                            print(f"  {key}: {value}")
                    if 'service_categories' in response:
                        print(f"  Categories:")
                        for cat, services in response['service_categories'].items():
                            print(f"    {cat}: {len(services)} services")
                else:
                    print(response)
            elif query.lower() == 'memory':
                response = service.do("memory")
                print(f"\n🧠 Memory Stats:")
                if isinstance(response, dict):
                    for key, value in response.items():
                        print(f"  {key}: {value}")
                else:
                    print(response)
            else:
                # Normal query - now returns REAL DATA
                response = service.ask(query)
                
                # Format the response nicely based on type
                if isinstance(response, list):
                    print(f"\n📊 Results ({len(response)} items):")
                    for i, item in enumerate(response[:20], 1):  # Show first 20
                        if isinstance(item, dict):
                            # Format dict items nicely
                            name = item.get('name', item.get('tag', item.get('tournament_name', str(item))))
                            print(f"  {i}. {name}")
                        else:
                            print(f"  {i}. {item}")
                    if len(response) > 20:
                        print(f"  ... and {len(response) - 20} more")
                elif isinstance(response, dict):
                    print(f"\n📊 Data:")
                    for key, value in response.items():
                        print(f"  {key}: {value}")
                elif isinstance(response, str) and len(response) > 500:
                    # Long string - might be formatted output
                    print(f"\n{response[:500]}...")
                    print(f"  ... ({len(response)} total characters)")
                else:
                    print(f"\n💡 {response}")
            
            print()  # Extra line for readability
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
    
    print("\n👋 Ollama Bonjour Service Stopped")