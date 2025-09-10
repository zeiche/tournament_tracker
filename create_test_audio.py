#!/usr/bin/env python3
"""
Create test audio file: 8 seconds of silence followed by "this is a test"
Uses polymorphic TTS service through Bonjour announcements
"""

import sys
import os
import wave
import struct
import subprocess
import time
from pathlib import Path

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from polymorphic_core import announcer, discover_capability
except ImportError:
    print("❌ Polymorphic core not available")
    sys.exit(1)

def create_silence(duration_seconds=8, sample_rate=8000, channels=1, sample_width=2):
    """Create silence audio data"""
    num_samples = int(sample_rate * duration_seconds)
    silence_data = bytes(num_samples * channels * sample_width)  # All zeros = silence
    return silence_data

def generate_tts_with_espeak(text, sample_rate=8000):
    """Generate TTS audio using espeak directly as fallback"""
    try:
        cmd = [
            'espeak',
            '-s', '150',  # Speed
            '-p', '50',   # Pitch
            '-a', '100',  # Amplitude
            '-v', 'en',   # Voice
            '--stdout',
            text
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            print(f"✅ Generated TTS audio with espeak: '{text}'")
            return result.stdout
        else:
            print(f"❌ espeak failed: {result.stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ espeak error: {e}")
        return None

def create_test_wav_file(output_path="test_transcription.wav"):
    """Create the test WAV file with silence + speech"""
    
    sample_rate = 8000  # 8kHz for Twilio compatibility
    channels = 1        # Mono
    sample_width = 2    # 16-bit
    
    print("🔧 Creating test audio file...")
    
    # 1. Create 8 seconds of silence
    print("🤫 Creating 8 seconds of silence...")
    silence_data = create_silence(duration_seconds=8, sample_rate=sample_rate)
    
    # 2. Generate TTS for "this is a test"
    print("🗣️ Generating TTS: 'this is a test'")
    
    # Try to use polymorphic TTS service first
    tts_service = discover_capability('tts')
    tts_data = None
    
    if tts_service:
        print("📢 Found polymorphic TTS service, announcing...")
        announcer.announce(
            "TEXT_TO_SPEECH",
            [
                "TEXT: this is a test",
                "VOICE: normal", 
                "FORMAT: pcm_16bit_8khz",
                "TARGET: test_file"
            ]
        )
        
        # In a real implementation, we'd listen for AUDIO_READY
        # For now, fall back to espeak
        print("⚠️ Using espeak fallback (polymorphic TTS requires event handling)")
        tts_data = generate_tts_with_espeak("this is a test")
    else:
        print("⚠️ No polymorphic TTS service found, using espeak")
        tts_data = generate_tts_with_espeak("this is a test")
    
    if not tts_data:
        print("❌ Failed to generate TTS audio")
        return False
    
    # 3. Convert espeak WAV output to raw PCM
    # espeak outputs WAV format, we need to extract the PCM data
    try:
        # Save espeak output temporarily
        temp_path = "temp_espeak.wav"
        with open(temp_path, 'wb') as f:
            f.write(tts_data)
        
        # Read it back as WAV and extract PCM
        with wave.open(temp_path, 'rb') as wav_file:
            tts_pcm_data = wav_file.readframes(wav_file.getnframes())
            espeak_rate = wav_file.getframerate()
            espeak_channels = wav_file.getnchannels()
            espeak_width = wav_file.getsampwidth()
            
        print(f"📊 espeak output: {espeak_rate}Hz, {espeak_channels}ch, {espeak_width*8}bit")
        
        # Remove temp file
        os.unlink(temp_path)
        
        # Resample if needed (espeak often outputs at 22kHz, we want 8kHz)
        if espeak_rate != sample_rate:
            print(f"🔄 Resampling from {espeak_rate}Hz to {sample_rate}Hz...")
            tts_pcm_data = resample_audio(tts_pcm_data, espeak_rate, sample_rate, espeak_channels)
        
        # Convert to mono if needed
        if espeak_channels == 2 and channels == 1:
            print("🔄 Converting stereo to mono...")
            tts_pcm_data = stereo_to_mono(tts_pcm_data)
            
    except Exception as e:
        print(f"❌ Error processing espeak output: {e}")
        return False
    
    # 4. Combine silence + TTS
    print("🔗 Combining silence + speech...")
    combined_data = silence_data + tts_pcm_data
    
    # 5. Write final WAV file
    print(f"💾 Writing WAV file: {output_path}")
    try:
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(combined_data)
        
        # Get file info
        duration = len(combined_data) / (sample_rate * channels * sample_width)
        file_size = os.path.getsize(output_path)
        
        print(f"✅ Created test audio file:")
        print(f"   📁 File: {output_path}")
        print(f"   ⏱️ Duration: {duration:.1f} seconds")
        print(f"   📊 Format: {sample_rate}Hz, {channels}ch, {sample_width*8}bit")
        print(f"   💿 Size: {file_size:,} bytes")
        print(f"   🎵 Content: 8s silence + 'this is a test'")
        
        # Announce the audio is ready
        announcer.announce(
            "TEST_AUDIO_CREATED",
            [
                f"FILE: {output_path}",
                f"DURATION: {duration:.1f}s",
                "CONTENT: 8s silence + 'this is a test'",
                "FORMAT: WAV 8kHz mono 16bit",
                "READY: For transcription testing"
            ]
        )
        
        return True
        
    except Exception as e:
        print(f"❌ Error writing WAV file: {e}")
        return False

def resample_audio(pcm_data, from_rate, to_rate, channels=1):
    """Simple resampling by decimation (for downsampling)"""
    if from_rate == to_rate:
        return pcm_data
    
    # Simple decimation for downsampling
    factor = from_rate // to_rate
    if factor <= 1:
        return pcm_data  # Can't upsample with this method
    
    # Convert to samples
    samples = []
    for i in range(0, len(pcm_data), 2 * channels):
        if i + 1 < len(pcm_data):
            sample = struct.unpack('<h', pcm_data[i:i+2])[0]
            samples.append(sample)
    
    # Decimate
    decimated_samples = samples[::factor]
    
    # Convert back to bytes
    return b''.join(struct.pack('<h', sample) for sample in decimated_samples)

def stereo_to_mono(pcm_data):
    """Convert stereo PCM to mono by averaging channels"""
    mono_data = bytearray()
    for i in range(0, len(pcm_data), 4):  # 4 bytes = 2 samples of 16-bit
        if i + 3 < len(pcm_data):
            left = struct.unpack('<h', pcm_data[i:i+2])[0]
            right = struct.unpack('<h', pcm_data[i+2:i+4])[0]
            mono = (left + right) // 2
            mono_data.extend(struct.pack('<h', mono))
    return bytes(mono_data)

def main():
    print("🎙️ Creating test audio for transcription testing...")
    print("📡 Using Bonjour polymorphic TTS services...")
    
    # Create the test file
    success = create_test_wav_file("test_transcription.wav")
    
    if success:
        print("\n🎉 Test audio file created successfully!")
        print("🧪 Ready to test transcription services")
        print("💡 Use this file to test voice activity detection and transcription accuracy")
    else:
        print("\n❌ Failed to create test audio file")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())