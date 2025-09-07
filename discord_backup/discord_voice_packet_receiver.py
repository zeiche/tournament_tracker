#!/usr/bin/env python3
"""
discord_voice_packet_receiver.py - Receives raw voice packets from Discord
Hooks into Discord's voice websocket to get opus packets
Announces OPUS_PACKET for each received packet
"""

import asyncio
import discord
from capability_announcer import announcer
from capability_discovery import register_capability

class VoicePacketReceiver:
    """Receives voice packets from Discord and announces them"""
    
    def __init__(self, voice_client):
        """Initialize with a Discord voice client"""
        self.voice_client = voice_client
        self.receiving = False
        
        announcer.announce(
            "VoicePacketReceiver",
            [
                "I receive raw voice packets from Discord",
                "I announce OPUS_PACKET for each packet",
                "I bridge Discord voice to the Bonjour system"
            ]
        )
        
    def start_receiving(self):
        """Start receiving voice packets"""
        if not self.voice_client or not self.voice_client.is_connected():
            return False
            
        # Hook into the voice client's ws to get packets
        # This is a bit hacky but discord.py doesn't expose voice receiving
        try:
            ws = self.voice_client.ws
            if ws:
                # Store original handler
                original_handler = ws.received_message
                
                # Create our interceptor
                async def packet_interceptor(msg):
                    """Intercept voice packets"""
                    # Check if it's an RTP packet (voice data)
                    if len(msg) > 12:  # RTP header is 12 bytes minimum
                        # Extract some RTP info
                        # Byte 0-1: RTP header
                        # Byte 2-3: Sequence number
                        # Byte 4-7: Timestamp
                        # Byte 8-11: SSRC (identifies the user)
                        # Byte 12+: Opus payload
                        
                        if len(msg) > 12:
                            ssrc = int.from_bytes(msg[8:12], 'big')
                            opus_data = msg[12:]
                            
                            # Announce the opus packet
                            announcer.announce(
                                "OPUS_PACKET",
                                {
                                    'packet': opus_data,
                                    'ssrc': ssrc,
                                    'user_id': ssrc,  # SSRC maps to user
                                    'guild_id': self.voice_client.guild.id if hasattr(self.voice_client, 'guild') else 0,
                                    'size': len(opus_data)
                                }
                            )
                    
                    # Call original handler
                    if original_handler:
                        await original_handler(msg)
                
                # Replace handler
                ws.received_message = packet_interceptor
                self.receiving = True
                
                announcer.announce(
                    "VoicePacketReceiver",
                    ["Started receiving voice packets"]
                )
                return True
                
        except Exception as e:
            announcer.announce(
                "VoicePacketReceiver",
                [f"Failed to hook voice packets: {e}"]
            )
            return False
            
    def stop_receiving(self):
        """Stop receiving voice packets"""
        self.receiving = False
        announcer.announce(
            "VoicePacketReceiver",
            ["Stopped receiving voice packets"]
        )


# Function to inject packet receiving into an existing voice client
def enable_voice_packet_receiving(voice_client):
    """Enable packet receiving on a voice client"""
    if not voice_client:
        return None
        
    receiver = VoicePacketReceiver(voice_client)
    if receiver.start_receiving():
        return receiver
    return None


# Alternative: Create a custom voice protocol that announces packets
class AnnouncingVoiceProtocol(discord.VoiceProtocol):
    """Voice protocol that announces received packets"""
    
    def __init__(self, client, channel):
        super().__init__(client, channel)
        self.packets_received = 0
        
    async def on_voice_server_update(self, data):
        """Handle voice server update"""
        await super().on_voice_server_update(data)
        
    async def on_voice_state_update(self, data):
        """Handle voice state update"""
        await super().on_voice_state_update(data)
        
    def received_packet(self, data):
        """Called when a voice packet is received"""
        self.packets_received += 1
        
        # Announce the packet
        if len(data) > 12:
            opus_data = data[12:]  # Skip RTP header
            announcer.announce(
                "OPUS_PACKET",
                {
                    'packet': opus_data,
                    'packet_number': self.packets_received,
                    'size': len(opus_data)
                }
            )


if __name__ == "__main__":
    print("Voice Packet Receiver module")
    print("This module hooks into Discord voice to receive packets")
    print("Import and use enable_voice_packet_receiving() with a voice client")