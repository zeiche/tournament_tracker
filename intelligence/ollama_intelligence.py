#!/usr/bin/env python3
"""
Ollama Intelligence - Uses Ollama for local LLM inference
Supports multiple models including Llama, Mistral, Phi, etc.
"""

import json
import logging
from typing import Dict, List, Any, Optional
import subprocess
import requests
import sys
import os

# Add parent directory to path for polymorphic_core import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from polymorphic_core import announcer

from .base_intelligence import BaseIntelligence, ServiceUnderstanding, QueryResponse

logger = logging.getLogger('intelligence.ollama')

class OllamaIntelligence(BaseIntelligence):
    """
    Intelligence backend using Ollama for completely offline operation
    """
    
    def __init__(self, model='mistral', base_url='http://localhost:11434'):
        """
        Initialize Ollama intelligence
        
        Args:
            model: Model to use (mistral, llama2, phi, neural-chat, etc.)
            base_url: Ollama API endpoint
        """
        super().__init__()
        self.model = model
        self.base_url = base_url
        self.api_generate = f"{base_url}/api/generate"
        self.api_models = f"{base_url}/api/tags"
        
        # Check if Ollama is running
        try:
            self._check_ollama()
            self.available = True
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self.available = False
        
        # System prompt for Bonjour understanding
        self.system_prompt = """You are an intelligent service discovery assistant. 
You understand Bonjour/mDNS service announcements and can reason about how different services work together.
You work offline and help users understand and use discovered services.
Be concise and practical in your responses."""
        
        # Announce ourselves via Bonjour
        self._announce_service()
        
        # Subscribe to service announcements
        self._subscribe_to_announcements()
    
    def _check_ollama(self):
        """Check if Ollama is running and model is available"""
        try:
            # Check if Ollama is running
            response = requests.get(self.api_models, timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'].split(':')[0] for m in models]
                
                if self.model not in model_names:
                    logger.warning(f"Model {self.model} not found. Available: {model_names}")
                    logger.info(f"Pulling {self.model} model...")
                    self._pull_model(self.model)
                else:
                    logger.info(f"Ollama is running with {self.model} model")
            else:
                raise ConnectionError("Ollama API not responding")
                
        except requests.exceptions.RequestException:
            logger.warning("Ollama not running. Attempting to start...")
            self._start_ollama()
    
    def _start_ollama(self):
        """Attempt to start Ollama service"""
        try:
            # Try to start Ollama
            subprocess.run(['ollama', 'serve'], 
                         capture_output=True, 
                         timeout=2,
                         check=False)
        except Exception as e:
            logger.error(f"Could not start Ollama: {e}")
            logger.info("Please install Ollama: curl -fsSL https://ollama.ai/install.sh | sh")
            raise RuntimeError("Ollama not available")
    
    def _pull_model(self, model: str):
        """Pull a model if not available"""
        try:
            logger.info(f"Downloading {model} model (this may take a few minutes)...")
            result = subprocess.run(['ollama', 'pull', model],
                                  capture_output=True,
                                  text=True,
                                  timeout=600)  # 10 minute timeout
            if result.returncode == 0:
                logger.info(f"Successfully downloaded {model}")
            else:
                logger.error(f"Failed to download {model}: {result.stderr}")
        except Exception as e:
            logger.error(f"Could not pull model: {e}")
    
    def _generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate text using Ollama API"""
        try:
            payload = {
                'model': self.model,
                'prompt': f"{self.system_prompt}\n\n{prompt}",
                'temperature': temperature,
                'stream': False
            }
            
            response = requests.post(self.api_generate, 
                                    json=payload,
                                    timeout=30)
            
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return ""
    
    def understand_service(self, name: str, capabilities: List[str]) -> ServiceUnderstanding:
        """Use Ollama to understand a service announcement"""
        
        prompt = f"""A service named "{name}" just announced itself with these capabilities:
{json.dumps(capabilities, indent=2)}

Based on this announcement:
1. What type of service is this?
2. What can it be used for? (list 3 uses)
3. What other services might it work well with?
4. Rate your confidence in understanding this service (0-100%)

Respond in JSON format:
{{
    "service_type": "...",
    "suggested_uses": ["use1", "use2", "use3"],
    "relationships": ["works with X", "complements Y"],
    "confidence": 85
}}"""

        response = self._generate(prompt, temperature=0.3)
        
        # Parse response
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                # Fallback parsing
                data = {
                    'service_type': name,
                    'suggested_uses': self._extract_uses_fallback(response),
                    'relationships': self._extract_relationships_fallback(response),
                    'confidence': 70
                }
        except Exception as e:
            logger.warning(f"Could not parse Ollama response: {e}")
            # Fallback to pattern matching
            data = self._fallback_understanding(name, capabilities)
        
        return ServiceUnderstanding(
            service_name=name,
            capabilities=capabilities,
            suggested_uses=data.get('suggested_uses', []),
            relationships=data.get('relationships', []),
            confidence=data.get('confidence', 50) / 100.0
        )
    
    def query(self, question: str) -> QueryResponse:
        """Answer a question using Ollama and service knowledge"""
        
        # Build context from discovered services
        context = "Available services:\n"
        for name, data in self.discovered_services.items():
            context += f"- {name}: {', '.join(data['capabilities'][:3])}\n"
        
        prompt = f"""{context}

User question: {question}

Provide a helpful answer based on the available services. Include:
1. Direct answer to the question
2. Which services are relevant
3. Suggested follow-up actions

Keep the response concise and practical."""

        response = self._generate(prompt)
        
        # Extract relevant services from response
        relevant_services = []
        for service_name in self.discovered_services.keys():
            if service_name.lower() in response.lower():
                relevant_services.append(service_name)
        
        return QueryResponse(
            answer=response,
            confidence=0.8 if response else 0.0,
            sources=relevant_services,
            suggestions=self._extract_suggestions(response)
        )
    
    def suggest_action(self, goal: str) -> List[Dict[str, Any]]:
        """Suggest actions using Ollama reasoning"""
        
        context = json.dumps(self.get_service_map(), indent=2)
        
        prompt = f"""Given these available services:
{context}

Goal: {goal}

Suggest a sequence of actions to achieve this goal. For each action, specify:
1. Which service to use
2. What method to call (ask/tell/do)
3. What parameters to pass

Respond with a JSON array of actions."""

        response = self._generate(prompt, temperature=0.5)
        
        try:
            # Extract JSON array
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        
        # Fallback
        return [{
            'service': 'unknown',
            'method': 'ask',
            'params': goal
        }]
    
    def _fallback_understanding(self, name: str, capabilities: List[str]) -> Dict:
        """Fallback understanding using simple patterns"""
        uses = []
        relationships = []
        
        name_lower = name.lower()
        caps_text = ' '.join(capabilities).lower()
        
        # Detect service type and suggest uses
        if 'database' in name_lower or 'db' in name_lower:
            uses = ['Query tournament data', 'Store results', 'Manage players']
            relationships = ['Works with sync service', 'Feeds visualizer']
        elif 'sync' in name_lower:
            uses = ['Update data from APIs', 'Synchronize tournaments', 'Refresh standings']
            relationships = ['Updates database', 'Triggers notifications']
        elif 'visual' in name_lower or 'graph' in name_lower:
            uses = ['Create heat maps', 'Generate reports', 'Build charts']
            relationships = ['Reads from database', 'Exports to web']
        elif 'audio' in name_lower:
            uses = ['Play sounds', 'Process voice', 'Generate speech']
            relationships = ['Works with Discord', 'Handles notifications']
        
        return {
            'service_type': name,
            'suggested_uses': uses or ['Process data', 'Handle requests', 'Provide service'],
            'relationships': relationships or ['Standalone service'],
            'confidence': 60 if uses else 40
        }
    
    def _extract_uses_fallback(self, text: str) -> List[str]:
        """Extract uses from free text"""
        uses = []
        lines = text.split('\n')
        for line in lines:
            if any(marker in line for marker in ['-', '*', '•', '1.', '2.', '3.']):
                use = line.strip().lstrip('-*•123. ')
                if len(use) > 5:
                    uses.append(use)
        return uses[:3] if uses else ['General service functionality']
    
    def _extract_relationships_fallback(self, text: str) -> List[str]:
        """Extract relationships from free text"""
        relationships = []
        keywords = ['works with', 'complements', 'integrates', 'connects', 'uses']
        
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                # Find the context around the keyword
                idx = text_lower.index(keyword)
                snippet = text[max(0, idx-20):min(len(text), idx+50)]
                relationships.append(snippet.strip())
        
        return relationships[:2] if relationships else []
    
    def _extract_suggestions(self, text: str) -> List[str]:
        """Extract suggestions from response text"""
        suggestions = []
        
        # Look for action words
        action_indicators = ['try', 'you can', 'you could', 'consider', 'use']
        
        lines = text.split('.')
        for line in lines:
            line_lower = line.lower()
            if any(indicator in line_lower for indicator in action_indicators):
                suggestion = line.strip()
                if len(suggestion) > 10:
                    suggestions.append(suggestion)
        
        return suggestions[:3]
    
    def _announce_service(self):
        """Announce Ollama Intelligence via Bonjour"""
        capabilities = [
            f"Ollama Intelligence - Claude's little brother",
            f"Model: {self.model} (offline, no API keys needed)",
            "I understand Bonjour service announcements",
            "I can reason about service relationships",
            "I work completely offline - no internet required",
            "ask('how do I sync tournaments?') - Natural language queries",
            "tell('discord', response) - Format responses",
            "do('analyze services') - Analyze discovered services",
            "I am Claude's offline assistant for local intelligence"
        ]
        
        if self.available:
            capabilities.append("✅ Ollama is running and ready")
        else:
            capabilities.append("⚠️ Ollama not running - install with: curl -fsSL https://ollama.ai/install.sh | sh")
        
        announcer.announce("Ollama Intelligence", capabilities)
    
    def _subscribe_to_announcements(self):
        """Subscribe to Bonjour service announcements"""
        # Monitor all existing announcements
        for announcement in announcer.announcements:
            service_name = announcement.get('service', 'Unknown')
            capabilities = announcement.get('capabilities', [])
            
            # Store in our discovered services
            self.discovered_services[service_name] = {
                'capabilities': capabilities,
                'timestamp': None
            }
            
            # Log that we've discovered a service
            logger.info(f"Ollama discovered service: {service_name}")
    
    def ask(self, query: str, **kwargs) -> Any:
        """Polymorphic ask method for natural language queries"""
        if not self.available:
            return "Ollama is not running. Install with: curl -fsSL https://ollama.ai/install.sh | sh"
        
        return self.query(query)
    
    def tell(self, format: str, data: Any = None) -> str:
        """Polymorphic tell method for formatting responses"""
        if format == 'discord':
            if isinstance(data, QueryResponse):
                response = f"**{data.answer}**\n"
                if data.sources:
                    response += f"\n*Sources: {', '.join(data.sources)}*"
                return response
            return str(data)
        elif format == 'json':
            if hasattr(data, '__dict__'):
                return json.dumps(data.__dict__, indent=2)
            return json.dumps(data, indent=2)
        else:
            return str(data)
    
    def do(self, action: str, **kwargs) -> Any:
        """Polymorphic do method for performing actions"""
        action_lower = action.lower()
        
        if 'analyze' in action_lower:
            # Analyze all discovered services
            analysis = []
            for name, data in self.discovered_services.items():
                understanding = self.understand_service(name, data['capabilities'])
                analysis.append({
                    'service': name,
                    'type': understanding.suggested_uses[0] if understanding.suggested_uses else 'Unknown',
                    'confidence': understanding.confidence
                })
            return analysis
        
        elif 'suggest' in action_lower:
            # Extract goal from action
            goal = action.replace('suggest', '').strip()
            return self.suggest_action(goal)
        
        elif 'discover' in action_lower:
            # Re-discover services
            self._subscribe_to_announcements()
            return f"Discovered {len(self.discovered_services)} services"
        
        else:
            # Try to understand as a goal
            return self.suggest_action(action)