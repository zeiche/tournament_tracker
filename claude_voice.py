#!/usr/bin/env python3
"""
claude_voice.py - Give Claude a robot voice and send audio via Discord

Since the server has no audio output, we:
1. Generate robot voice audio files
2. Send them via Discord DM
3. Ultra-lightweight using espeak
"""

import os
import subprocess
import tempfile
from typing import Optional, Dict
import asyncio
import discord

class ClaudeVoice:
    """Robot voice for Claude that sends audio via Discord"""
    
    # Robot voice presets
    VOICES = {
        "normal": {
            "voice": "en+m3",      # Male robot voice
            "speed": 150,
            "pitch": 50,
            "amplitude": 100
        },
        "excited": {
            "voice": "en+m3",
            "speed": 180,
            "pitch": 70,
            "amplitude": 120
        },
        "serious": {
            "voice": "en+m1",      # Deeper voice
            "speed": 120,
            "pitch": 30,
            "amplitude": 90
        },
        "whisper": {
            "voice": "en+whisper",
            "speed": 100,
            "pitch": 50,
            "amplitude": 50
        },
        "glados": {               # Portal-style
            "voice": "en+f3",      # Female robot
            "speed": 140,
            "pitch": 60,
            "amplitude": 100
        }
    }
    
    def __init__(self, voice_preset: str = "normal"):
        """Initialize with a voice preset"""
        self.voice_config = self.VOICES.get(voice_preset, self.VOICES["normal"])
        self.preset = voice_preset
        
    def generate_audio(self, text: str, output_file: Optional[str] = None) -> str:
        """
        Generate robot voice audio file
        
        Args:
            text: Text to speak
            output_file: Output filename (auto-generated if None)
            
        Returns:
            Path to generated audio file
        """
        if not output_file:
            # Generate temp filename
            output_file = tempfile.mktemp(suffix='.wav', prefix='claude_voice_')
        
        # Build espeak command
        cmd = [
            'espeak',
            '-v', self.voice_config['voice'],
            '-s', str(self.voice_config['speed']),
            '-p', str(self.voice_config['pitch']),
            '-a', str(self.voice_config['amplitude']),
            '-w', output_file,
            text
        ]
        
        # Generate audio
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"🎙️ Generated audio: {output_file} ({os.path.getsize(output_file)} bytes)")
            return output_file
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to generate audio: {e}")
            return None
    
    async def send_to_discord(self, text: str, user: str = "zeiche", delete_after: bool = True) -> bool:
        """
        Generate audio and send via Discord DM
        
        Args:
            text: Text to speak
            user: Discord username to DM
            delete_after: Delete audio file after sending
            
        Returns:
            Success boolean
        """
        # Generate audio
        audio_file = self.generate_audio(text)
        if not audio_file:
            return False
        
        # Get Discord token
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
            print("❌ No Discord token found")
            return False
        
        # Send via Discord
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        client = discord.Client(intents=intents)
        success = False
        
        @client.event
        async def on_ready():
            nonlocal success
            
            # Find user
            target_user = None
            for guild in client.guilds:
                await guild.chunk()
                for member in guild.members:
                    if user.lower() in member.name.lower():
                        target_user = member
                        break
                if target_user:
                    break
            
            if target_user:
                try:
                    channel = await target_user.create_dm()
                    
                    # Create embed
                    embed = discord.Embed(
                        title="🤖 Claude Voice Message",
                        description=f"```{text}```",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="Voice Preset",
                        value=self.preset.upper(),
                        inline=True
                    )
                    embed.add_field(
                        name="Duration",
                        value=f"~{len(text.split())*0.5:.1f}s",
                        inline=True
                    )
                    
                    # Send audio with embed
                    with open(audio_file, 'rb') as f:
                        file = discord.File(f, filename="claude_voice.wav")
                        await channel.send(embed=embed, file=file)
                    
                    success = True
                    print(f"✅ Voice message sent to {target_user.name}")
                    
                except Exception as e:
                    print(f"❌ Failed to send DM: {e}")
            else:
                print(f"❌ User '{user}' not found")
            
            await client.close()
        
        await client.start(token)
        
        # Cleanup
        if delete_after and os.path.exists(audio_file):
            os.unlink(audio_file)
        
        return success
    
    def say(self, text: str, send_discord: bool = True, user: str = "zeiche") -> bool:
        """
        Simple method to speak text
        
        Args:
            text: Text to speak
            send_discord: Send via Discord (since server has no audio)
            user: Discord user to send to
            
        Returns:
            Success boolean
        """
        if send_discord:
            # Run async function
            return asyncio.run(self.send_to_discord(text, user))
        else:
            # Just generate file
            audio_file = self.generate_audio(text)
            if audio_file:
                print(f"✅ Audio saved to: {audio_file}")
                return True
            return False


def demo():
    """Demo different robot voices"""
    print("=" * 60)
    print("🤖 CLAUDE ROBOT VOICE DEMO")
    print("=" * 60)
    
    demos = [
        ("normal", "Hello zeiche. I am Claude, your tournament assistant."),
        ("excited", "Wow! You got first place in the tournament!"),
        ("serious", "Warning: Database synchronization in progress."),
        ("whisper", "Psst... I found a secret tech in your frame data."),
        ("glados", "The cake is a lie. But your tournament ranking is real."),
    ]
    
    for preset, text in demos:
        print(f"\n{preset.upper()}: {text}")
        voice = ClaudeVoice(preset)
        audio_file = voice.generate_audio(text, f"demo_{preset}.wav")
        if audio_file:
            size = os.path.getsize(audio_file) / 1024
            print(f"  → Generated {audio_file} ({size:.1f} KB)")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Claude Robot Voice')
    parser.add_argument('text', nargs='?', help='Text to speak')
    parser.add_argument('--voice', choices=list(ClaudeVoice.VOICES.keys()),
                       default='normal', help='Voice preset')
    parser.add_argument('--demo', action='store_true', help='Run demo')
    parser.add_argument('--no-discord', action='store_true', 
                       help='Just save audio file, don\'t send to Discord')
    parser.add_argument('--user', default='zeiche', help='Discord user to DM')
    
    args = parser.parse_args()
    
    if args.demo:
        demo()
    elif args.text:
        voice = ClaudeVoice(args.voice)
        success = voice.say(
            args.text,
            send_discord=not args.no_discord,
            user=args.user
        )
        if not success:
            print("❌ Failed to generate/send voice")
    else:
        print("Usage: claude_voice.py 'text to speak' [--voice preset]")
        print(f"Available voices: {', '.join(ClaudeVoice.VOICES.keys())}")


if __name__ == "__main__":
    main()