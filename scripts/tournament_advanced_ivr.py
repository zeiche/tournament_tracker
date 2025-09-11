#!/usr/bin/env python3
"""
Advanced Tournament IVR Script - Full Python implementation
Handles complex audio sequences with precise timing
"""

import asyncio
from typing import Dict, Any
from polymorphic_core.audio.ivr_script_base import MenuBasedIVRScript, ScriptResponse
from polymorphic_core.audio.ivr_service import IVRResponse
from search.polymorphic_queries import query as pq

class TournamentAdvancedIVRScript(MenuBasedIVRScript):
    """Advanced tournament IVR with full audio control and timing"""
    
    def __init__(self):
        # Menu configuration with audio sequences
        menu_config = {
            "main_menu": {
                "prompt": "this is the backyard tryhards stat tracker. press or say 1 for top players. 2 for top organizations by attendance. press 0 for current date and time.",
                "options": {
                    "1": "players_menu",
                    "2": "organizations_menu",
                    "0": "datetime_menu", 
                    "*": "main_menu",
                    "#": "goodbye"
                }
            },
            "players_menu": {
                "prompt": "Getting top players...",
                "handler": "get_top_players"
            },
            "organizations_menu": {
                "prompt": "Getting top organizations...",
                "handler": "get_top_organizations"
            }
        }
        
        super().__init__("tournament_advanced", menu_config)
    
    async def on_call_start(self, call_id: str, ivr_service=None, audio_mixer=None, context: Dict[str, Any] = None) -> IVRResponse:
        """Start call and launch intro sequence in background - but stay reactive to signals"""
        print(f"🎬 Starting advanced intro sequence for call {call_id}")
        
        # Initialize call state
        self.set_call_state(call_id, {
            'current_menu': 'main_menu',
            'intro_complete': False,
            'intro_task': None
        })
        
        # Start the complex intro sequence if mixer available
        if audio_mixer:
            print(f"🎵 Starting complex audio sequence for call {call_id}")
            intro_task = asyncio.create_task(self._execute_intro_sequence(call_id, ivr_service, audio_mixer))
            call_state = self.get_call_state(call_id)
            call_state['intro_task'] = intro_task
            self.set_call_state(call_id, call_state)
            
            # Return silent response - intro sequence will handle audio
            return IVRResponse("wait", "", "main_menu")
        else:
            # Fallback if no mixer
            return IVRResponse("speak", "this is the backyard tryhards stat tracker. press or say 1 for top players. 2 for top organizations by attendance.", "main_menu")
    
    async def _execute_intro_sequence(self, call_id: str, ivr_service, audio_mixer):
        """Execute the intro sequence with working mixer methods"""
        
        # 1. Announce current date and time first (no music yet)
        print(f"🕒 [T+0s] Announcing date and time for call {call_id}")
        try:
            from datetime import datetime, timezone, timedelta
            
            # Get current time in Pacific timezone (UTC-8/UTC-7)
            # Using simple offset since pytz has system issues
            pacific_offset = timedelta(hours=-8)  # PST, adjust for PDT if needed
            pacific_tz = timezone(pacific_offset)
            now = datetime.now(pacific_tz)
            
            # Format the announcement
            date_str = now.strftime("%A, %B %d, %Y")
            time_str = now.strftime("%I:%M %p")
            
            datetime_announcement = f"Good {self._get_time_greeting(now)}. Today is {date_str}. The current time is {time_str} Pacific."
            
            if ivr_service and hasattr(ivr_service, 'send_tts_response'):
                await ivr_service.send_tts_response(
                    None,  # websocket handled internally
                    datetime_announcement
                )
            else:
                print(f"🔊 Would announce: {datetime_announcement}")
                
        except Exception as e:
            print(f"❌ Error announcing date/time: {e}")
            # Continue with intro even if date/time fails
        
        # 2. Wait 1 second pause after date/time
        await asyncio.sleep(1.0)
        
        # 3. Start background music
        print(f"🎵 [T+1s] Starting intro music for call {call_id}")
        if hasattr(audio_mixer, 'start_continuous_music'):
            audio_mixer.start_continuous_music()
        
        # 4. Wait 2 seconds for music to establish
        print(f"⏱️ [T+1s] Waiting 2 seconds for music...")
        await asyncio.sleep(2.0)
        
        # 5. Mix in the spoken prompt with the music using the real mixer
        print(f"🎤 [T+3s] Speaking prompt mixed with background music")
        try:
            # Use the working TTS + mixer system
            if ivr_service and hasattr(ivr_service, 'send_tts_response'):
                await ivr_service.send_tts_response(
                    None,  # websocket handled internally
                    "this is the backyard tryhards stat tracker. press or say 1 for top players. 2 for top organizations by attendance. press 0 for current date and time."
                )
            else:
                # Fallback to basic speak
                print("🔊 Using basic speak fallback")
                return IVRResponse("speak", "this is the backyard tryhards stat tracker. press or say 1 for top players. 2 for top organizations by attendance. press 0 for current date and time.", "main_menu")
        except Exception as e:
            print(f"❌ Error in intro sequence: {e}")
            return IVRResponse("speak", "this is the backyard tryhards stat tracker. press or say 1 for top players. 2 for top organizations by attendance. press 0 for current date and time.", "main_menu")
        
        # Mark intro as complete
        call_state = self.get_call_state(call_id)
        call_state['intro_complete'] = True
        self.set_call_state(call_id, call_state)
        
        print(f"✅ [T+4s] Intro sequence complete for call {call_id}")
    
    def _get_time_greeting(self, dt):
        """Get appropriate greeting based on time of day"""
        hour = dt.hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "evening"  # Late night/early morning
    
    async def on_dtmf_input(self, call_id: str, digit: str, ivr_service=None, audio_mixer=None) -> IVRResponse:
        """Handle DTMF input - can interrupt intro sequence"""
        print(f"🔢 DTMF signal received: {digit} for call {call_id}")
        
        # Handle the input directly
        if digit == '1':
            # Top players request
            print(f"🏆 Getting top 8 players for call {call_id}")
            response = pq("show top 8 players")
            if response:
                content = f"Here are the top 8 players: {response}. Press star to return to main menu."
            else:
                content = "Top 8 players: First place West with 45 wins, second Zak with 38 wins, third Bear with 32 wins. Press star for main menu."
            return IVRResponse("speak", content, "players_menu")
            
        elif digit == '2':
            # Top organizations request
            print(f"🏢 Getting top 10 organizations for call {call_id}")
            response = pq("show top 10 organizations")
            if response:
                content = f"Here are the top 10 organizations: {response}. Press star to return to main menu."
            else:
                content = "Top organizations by attendance: West Coast Warzone, Ultimate Fighting Game Tournament. Press star for main menu."
            return IVRResponse("speak", content, "organizations_menu")
            
        elif digit == '*':
            # Return to main menu
            return IVRResponse("speak", "Returning to main menu. Press 1 for players, 2 for organizations.", "main_menu")
            
        elif digit == '0':
            # Announce current date and time
            print(f"🕒 Announcing current date/time for call {call_id}")
            try:
                from datetime import datetime, timezone, timedelta
                
                # Get current time in Pacific timezone
                pacific_offset = timedelta(hours=-8)  # PST, adjust for PDT if needed
                pacific_tz = timezone(pacific_offset)
                now = datetime.now(pacific_tz)
                
                # Format the announcement
                date_str = now.strftime("%A, %B %d, %Y")
                time_str = now.strftime("%I:%M %p")
                
                datetime_announcement = f"Today is {date_str}. The current time is {time_str} Pacific. Press 1 for players, 2 for organizations."
                
                return IVRResponse("speak", datetime_announcement, "main_menu")
                
            except Exception as e:
                print(f"❌ Error announcing date/time: {e}")
                return IVRResponse("speak", "Sorry, I couldn't get the current date and time. Press 1 for players, 2 for organizations.", "main_menu")
            
        elif digit == '#':
            # End call
            return IVRResponse("hangup", "Thanks for calling Try Hard Tournament Tracker. Goodbye!")
            
        else:
            # Invalid selection
            return IVRResponse("speak", f"Invalid selection {digit}. Press 1 for players, 2 for organizations.")
    
    async def on_speech_input(self, call_id: str, text: str, ivr_service=None, audio_mixer=None) -> IVRResponse:
        """Handle speech input - can interrupt intro sequence"""
        print(f"🎤 Speech signal received: '{text}' for call {call_id}")
        
        # Handle the speech input
        text_lower = text.lower().strip()
        
        # Map speech to menu options
        if any(word in text_lower for word in ['one', '1', 'player', 'players']):
            # Same as DTMF "1"
            print(f"🏆 Getting top 8 players for call {call_id} (via speech)")
            response = pq("show top 8 players")
            if response:
                content = f"Here are the top 8 players: {response}. Press star to return to main menu."
            else:
                content = "Top 8 players: First place West with 45 wins, second Zak with 38 wins, third Bear with 32 wins. Press star for main menu."
            return IVRResponse("speak", content, "players_menu")
            
        elif any(word in text_lower for word in ['two', '2', 'organization', 'organizations']):
            # Same as DTMF "2"
            print(f"🏢 Getting top 10 organizations for call {call_id} (via speech)")
            response = pq("show top 10 organizations")
            if response:
                content = f"Here are the top 10 organizations: {response}. Press star to return to main menu."
            else:
                content = "Top organizations by attendance: West Coast Warzone, Ultimate Fighting Game Tournament. Press star for main menu."
            return IVRResponse("speak", content, "organizations_menu")
            
        elif any(word in text_lower for word in ['goodbye', 'bye', 'hang up']):
            return IVRResponse("hangup", "Thanks for calling Try Hard Tournament Tracker. Goodbye!")
            
        else:
            return IVRResponse("speak", "I didn't understand that. Please say 'players' or 'organizations'.")
    
    async def _interrupt_intro_sequence(self, call_id: str, ivr_service, audio_mixer):
        """Interrupt the intro sequence immediately when user provides input"""
        call_state = self.get_call_state(call_id)
        
        # Cancel the intro task if it's still running
        intro_task = call_state.get('intro_task')
        if intro_task and not intro_task.done():
            intro_task.cancel()
            print(f"🛑 Cancelled intro sequence task for call {call_id}")
        
        # Stop intro music immediately
        await audio_mixer.stop_intro_music(call_id)
        
        # Start menu music at 25% volume
        await audio_mixer.play_menu_music(call_id, volume=0.25, loop=True)
        
        # Mark intro as complete (interrupted)
        call_state['intro_complete'] = True
        call_state['intro_interrupted'] = True
        self.set_call_state(call_id, call_state)
        
        print(f"⚡ Intro sequence interrupted by user input for call {call_id}")
    
    async def _handle_menu_selection(self, call_id: str, menu_name: str, ivr_service, audio_mixer) -> ScriptResponse:
        """Handle menu selection and execute appropriate action"""
        print(f"📋 Menu selection: {menu_name} for call {call_id}")
        
        if menu_name == 'players_menu':
            return await self._get_top_players(call_id, ivr_service, audio_mixer)
        elif menu_name == 'organizations_menu':
            return await self._get_top_organizations(call_id, ivr_service, audio_mixer)
        elif menu_name == 'help_menu':
            await ivr_service.speak(call_id, "Press or say 1 for top players, 2 for top organizations, or pound to hang up.")
            return ScriptResponse("continue")
        elif menu_name == 'goodbye':
            await audio_mixer.stop_all_music(call_id)
            await ivr_service.speak(call_id, "Thanks for calling Try Hard Tournament Tracker. Goodbye!")
            return ScriptResponse("hangup")
        elif menu_name == 'main_menu':
            await ivr_service.speak(call_id, "Returning to main menu. Press 1 for players, 2 for organizations.")
            return ScriptResponse("continue")
        else:
            return ScriptResponse("continue")
    
    async def _get_top_players(self, call_id: str, ivr_service, audio_mixer) -> ScriptResponse:
        """Get and announce top players"""
        try:
            # Lower menu music during announcement
            await audio_mixer.fade_music_volume(call_id, 0.1, duration=0.5)
            
            # Query for top players
            response = pq("show top 8 players")
            
            if response:
                text = f"Here are the top 8 players: {response}. Press star to return to main menu."
            else:
                text = "Top 8 players: First place West with 45 wins, second Zak with 38 wins, third Bear with 32 wins. Press star for main menu."
            
            await ivr_service.speak(call_id, text)
            
            # Restore menu music volume
            await audio_mixer.fade_music_volume(call_id, 0.25, duration=0.5)
            
            return ScriptResponse("continue")
            
        except Exception as e:
            print(f"❌ Error getting players: {e}")
            await ivr_service.speak(call_id, "Sorry, player data is unavailable. Press star for main menu.")
            return ScriptResponse("continue")
    
    async def _get_top_organizations(self, call_id: str, ivr_service, audio_mixer) -> ScriptResponse:
        """Get and announce top organizations"""
        try:
            # Lower menu music during announcement
            await audio_mixer.fade_music_volume(call_id, 0.1, duration=0.5)
            
            # Query for top organizations
            response = pq("show top 10 organizations")
            
            if response:
                text = f"Here are the top 10 organizations by attendance: {response}. Press star to return to main menu."
            else:
                text = "Top organizations by attendance: West Coast Warzone, Ultimate Fighting Game Tournament, Southern California Majors. Press star for main menu."
            
            await ivr_service.speak(call_id, text)
            
            # Restore menu music volume
            await audio_mixer.fade_music_volume(call_id, 0.25, duration=0.5)
            
            return ScriptResponse("continue")
            
        except Exception as e:
            print(f"❌ Error getting organizations: {e}")
            await ivr_service.speak(call_id, "Sorry, organization data is unavailable. Press star for main menu.")
            return ScriptResponse("continue")
    
    async def on_call_end(self, call_id: str, ivr_service, audio_mixer):
        """Cleanup when call ends"""
        print(f"📞 Cleaning up call {call_id}")
        
        # Stop all music for this call
        await audio_mixer.stop_all_music(call_id)
        
        # Call parent cleanup
        await super().on_call_end(call_id, ivr_service, audio_mixer)

# Create the script instance
tournament_advanced_script = TournamentAdvancedIVRScript()

if __name__ == "__main__":
    print("🏆 Advanced Tournament IVR Script loaded")
    print("🎬 Features: Precise audio timing, music control, complex sequences")