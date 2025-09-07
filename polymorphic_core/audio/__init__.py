"""
polymorphic audio subsystem - handles all audio polymorphically
doesn't care about tournaments, just audio
"""

from .audio_player import PolymorphicAudioPlayer
from .audio_provider import PolymorphicAudioProvider
from .audio_request import PolymorphicAudioRequest
from .opus_decoder import PolymorphicOpusDecoder
from .transcription import PolymorphicTranscription
from .tts_service import PolymorphicTTSService

__all__ = [
    'PolymorphicAudioPlayer',
    'PolymorphicAudioProvider',
    'PolymorphicAudioRequest',
    'PolymorphicOpusDecoder',
    'PolymorphicTranscription',
    'PolymorphicTTSService'
]