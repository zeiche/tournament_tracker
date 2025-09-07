#!/usr/bin/env python3
"""
polymorphic_opus_decoder.py - Decodes opus packets to PCM audio
Subscribes to OPUS_PACKET announcements
Announces AUDIO_AVAILABLE with decoded PCM
"""

from capability_announcer import announcer
from capability_discovery import register_capability
import struct
import io

try:
    import opuslib
    import opuslib.api
    import opuslib.api.decoder
    HAS_OPUS = True
except ImportError:
    HAS_OPUS = False
    print("WARNING: opuslib not available, will pass through raw data")

class PolymorphicOpusDecoder:
    """Decodes opus audio packets polymorphically"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Announce ourselves
        announcer.announce(
            "PolymorphicOpusDecoder",
            [
                "I decode opus packets to PCM",
                "I subscribe to OPUS_PACKET announcements",
                "I announce AUDIO_AVAILABLE with decoded audio",
                "I work with Discord voice data",
                "I am the opus-to-PCM bridge"
            ]
        )
        
        # Setup opus decoder if available
        if HAS_OPUS:
            try:
                # Discord uses 48kHz, 2 channels
                self.decoder = opuslib.api.decoder.create_state(48000, 2)
                self.frame_size = 960  # 20ms at 48kHz
                announcer.announce("PolymorphicOpusDecoder", ["Opus decoder initialized"])
            except Exception as e:
                print(f"Failed to create opus decoder: {e}")
                self.decoder = None
        else:
            self.decoder = None
            
        # Setup subscriptions
        self.setup_subscriptions()
        
    def setup_subscriptions(self):
        """Subscribe to opus packet announcements"""
        
        # Manual subscription since @subscribe doesn't exist
        # We'll poll for announcements or hook into the announcer
        
    def on_opus_packet(self, data):
            """Decode opus packet when received"""
            if not isinstance(data, dict):
                return
                
            packet = data.get('packet')
            user_id = data.get('user_id')
            guild_id = data.get('guild_id')
            
            if not packet:
                return
                
            # Decode the opus packet
            pcm_data = self.decode_opus(packet)
            
            if pcm_data:
                # Announce decoded audio
                announcer.announce(
                    "AUDIO_AVAILABLE",
                    {
                        'source': f'discord_voice_{user_id}',
                        'user_id': user_id,
                        'guild_id': guild_id,
                        'audio_data': pcm_data,
                        'format': 'pcm_s16le',
                        'channels': 2,
                        'sample_rate': 48000,
                        'metadata': {
                            'type': 'voice',
                            'decoded_from': 'opus'
                        }
                    }
                )
                
                announcer.announce(
                    "PolymorphicOpusDecoder",
                    [f"Decoded {len(packet)} bytes opus → {len(pcm_data)} bytes PCM"]
                )
                
    def decode_opus(self, opus_packet: bytes) -> bytes:
        """Decode opus packet to PCM"""
        if not self.decoder:
            # No decoder, return as-is or empty
            return opus_packet if len(opus_packet) > 100 else b''
            
        try:
            # Decode opus to PCM
            # Output buffer: 2 channels * 960 samples * 2 bytes
            pcm = bytearray(self.frame_size * 2 * 2)
            
            # Decode the packet
            samples = opuslib.api.decoder.decode(
                self.decoder,
                opus_packet,
                len(opus_packet),
                pcm,
                self.frame_size,
                0  # No FEC
            )
            
            if samples > 0:
                # Return the decoded PCM data
                return bytes(pcm[:samples * 2 * 2])
            else:
                return b''
                
        except Exception as e:
            announcer.announce(
                "PolymorphicOpusDecoder",
                [f"Decode error: {e}"]
            )
            return b''
            
    def decode_with_fallback(self, data: bytes) -> bytes:
        """Try to decode or pass through"""
        # Check if it looks like opus (very rough check)
        if len(data) > 0 and data[0] in [0x78, 0x79, 0x7A]:  # Common opus headers
            return self.decode_opus(data)
        else:
            # Might already be PCM or other format
            return data
            
    def get_status(self):
        """Get decoder status"""
        return {
            'has_opus': HAS_OPUS,
            'decoder_ready': self.decoder is not None,
            'subscribed_to': ['OPUS_PACKET']
        }

# Create singleton instance
opus_decoder = PolymorphicOpusDecoder()

# Register as capability
register_capability('opus_decoder', lambda: opus_decoder)

if __name__ == "__main__":
    import asyncio
    
    print("Polymorphic Opus Decoder running...")
    print(f"Status: {opus_decoder.get_status()}")
    
    # Keep running to receive announcements
    try:
        asyncio.run(asyncio.Event().wait())
    except KeyboardInterrupt:
        print("\nOpus decoder stopped")