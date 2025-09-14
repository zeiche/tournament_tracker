#!/usr/bin/env python3
"""
Bonjour Media Stream Service - WebSocket-based real-time media streaming
Refactored from Twilio WebSocket pattern for generic media streaming with JSON metadata
"""

import base64
import json
import logging
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("services.bonjour_media_stream_service")

from polymorphic_core.local_bonjour import local_announcer
from polymorphic_core.service_locator import get_service
from logging_services.polymorphic_log_manager import get_log_manager


class BonjourMediaStreamService:
    """WebSocket-based media streaming service with JSON metadata handling"""
    
    def __init__(self, port: int = 8095):
        self.port = port
        self.active_connections = {}
        self.message_handlers = {
            'connected': self._handle_connected,
            'start': self._handle_start,
            'media': self._handle_media,
            'metadata': self._handle_metadata,
            'closed': self._handle_closed
        }
        
        # Get services via service locator
        self.log_manager = get_log_manager()
        
        # Announce to bonjour
        local_announcer.announce("BonjourMediaStreamService", [
            "I stream real-time media via WebSockets",
            "I handle JSON metadata for media streams", 
            "I decode base64 media payloads",
            "I integrate with polymorphic logging",
            "I provide media streaming endpoints",
            f"I run on port {self.port}"
        ])
    
    async def handle_websocket(self, websocket, path):
        """Handle WebSocket connection for media streaming"""
        connection_id = f"conn_{int(time.time())}"
        self.active_connections[connection_id] = {
            'websocket': websocket,
            'start_time': time.time(),
            'message_count': 0,
            'has_seen_media': False,
            'metadata': {}
        }
        
        self.log_manager.info(f"WebSocket connection accepted: {connection_id}")
        
        try:
            async for message in websocket:
                await self._process_message(connection_id, message)
        except Exception as e:
            self.log_manager.error(f"WebSocket error for {connection_id}: {e}")
        finally:
            await self._cleanup_connection(connection_id)
    
    async def _process_message(self, connection_id: str, message: str):
        """Process incoming WebSocket message"""
        conn = self.active_connections[connection_id]
        conn['message_count'] += 1
        
        try:
            # All messages are JSON encoded
            data = json.loads(message)
            event = data.get('event', 'unknown')
            
            # Route to appropriate handler
            if event in self.message_handlers:
                await self.message_handlers[event](connection_id, data)
            else:
                self.log_manager.warning(f"Unknown event type: {event}")
                
        except json.JSONDecodeError as e:
            self.log_manager.error(f"Invalid JSON message: {e}")
        except Exception as e:
            self.log_manager.error(f"Message processing error: {e}")
    
    async def _handle_connected(self, connection_id: str, data: Dict[str, Any]):
        """Handle connection event"""
        self.log_manager.info(f"Connected event from {connection_id}: {data}")
        
        # Log connection with metadata
        self.log_manager.info("Media stream connection established", data={
            'connection_id': connection_id,
            'event': 'connected',
            'timestamp': datetime.now().isoformat(),
            'client_info': data.get('client', {})
        })
    
    async def _handle_start(self, connection_id: str, data: Dict[str, Any]):
        """Handle stream start event"""
        self.log_manager.info(f"Stream start event from {connection_id}")
        
        # Extract stream metadata
        stream_info = data.get('stream', {})
        self.active_connections[connection_id]['metadata'] = stream_info
        
        # Log stream start with full metadata
        self.log_manager.info("Media stream started", data={
            'connection_id': connection_id,
            'event': 'start',
            'stream_name': stream_info.get('name', 'unnamed'),
            'audio_type': stream_info.get('audioType', 'unknown'),
            'sample_rate': stream_info.get('sampleRate', 0),
            'channels': stream_info.get('channels', 0),
            'timestamp': datetime.now().isoformat()
        })
    
    async def _handle_media(self, connection_id: str, data: Dict[str, Any]):
        """Handle media data event"""
        conn = self.active_connections[connection_id]
        
        if not conn['has_seen_media']:
            # Log first media message with details
            media_data = data.get('media', {})
            payload = media_data.get('payload', '')
            
            try:
                # Decode base64 media payload
                chunk = base64.b64decode(payload)
                chunk_size = len(chunk)
                
                self.log_manager.info(f"First media chunk received: {chunk_size} bytes")
                
                # Create media stream object for logging
                from services.web_session_recorder import VideoStream
                
                # Log media stream with visualization
                media_stream = VideoStream(
                    video_data=chunk,
                    url=f"websocket://{connection_id}",
                    session_name=f"stream_{connection_id}",
                    duration=1,  # Will be updated when stream ends
                    content_type="audio/wav"  # Or detect from metadata
                )
                
                self.log_manager.info("WebSocket media stream chunk", data=media_stream)
                
                conn['has_seen_media'] = True
                self.log_manager.info("Suppressing additional media messages for this connection")
                
            except Exception as e:
                self.log_manager.error(f"Media processing error: {e}")
    
    async def _handle_metadata(self, connection_id: str, data: Dict[str, Any]):
        """Handle metadata event (custom extension)"""
        metadata = data.get('metadata', {})
        conn = self.active_connections[connection_id]
        conn['metadata'].update(metadata)
        
        self.log_manager.info("Media stream metadata received", data={
            'connection_id': connection_id,
            'metadata': metadata,
            'timestamp': datetime.now().isoformat()
        })
    
    async def _handle_closed(self, connection_id: str, data: Dict[str, Any]):
        """Handle connection closed event"""
        conn = self.active_connections[connection_id]
        duration = time.time() - conn['start_time']
        
        # Log final stream statistics
        self.log_manager.info("Media stream closed", data={
            'connection_id': connection_id,
            'total_messages': conn['message_count'],
            'duration_seconds': round(duration, 2),
            'had_media': conn['has_seen_media'],
            'final_metadata': conn['metadata']
        })
    
    async def _cleanup_connection(self, connection_id: str):
        """Clean up connection resources"""
        if connection_id in self.active_connections:
            conn = self.active_connections[connection_id]
            duration = time.time() - conn['start_time']
            
            self.log_manager.info(
                f"Connection {connection_id} closed. "
                f"Received {conn['message_count']} messages over {duration:.2f}s"
            )
            
            del self.active_connections[connection_id]
    
    def start_server(self):
        """Start the WebSocket media streaming server"""
        try:
            import websockets
            
            self.log_manager.info(f"Starting Bonjour Media Stream Service on port {self.port}")
            
            # Start WebSocket server
            start_server = websockets.serve(self.handle_websocket, "localhost", self.port)
            
            self.log_manager.info(f"🎬 Bonjour Media Stream Service running on ws://localhost:{self.port}")
            
            return start_server
            
        except ImportError:
            self.log_manager.error("websockets library not installed. Run: pip install websockets")
            return None
        except Exception as e:
            self.log_manager.error(f"Failed to start media stream service: {e}")
            return None
    
    def ask(self, query: str, **kwargs) -> Any:
        """Query interface for bonjour service locator"""
        query_lower = query.lower().strip()
        
        if 'status' in query_lower:
            return {
                'service': 'BonjourMediaStreamService',
                'port': self.port,
                'active_connections': len(self.active_connections),
                'endpoints': ['/media'],
                'supported_events': list(self.message_handlers.keys())
            }
        elif 'connections' in query_lower:
            return list(self.active_connections.keys())
        elif 'stats' in query_lower:
            total_messages = sum(conn['message_count'] for conn in self.active_connections.values())
            return {
                'active_connections': len(self.active_connections),
                'total_messages_processed': total_messages
            }
        
        return f"Available queries: status, connections, stats"
    
    def tell(self, format_type: str, data: Any = None) -> str:
        """Format data for output"""
        if data is None:
            data = self.ask('status')
        
        if format_type == 'json':
            return json.dumps(data, indent=2)
        elif format_type == 'discord':
            if isinstance(data, dict) and 'service' in data:
                return f"🎬 **{data['service']}**\n📡 Port: {data['port']}\n🔗 Connections: {data['active_connections']}"
            return str(data)
        else:
            return str(data)
    
    def do(self, action: str, **kwargs) -> Any:
        """Perform actions via natural language"""
        action_lower = action.lower().strip()
        
        if 'start' in action_lower:
            return self.start_server()
        elif 'stop' in action_lower or 'shutdown' in action_lower:
            # Close all connections
            for conn_id in list(self.active_connections.keys()):
                asyncio.create_task(self._cleanup_connection(conn_id))
            return "Shutting down media stream service"
        
        return f"Available actions: start, stop"


# Service factory function
def get_media_stream_service(port: int = 8095) -> BonjourMediaStreamService:
    """Get or create media stream service instance"""
    return BonjourMediaStreamService(port=port)


if __name__ == '__main__':
    import asyncio
    
    # Create and start the service
    service = BonjourMediaStreamService()
    
    print("🎬 Bonjour Media Stream Service")
    print("📡 WebSocket endpoint: /media")  
    print("📊 Handles JSON metadata for real-time streaming")
    print("🔗 Integrates with polymorphic logging system")
    print("⏹️  Press Ctrl+C to stop")
    
    try:
        # Start server
        server = service.start_server()
        if server:
            asyncio.get_event_loop().run_until_complete(server)
            asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\n🛑 Service stopped")