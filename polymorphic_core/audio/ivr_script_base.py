#!/usr/bin/env python3
"""
IVR Script Base Classes - Full Python scripting for IVR
Allows complex audio/timing logic, not just state transitions
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ScriptResponse:
    """Response from script execution"""
    action: str  # 'speak', 'play_audio', 'wait', 'hangup', 'continue'
    content: str = ""
    duration: float = 0.0
    volume: float = 1.0
    loop: bool = False
    next_handler: Optional[str] = None

class IVRScriptBase(ABC):
    """Base class for full-featured IVR scripts"""
    
    def __init__(self, name: str):
        self.name = name
        self.call_states = {}  # call_id -> state_data
    
    @abstractmethod
    async def on_call_start(self, call_id: str, ivr_service, audio_mixer, context: Dict[str, Any]) -> ScriptResponse:
        """Called when call starts - handle intro sequence"""
        pass
    
    @abstractmethod
    async def on_dtmf_input(self, call_id: str, digit: str, ivr_service, audio_mixer) -> ScriptResponse:
        """Called when DTMF digit detected"""
        pass
    
    @abstractmethod
    async def on_speech_input(self, call_id: str, text: str, ivr_service, audio_mixer) -> ScriptResponse:
        """Called when speech detected"""
        pass
    
    async def on_call_end(self, call_id: str, ivr_service, audio_mixer):
        """Called when call ends - cleanup"""
        if call_id in self.call_states:
            del self.call_states[call_id]
    
    def get_call_state(self, call_id: str) -> Dict[str, Any]:
        """Get state for specific call"""
        return self.call_states.get(call_id, {})
    
    def set_call_state(self, call_id: str, state: Dict[str, Any]):
        """Set state for specific call"""
        self.call_states[call_id] = state

class SequencedIVRScript(IVRScriptBase):
    """IVR script that can handle complex audio sequences with timing"""
    
    async def execute_audio_sequence(self, call_id: str, sequence: list, ivr_service, audio_mixer):
        """Execute a sequence of audio/timing commands"""
        for step in sequence:
            action = step.get('action')
            
            if action == 'play_music':
                audio_file = step.get('file')
                volume = step.get('volume', 1.0)
                loop = step.get('loop', False)
                await audio_mixer.play_audio(audio_file, volume=volume, loop=loop)
                
            elif action == 'wait':
                duration = step.get('duration', 1.0)
                await asyncio.sleep(duration)
                
            elif action == 'speak':
                text = step.get('text', '')
                await ivr_service.speak(call_id, text)
                
            elif action == 'stop_music':
                music_type = step.get('type', 'all')
                await audio_mixer.stop_music(music_type)
                
            elif action == 'fade_music':
                target_volume = step.get('volume', 0.0)
                duration = step.get('duration', 1.0)
                await audio_mixer.fade_to_volume(target_volume, duration)

class MenuBasedIVRScript(SequencedIVRScript):
    """IVR script with traditional menu structure but enhanced audio control"""
    
    def __init__(self, name: str, menu_config: Dict[str, Any]):
        super().__init__(name)
        self.menu_config = menu_config
    
    async def play_menu_prompt(self, call_id: str, menu_name: str, ivr_service, audio_mixer):
        """Play menu prompt with audio management"""
        menu = self.menu_config.get(menu_name, {})
        
        # Execute audio sequence for this menu
        sequence = menu.get('audio_sequence', [])
        if sequence:
            await self.execute_audio_sequence(call_id, sequence, ivr_service, audio_mixer)
        
        # Speak the prompt
        prompt = menu.get('prompt', '')
        if prompt:
            await ivr_service.speak(call_id, prompt)

if __name__ == "__main__":
    print("🎬 IVR Script Base Classes loaded")
    print("📝 Ready for full Python IVR scripting")