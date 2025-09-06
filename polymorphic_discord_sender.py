#!/usr/bin/env python3
"""
polymorphic_discord_sender.py - Send ANYTHING to Discord

TRUE POLYMORPHISM: Give it ANY Python object and it figures out how to send it!
- Strings → Text messages
- Images → Image attachments  
- Audio → Voice messages
- Dictionaries → Formatted embeds
- Lists → Tables or multi-messages
- Objects → Serialized representations
- Files → Attachments
- DataFrames → Tables
- Matplotlib figures → Charts
- ANYTHING → It figures it out!

This is the ULTIMATE Discord sender - it accepts ANYTHING!
"""

import os
import io
import json
import pickle
import asyncio
import discord
import tempfile
import subprocess
from typing import Any, Optional, Union, List
from pathlib import Path
from datetime import datetime
import inspect

class PolymorphicDiscordSender:
    """
    The ULTIMATE polymorphic Discord sender.
    Give it ANYTHING - it figures out how to send it!
    """
    
    def __init__(self):
        self.token = self._get_token()
        
    def _get_token(self) -> str:
        """Get Discord token from environment or .env file"""
        token = os.getenv('DISCORD_BOT_TOKEN')
        if not token:
            env_file = '/home/ubuntu/claude/tournament_tracker/.env'
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('DISCORD_BOT_TOKEN='):
                            token = line.split('=', 1)[1].strip().strip('"').strip("'")
                            break
        return token
    
    def send(self, target: str, *objects: Any, **kwargs) -> bool:
        """
        Send ANYTHING to Discord!
        
        Args:
            target: Username or channel to send to
            *objects: ANY Python objects to send
            **kwargs: Optional parameters (title, description, etc.)
            
        Returns:
            Success boolean
        """
        return asyncio.run(self._async_send(target, *objects, **kwargs))
    
    async def _async_send(self, target: str, *objects: Any, **kwargs) -> bool:
        """Async implementation of polymorphic sending"""
        if not self.token:
            print("❌ No Discord token found")
            return False
        
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        client = discord.Client(intents=intents)
        success = False
        
        @client.event
        async def on_ready():
            nonlocal success
            
            # Find target (user or channel)
            channel = await self._find_target(client, target)
            if not channel:
                print(f"❌ Target '{target}' not found")
                await client.close()
                return
            
            # Process and send each object
            for obj in objects:
                try:
                    await self._send_object(channel, obj, **kwargs)
                    success = True
                except Exception as e:
                    print(f"❌ Failed to send {type(obj).__name__}: {e}")
            
            await client.close()
        
        try:
            await client.start(self.token)
        except discord.LoginFailure:
            print("❌ Invalid Discord token")
        except Exception as e:
            print(f"❌ Discord error: {e}")
        
        return success
    
    async def _find_target(self, client: discord.Client, target: str):
        """Find user or channel by name"""
        # Try to find user first
        for guild in client.guilds:
            await guild.chunk()
            for member in guild.members:
                if target.lower() in member.name.lower():
                    return await member.create_dm()
        
        # Try to find channel
        for guild in client.guilds:
            for channel in guild.text_channels:
                if target.lower() in channel.name.lower():
                    return channel
        
        return None
    
    async def _send_object(self, channel, obj: Any, **kwargs):
        """
        Figure out what the object is and send it appropriately
        
        THE MAGIC HAPPENS HERE - It handles ANYTHING!
        """
        obj_type = type(obj).__name__
        
        # STRING → Text message
        if isinstance(obj, str):
            if len(obj) > 2000:
                # Too long - send as file
                with io.StringIO(obj) as f:
                    await channel.send(
                        "📄 Text content (too long for message):",
                        file=discord.File(f, "content.txt")
                    )
            else:
                await channel.send(obj)
        
        # BYTES → Figure out what it is
        elif isinstance(obj, bytes):
            await self._send_bytes(channel, obj, **kwargs)
        
        # PATH/FILE → Send as attachment
        elif isinstance(obj, (Path, str)) and os.path.exists(str(obj)):
            await self._send_file(channel, str(obj), **kwargs)
        
        # DICT → Format as embed
        elif isinstance(obj, dict):
            embed = self._dict_to_embed(obj, **kwargs)
            await channel.send(embed=embed)
        
        # LIST/TUPLE → Send each item or format as table
        elif isinstance(obj, (list, tuple)):
            if len(obj) <= 5:
                # Send each item
                for item in obj:
                    await self._send_object(channel, item, **kwargs)
            else:
                # Format as table
                table = self._format_table(obj)
                await channel.send(f"```\n{table}\n```")
        
        # PIL IMAGE → Send as image
        elif obj.__class__.__name__ == 'Image':
            buffer = io.BytesIO()
            obj.save(buffer, format='PNG')
            buffer.seek(0)
            await channel.send(
                file=discord.File(buffer, "image.png")
            )
        
        # MATPLOTLIB FIGURE → Send as chart
        elif obj.__class__.__name__ == 'Figure':
            buffer = io.BytesIO()
            obj.savefig(buffer, format='png')
            buffer.seek(0)
            await channel.send(
                "📊 Chart:",
                file=discord.File(buffer, "chart.png")
            )
        
        # PANDAS DATAFRAME → Send as table
        elif obj.__class__.__name__ == 'DataFrame':
            table = obj.to_string()
            if len(table) > 1900:
                # Too long - send as CSV
                buffer = io.StringIO()
                obj.to_csv(buffer)
                buffer.seek(0)
                await channel.send(
                    "📊 DataFrame (CSV):",
                    file=discord.File(buffer, "data.csv")
                )
            else:
                await channel.send(f"```\n{table}\n```")
        
        # NUMPY ARRAY → Send as data
        elif obj.__class__.__module__ == 'numpy':
            data_str = str(obj)
            if len(data_str) > 1900:
                buffer = io.StringIO(data_str)
                await channel.send(
                    "🔢 NumPy Array:",
                    file=discord.File(buffer, "array.txt")
                )
            else:
                await channel.send(f"```python\n{data_str}\n```")
        
        # EXCEPTION → Format error nicely
        elif isinstance(obj, Exception):
            embed = discord.Embed(
                title="❌ Error",
                description=str(obj),
                color=discord.Color.red()
            )
            embed.add_field(
                name="Type",
                value=obj.__class__.__name__,
                inline=True
            )
            await channel.send(embed=embed)
        
        # FUNCTION/METHOD → Send source code
        elif callable(obj):
            try:
                source = inspect.getsource(obj)
                if len(source) > 1900:
                    buffer = io.StringIO(source)
                    await channel.send(
                        f"📝 Source code for {obj.__name__}:",
                        file=discord.File(buffer, f"{obj.__name__}.py")
                    )
                else:
                    await channel.send(f"```python\n{source}\n```")
            except:
                await channel.send(f"📦 {obj.__name__} (built-in function)")
        
        # AUDIO DATA → Convert and send
        elif self._is_audio_data(obj):
            audio_file = await self._process_audio(obj)
            if audio_file:
                await channel.send(
                    "🎵 Audio:",
                    file=discord.File(audio_file, "audio.wav")
                )
                os.unlink(audio_file)
        
        # TOURNAMENT/PLAYER/MODEL → Format intelligently
        elif hasattr(obj, '__tablename__'):  # SQLAlchemy model
            embed = self._model_to_embed(obj)
            await channel.send(embed=embed)
        
        # CLASS INSTANCE → Serialize and send
        elif hasattr(obj, '__dict__'):
            data = {
                '_type': obj.__class__.__name__,
                '_module': obj.__class__.__module__,
                **obj.__dict__
            }
            embed = self._dict_to_embed(data, title=obj.__class__.__name__)
            await channel.send(embed=embed)
        
        # GENERATOR/ITERATOR → Process items
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
            items = list(obj)[:10]  # Limit to 10 items
            await self._send_object(channel, items, **kwargs)
        
        # ANYTHING ELSE → Pickle and send
        else:
            try:
                # Try to pickle it
                pickled = pickle.dumps(obj)
                buffer = io.BytesIO(pickled)
                await channel.send(
                    f"🔧 Pickled {obj_type} object:",
                    file=discord.File(buffer, f"{obj_type}.pickle")
                )
            except:
                # Last resort - send string representation
                text = str(obj)
                if len(text) > 1900:
                    buffer = io.StringIO(text)
                    await channel.send(
                        f"📄 {obj_type} (text representation):",
                        file=discord.File(buffer, f"{obj_type}.txt")
                    )
                else:
                    await channel.send(f"```\n{obj_type}: {text}\n```")
    
    def _dict_to_embed(self, data: dict, **kwargs) -> discord.Embed:
        """Convert dictionary to Discord embed"""
        title = kwargs.get('title', 'Data')
        description = kwargs.get('description', '')
        color = kwargs.get('color', discord.Color.blue())
        
        embed = discord.Embed(
            title=title,
            description=description or str(data.get('_description', '')),
            color=color
        )
        
        for key, value in data.items():
            if not key.startswith('_'):
                # Format value nicely
                if isinstance(value, (list, tuple)):
                    value = ', '.join(str(v) for v in value[:5])
                    if len(data[key]) > 5:
                        value += f"... ({len(data[key])} items)"
                elif isinstance(value, dict):
                    value = f"{len(value)} items"
                else:
                    value = str(value)[:1024]  # Discord limit
                
                embed.add_field(
                    name=key.replace('_', ' ').title(),
                    value=value or 'None',
                    inline=True
                )
        
        return embed
    
    def _model_to_embed(self, model) -> discord.Embed:
        """Convert SQLAlchemy model to embed"""
        embed = discord.Embed(
            title=f"{model.__class__.__name__}: {getattr(model, 'name', 'Unknown')}",
            color=discord.Color.green()
        )
        
        # Add fields for each column
        for column in model.__table__.columns:
            value = getattr(model, column.name, None)
            if value is not None:
                embed.add_field(
                    name=column.name.replace('_', ' ').title(),
                    value=str(value)[:1024],
                    inline=True
                )
        
        return embed
    
    def _format_table(self, items: list) -> str:
        """Format list as ASCII table"""
        if not items:
            return "Empty list"
        
        # Simple table format
        lines = []
        for i, item in enumerate(items[:20], 1):
            lines.append(f"{i:3}. {str(item)[:75]}")
        
        if len(items) > 20:
            lines.append(f"... and {len(items) - 20} more items")
        
        return '\n'.join(lines)
    
    async def _send_file(self, channel, filepath: str, **kwargs):
        """Send file with appropriate handling based on type"""
        path = Path(filepath)
        
        # Determine file type and send appropriately
        if path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
            # Image
            embed = discord.Embed(
                title=kwargs.get('title', '🖼️ Image'),
                color=discord.Color.blue()
            )
            file = discord.File(filepath, path.name)
            embed.set_image(url=f"attachment://{path.name}")
            await channel.send(embed=embed, file=file)
        
        elif path.suffix.lower() in ['.mp3', '.wav', '.ogg', '.m4a']:
            # Audio
            await channel.send(
                "🎵 Audio file:",
                file=discord.File(filepath, path.name)
            )
        
        elif path.suffix.lower() in ['.mp4', '.avi', '.mov', '.webm']:
            # Video
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > 8:
                await channel.send(f"❌ Video too large ({size_mb:.1f} MB > 8 MB limit)")
            else:
                await channel.send(
                    "🎬 Video:",
                    file=discord.File(filepath, path.name)
                )
        
        else:
            # Generic file
            await channel.send(
                f"📎 {path.suffix.upper()} file:",
                file=discord.File(filepath, path.name)
            )
    
    async def _send_bytes(self, channel, data: bytes, **kwargs):
        """Figure out what the bytes are and send appropriately"""
        # Try to detect file type
        if data[:4] == b'\x89PNG':
            # PNG image
            await channel.send(
                file=discord.File(io.BytesIO(data), "image.png")
            )
        elif data[:3] == b'\xff\xd8\xff':
            # JPEG image
            await channel.send(
                file=discord.File(io.BytesIO(data), "image.jpg")
            )
        elif data[:4] == b'RIFF' and data[8:12] == b'WAVE':
            # WAV audio
            await channel.send(
                "🎵 Audio:",
                file=discord.File(io.BytesIO(data), "audio.wav")
            )
        else:
            # Unknown - send as binary
            await channel.send(
                f"📦 Binary data ({len(data)} bytes):",
                file=discord.File(io.BytesIO(data), "data.bin")
            )
    
    def _is_audio_data(self, obj) -> bool:
        """Check if object appears to be audio data"""
        return (
            hasattr(obj, 'shape') and len(obj.shape) in [1, 2] or
            isinstance(obj, (list, tuple)) and all(isinstance(x, (int, float)) for x in obj[:100])
        )
    
    async def _process_audio(self, audio_data) -> Optional[str]:
        """Convert audio data to WAV file"""
        try:
            import numpy as np
            import wave
            
            # Convert to numpy array
            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data)
            
            # Normalize
            if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                audio_data = (audio_data * 32767).astype(np.int16)
            
            # Save as WAV
            temp_file = tempfile.mktemp(suffix='.wav')
            with wave.open(temp_file, 'w') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(44100)
                wav.writeframes(audio_data.tobytes())
            
            return temp_file
        except:
            return None


# Convenience function for go.py integration
def send_to_discord(target: str, *objects, **kwargs) -> bool:
    """
    Send ANY object(s) to Discord
    
    Examples:
        send_to_discord("zeiche", "Hello!")
        send_to_discord("zeiche", image_path)
        send_to_discord("zeiche", tournament_object)
        send_to_discord("zeiche", {"stats": stats_dict})
        send_to_discord("zeiche", dataframe, figure, "Analysis complete!")
    """
    sender = PolymorphicDiscordSender()
    return sender.send(target, *objects, **kwargs)


def demo():
    """Demo the polymorphic sender"""
    print("=" * 60)
    print("🚀 POLYMORPHIC DISCORD SENDER DEMO")
    print("=" * 60)
    
    sender = PolymorphicDiscordSender()
    
    # Demo objects
    demos = [
        "Simple text message",
        {"type": "dictionary", "data": [1, 2, 3], "nested": {"key": "value"}},
        ["list", "of", "items", "to", "send"],
        Exception("Demo error for testing"),
        Path("/home/ubuntu/claude/tournament_tracker/poop_emoji_yellow.png"),
    ]
    
    print("\nObjects that can be sent:")
    for i, obj in enumerate(demos, 1):
        print(f"{i}. {type(obj).__name__}: {str(obj)[:50]}...")
    
    print("\nUsage: send_to_discord('zeiche', obj1, obj2, ...)")
    print("\nThe sender figures out the best way to send ANYTHING!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        demo()
        print("\nUsage: polymorphic_discord_sender.py <target> <object> [object2] ...")
    else:
        target = sys.argv[1]
        
        # Try to evaluate objects (be careful with this in production!)
        objects = []
        for arg in sys.argv[2:]:
            try:
                # Try to evaluate as Python
                obj = eval(arg)
                objects.append(obj)
            except:
                # Treat as string
                objects.append(arg)
        
        success = send_to_discord(target, *objects)
        print("✅ Sent!" if success else "❌ Failed to send")