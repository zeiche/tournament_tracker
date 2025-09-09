#!/usr/bin/env python3
"""
Bridge Services Module - Organized collection of all bridge services

Bridges connect different services together:
- Discord ↔ Claude
- Discord ↔ Lightweight Intelligence  
- Discord ↔ Ollama
- Bonjour ↔ Services
- Twilio ↔ Services
- Audio ↔ Transcription

All bridges follow the polymorphic pattern and announce via Bonjour.
"""

from .base_bridge import BaseBridge, BridgeRegistry

__all__ = ['BaseBridge', 'BridgeRegistry']