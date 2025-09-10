#!/usr/bin/env python3
"""
Create better test audio with improved voice quality
"""

import sys
import os
import wave
import struct
import subprocess
import tempfile
from pathlib import Path

def create_silence(duration_seconds=8, sample_rate=8000, channels=1, sample_width=2):
    """Create silence audio data"""
    num_samples = int(sample_rate * duration_seconds)
    silence_data = bytes(num_samples * channels * sample_width)
    return silence_data

def generate_better_tts(text, sample_rate=8000):
    """Generate TTS with better voice settings"""
    print(f"🗣️ Generating TTS with improved settings: '{text}'")
    
    # Try festival first (better quality than espeak)
    festival_audio = try_festival(text, sample_rate)
    if festival_audio:
        return festival_audio
    
    # Fall back to improved espeak settings
    return try_improved_espeak(text, sample_rate)

def try_festival(text, sample_rate=8000):
    """Try using festival TTS (better quality)"""
    try:
        # Check if festival is available
        subprocess.run(['which', 'festival'], check=True, capture_output=True)
        
        print("🎭 Using Festival TTS (higher quality)")
        
        # Create festival script
        festival_script = f"""
(voice_cmu_us_slt_arctic_hts)
(set! *tts_audio_format* 'riff)
(set! *tts_audio_sample_rate* {sample_rate})
(tts "{text}")
"""
        
        # Run festival
        result = subprocess.run(
            ['festival', '--batch'],
            input=festival_script,
            text=True,
            capture_output=True
        )
        
        if result.returncode == 0:
            print("✅ Festival TTS generated successfully")
            # Festival outputs to a file by default, we'd need to handle that
            # For now, fall back to espeak
            return None
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ Festival not available, using espeak")
    
    return None

def try_improved_espeak(text, sample_rate=8000):
    """Generate TTS with improved espeak settings"""
    try:
        # Better espeak parameters
        cmd = [
            'espeak',
            '-s', '120',     # Slower speed (was 150)
            '-p', '40',      # Lower pitch (was 50) 
            '-a', '150',     # Higher amplitude
            '-v', 'en+f3',   # Female voice variant
            '-g', '5',       # Gap between words
            '--stdout',
            text
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            print("✅ Generated improved espeak TTS")
            return result.stdout
        else:
            print(f"❌ espeak failed: {result.stderr.decode()}")
    
    except Exception as e:
        print(f"❌ espeak error: {e}")
    
    # Last resort - basic espeak
    try:
        cmd = ['espeak', '-s', '100', '-a', '200', '--stdout', text]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            print("✅ Generated basic espeak TTS")
            return result.stdout
    except Exception as e:
        print(f"❌ Basic espeak failed: {e}")
    
    return None

def create_better_test_wav(output_path="better_test_transcription.wav"):
    """Create improved test WAV file"""
    
    sample_rate = 8000
    channels = 1
    sample_width = 2
    
    print("🔧 Creating improved test audio file...")
    
    # 1. Create 8 seconds of silence
    print("🤫 Creating 8 seconds of silence...")
    silence_data = create_silence(duration_seconds=8, sample_rate=sample_rate)
    
    # 2. Generate better TTS
    tts_data = generate_better_tts("this is a test", sample_rate)
    
    if not tts_data:
        print("❌ Failed to generate TTS audio")
        return False
    
    # 3. Process the TTS audio
    try:
        # Save TTS output temporarily
        temp_path = "temp_tts.wav"
        with open(temp_path, 'wb') as f:
            f.write(tts_data)
        
        # Read back as WAV
        with wave.open(temp_path, 'rb') as wav_file:
            tts_pcm_data = wav_file.readframes(wav_file.getnframes())
            tts_rate = wav_file.getframerate()
            tts_channels = wav_file.getnchannels()
            tts_width = wav_file.getsampwidth()
        
        print(f"📊 TTS output: {tts_rate}Hz, {tts_channels}ch, {tts_width*8}bit")
        
        # Clean up temp file
        os.unlink(temp_path)
        
        # Resample if needed
        if tts_rate != sample_rate:
            print(f"🔄 Resampling from {tts_rate}Hz to {sample_rate}Hz...")
            tts_pcm_data = simple_resample(tts_pcm_data, tts_rate, sample_rate, tts_channels)
        
        # Convert to mono if needed
        if tts_channels == 2 and channels == 1:
            print("🔄 Converting to mono...")
            tts_pcm_data = stereo_to_mono(tts_pcm_data)
    
    except Exception as e:
        print(f"❌ Error processing TTS: {e}")
        return False
    
    # 4. Combine silence + speech
    print("🔗 Combining silence + improved speech...")
    combined_data = silence_data + tts_pcm_data
    
    # 5. Write final WAV
    print(f"💾 Writing improved WAV: {output_path}")
    try:
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width) 
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(combined_data)
        
        duration = len(combined_data) / (sample_rate * channels * sample_width)
        file_size = os.path.getsize(output_path)
        
        print(f"✅ Created improved test audio:")
        print(f"   📁 File: {output_path}")
        print(f"   ⏱️ Duration: {duration:.1f} seconds")
        print(f"   🎵 Content: 8s silence + clearer 'this is a test'")
        print(f"   💿 Size: {file_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error writing WAV: {e}")
        return False

def simple_resample(pcm_data, from_rate, to_rate, channels=1):
    """Simple resampling by decimation"""
    if from_rate == to_rate:
        return pcm_data
    
    factor = from_rate // to_rate
    if factor <= 1:
        return pcm_data
    
    # Convert to samples, decimate, convert back
    samples = []
    for i in range(0, len(pcm_data), 2 * channels):
        if i + 1 < len(pcm_data):
            sample = struct.unpack('<h', pcm_data[i:i+2])[0]
            samples.append(sample)
    
    decimated_samples = samples[::factor]
    return b''.join(struct.pack('<h', sample) for sample in decimated_samples)

def stereo_to_mono(pcm_data):
    """Convert stereo to mono"""
    mono_data = bytearray()
    for i in range(0, len(pcm_data), 4):
        if i + 3 < len(pcm_data):
            left = struct.unpack('<h', pcm_data[i:i+2])[0]
            right = struct.unpack('<h', pcm_data[i+2:i+4])[0]
            mono = (left + right) // 2
            mono_data.extend(struct.pack('<h', mono))
    return bytes(mono_data)

def main():
    print("🎙️ Creating Better Test Audio for Transcription")
    print("=" * 50)
    
    success = create_better_test_wav("better_test_transcription.wav")
    
    if success:
        print("\n🎉 Improved test audio created!")
        print("🔊 Should have much clearer speech quality")
        print("🧪 Ready for transcription testing")
        
        # Also create a very simple test
        print("\n🔧 Creating additional simple test...")
        simple_success = create_simple_test()
        
        if simple_success:
            print("✅ Created simple test file too")
    else:
        print("\n❌ Failed to create improved test audio")
        return 1
    
    return 0

def create_simple_test():
    """Create a very simple, clear test"""
    try:
        # Just the speech part, no silence
        cmd = [
            'espeak',
            '-s', '80',      # Very slow
            '-a', '200',     # Loud
            '-p', '35',      # Low pitch
            '-g', '10',      # Long gaps
            '--stdout',
            'hello world test'
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            with open("simple_speech_test.wav", 'wb') as f:
                f.write(result.stdout)
            print("✅ Created simple_speech_test.wav")
            return True
    except:
        pass
    
    return False

if __name__ == "__main__":
    sys.exit(main())