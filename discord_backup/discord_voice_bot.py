#!/usr/bin/env python3
"""
discord_voice_bot.py - Join voice channels and speak!

Claude can now join Discord voice channels and talk using robot voice.
"""

# ENFORCE THE RULE: Everything goes through go.py!
import go_py_guard

import discord
from discord.ext import commands
import asyncio
import subprocess
import os
import tempfile
from discord_audio_sink import get_audio_sink
from capability_announcer import announcer
from capability_discovery import register_capability

# Import the PURE BONJOUR services to activate them
import pure_bonjour_voice_bridge
import polymorphic_tts_service  
import polymorphic_audio_player

# Simple TTS class using espeak
class SimpleTTS:
    def generate_voice(self, text, voice_type, output_file):
        # Default settings: medium-fast speed (175), normal pitch (50), slight gaps for clarity
        # This allows for clear communication while being engaging
        base_args = ['espeak', '-w', output_file, '-s', '175', '-p', '50', '-g', '2']
        
        if voice_type == "robot":
            # Slightly slower for robotic effect, lower pitch
            subprocess.run(['espeak', '-w', output_file, '-s', '160', '-p', '35', '-g', '5', text], check=False)
        elif voice_type == "excited":
            # Faster and slightly higher pitch for excitement
            subprocess.run(['espeak', '-w', output_file, '-s', '190', '-p', '60', '-g', '1', text], check=False)
        elif voice_type == "serious":
            # Slower and lower pitch for serious topics
            subprocess.run(['espeak', '-w', output_file, '-s', '150', '-p', '40', '-g', '3', text], check=False)
        else:  # normal - optimized for clear, engaging communication
            subprocess.run(base_args + [text], check=False)

class VoiceBot(commands.Cog):
    """Voice channel capabilities for Claude"""
    
    def __init__(self, bot):
        self.bot = bot
        self.robot = SimpleTTS()
        self.voice_client = None
        self.audio_sink = None
        self.is_recording = False
        
        # Register with the PURE BONJOUR audio player
        if hasattr(polymorphic_audio_player, 'audio_player'):
            polymorphic_audio_player.audio_player.register_discord_bot(self)
        
        # Register as discoverable capability
        register_capability('discord_voice_bot', lambda: self)
        
    async def join_voice(self, ctx):
        """Join the voice channel of the user who called the command"""
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if self.voice_client and self.voice_client.is_connected():
                await self.voice_client.move_to(channel)
            else:
                self.voice_client = await channel.connect()
            
            # Start recording audio when joining
            await self.start_recording(ctx.guild.id)
            
            return True
        else:
            await ctx.send("❌ You need to be in a voice channel for me to join!")
            return False
    
    async def start_recording(self, guild_id: int):
        """Start recording audio from voice channel"""
        print(f"🔴 [DEBUG] start_recording called for guild {guild_id}")
        
        if not self.voice_client or not self.voice_client.is_connected():
            print("🔴 [DEBUG] No voice client or not connected")
            return False
        
        if self.is_recording:
            print("🔴 [DEBUG] Already recording")
            return True  # Already recording
        
        try:
            # Get audio sink for this guild
            self.audio_sink = get_audio_sink(guild_id)
            print(f"🔴 [DEBUG] Got audio sink: {self.audio_sink}")
            
            # Start recording with the sink
            self.voice_client.start_recording(
                self.audio_sink,
                self.on_recording_finished,
                check_for_speech=False  # Record all audio
            )
            
            self.is_recording = True
            
            # Announce recording started
            announcer.announce(
                "VOICE_RECORDING",
                [
                    f"Started recording in guild {guild_id}",
                    "Audio sink attached",
                    "Listening for voice data"
                ]
            )
            
            print(f"🔴 Started recording audio in guild {guild_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error starting recording: {e}")
            announcer.announce(
                "VOICE_RECORDING_ERROR",
                [f"Failed to start recording: {e}"]
            )
            return False
    
    async def stop_recording(self):
        """Stop recording audio"""
        if not self.is_recording or not self.voice_client:
            return False
        
        try:
            # Stop recording
            self.voice_client.stop_recording()
            self.is_recording = False
            
            # Announce recording stopped
            announcer.announce(
                "VOICE_RECORDING",
                ["Stopped recording", "Processing audio data"]
            )
            
            print("⏹️ Stopped recording audio")
            return True
            
        except Exception as e:
            print(f"❌ Error stopping recording: {e}")
            return False
    
    async def on_recording_finished(self, sink, *args):
        """Called when recording is finished"""
        announcer.announce(
            "RECORDING_FINISHED",
            [
                "Recording session complete",
                f"Captured audio from {len(sink.audio_data)} users" if hasattr(sink, 'audio_data') else "Audio captured"
            ]
        )
        print("✅ Recording finished, audio data processed")
    
    async def say_in_voice(self, text: str, voice_type: str = "normal"):
        """Generate and play text in voice channel"""
        if not self.voice_client or not self.voice_client.is_connected():
            return False
        
        # Generate audio file
        temp_wav = tempfile.mktemp(suffix='.wav')
        self.robot.generate_voice(text, voice_type, temp_wav)
        
        # Convert WAV to a format Discord can stream (using espeak's built-in output)
        # Since ffmpeg has issues, we'll use the WAV directly
        
        # Play the audio
        try:
            audio_source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(temp_wav),
                volume=1.0
            )
            
            self.voice_client.play(
                audio_source,
                after=lambda e: print(f'Player error: {e}') if e else None
            )
            
            # Wait for audio to finish
            while self.voice_client.is_playing():
                await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Error playing audio: {e}")
            return False
        finally:
            # Cleanup
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
        
        return True
    
    @commands.command(name='join')
    async def join(self, ctx):
        """Join the voice channel"""
        if await self.join_voice(ctx):
            await ctx.send("🎤 Yo! Claude's in the voice channel now, dude!")
            await self.say_in_voice("What's up everyone! Claude here, ready to talk about tournaments!")
    
    @commands.command(name='leave')
    async def leave(self, ctx):
        """Leave the voice channel"""
        if self.voice_client:
            # Stop recording before leaving
            await self.stop_recording()
            
            await self.say_in_voice("Alright, I'm heading out. Catch you later, dude!")
            await self.voice_client.disconnect()
            self.voice_client = None
            await ctx.send("👋 Later! Claude out.")
        else:
            await ctx.send("I'm not in a voice channel right now")
    
    @commands.command(name='say')
    async def say(self, ctx, *, text: str):
        """Say something in voice channel"""
        if not self.voice_client or not self.voice_client.is_connected():
            if not await self.join_voice(ctx):
                return
        
        await ctx.send(f"🎙️ Saying: {text}")
        await self.say_in_voice(text)
    
    @commands.command(name='robot')
    async def robot_demo(self, ctx):
        """Demo robot voices"""
        if not self.voice_client or not self.voice_client.is_connected():
            if not await self.join_voice(ctx):
                return
        
        demos = [
            ("Hey everyone! I'm Claude, and I'm ready to chat about tournaments.", "normal"),
            ("This is my robot voice - a bit slower and lower pitched.", "robot"),
            ("Oh wow, this is so exciting! I love talking about fighting game tournaments!", "excited"),
            ("Now let me speak in a more serious tone about tournament data analysis.", "serious"),
        ]
        
        await ctx.send("🎤 Starting voice demo...")
        
        for text, voice in demos:
            await self.say_in_voice(text, voice)
            await asyncio.sleep(1)
        
        await ctx.send("✅ Demo complete!")
    
    @commands.command(name='record')
    async def record(self, ctx, action: str = "status"):
        """Control voice recording (start/stop/status)"""
        if action.lower() == "start":
            if not self.voice_client or not self.voice_client.is_connected():
                await ctx.send("❌ I need to be in a voice channel first! Use !join")
                return
            
            if self.is_recording:
                await ctx.send("🔴 Already recording!")
            else:
                if await self.start_recording(ctx.guild.id):
                    await ctx.send("🔴 Started recording voice channel audio!")
                else:
                    await ctx.send("❌ Failed to start recording")
        
        elif action.lower() == "stop":
            if not self.is_recording:
                await ctx.send("⚪ Not currently recording")
            else:
                if await self.stop_recording():
                    await ctx.send("⏹️ Stopped recording. Audio is being processed...")
                else:
                    await ctx.send("❌ Failed to stop recording")
        
        elif action.lower() == "status":
            if self.is_recording:
                await ctx.send("🔴 Currently RECORDING voice channel audio")
            else:
                await ctx.send("⚪ Not recording")
        
        else:
            await ctx.send("Usage: !record [start|stop|status]")


class ClaudeVoiceBot(commands.Bot):
    """Main bot class"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            description='Claude Voice Bot - Talk to Claude in voice channels!'
        )
    
    async def on_ready(self):
        print(f'✅ {self.user} is online!')
        print(f'📡 Connected to {len(self.guilds)} guilds')
        print('\nVoice Commands:')
        print('  !join - Join your voice channel (auto-starts recording)')
        print('  !leave - Leave voice channel (stops recording)')
        print('  !say <text> - Say something in voice')
        print('  !robot - Demo different robot voices')
        print('  !record [start|stop|status] - Control voice recording')
        print('  !help - Show all commands')
        print('\n🔴 Recording: Audio is automatically recorded when bot joins voice!')
        print('   Recordings are processed through the polymorphic pipeline')
        
        # Auto-join #general voice channel
        await self.auto_join_general_voice()
    
    async def auto_join_general_voice(self):
        """Automatically join #general voice channel on startup"""
        try:
            # Find #general voice channel across all guilds
            general_voice = None
            target_guild = None
            
            for guild in self.guilds:
                for channel in guild.voice_channels:
                    if channel.name.lower() in ['general', 'general-voice', 'voice']:
                        general_voice = channel
                        target_guild = guild
                        break
                if general_voice:
                    break
            
            if general_voice:
                print(f"🔍 Found voice channel: #{general_voice.name} in {target_guild.name}")
                
                # Get the VoiceBot cog and join
                voice_cog = self.get_cog('VoiceBot')
                if voice_cog:
                    # Connect to voice channel
                    voice_cog.voice_client = await general_voice.connect()
                    print(f"🎤 Auto-joined #{general_voice.name}")
                    
                    # Start recording automatically
                    await voice_cog.start_recording(target_guild.id)
                    print("🔴 Started recording automatically")
                    
                    # Announce via Bonjour
                    announcer.announce(
                        "DISCORD_AUTO_JOIN",
                        [
                            f"Bot auto-joined #{general_voice.name}",
                            f"Guild: {target_guild.name}",
                            "Recording started automatically"
                        ]
                    )
                else:
                    print("❌ VoiceBot cog not found")
            else:
                print("⚠️ No #general voice channel found")
                print("Available voice channels:")
                for guild in self.guilds:
                    for channel in guild.voice_channels:
                        print(f"  - {guild.name}: #{channel.name}")
        
        except Exception as e:
            print(f"❌ Auto-join failed: {e}")
            announcer.announce(
                "DISCORD_AUTO_JOIN_ERROR",
                [f"Auto-join failed: {e}"]
            )
    
    async def setup_hook(self):
        """Setup the bot"""
        await self.add_cog(VoiceBot(self))


async def main():
    """Run the voice bot"""
    # Get token
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        env_file = '/home/ubuntu/claude/tournament_tracker/.env'
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('DISCORD_BOT_TOKEN='):
                        token = line.split('=', 1)[1].strip().strip('"').strip("'")
                        break
    
    if not token:
        print("❌ No Discord token found!")
        return
    
    bot = ClaudeVoiceBot()
    
    try:
        await bot.start(token)
    except discord.LoginFailure:
        print("❌ Invalid token!")
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        await bot.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🎤 CLAUDE VOICE BOT - Discord Voice Channel Support")
    print("=" * 60)
    print("\nStarting voice bot...")
    print("I'll join voice channels and speak with my robot voice!\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Voice bot stopped")