#!/usr/bin/env python3
"""
Super simple audio transcription script
"""

import os
import sys
import wave
import json

def simple_transcribe(wav_file):
    """Simple transcription using Vosk directly"""
    
    print(f"🎵 Transcribing: {wav_file}")
    
    if not os.path.exists(wav_file):
        print(f"❌ File not found: {wav_file}")
        return None
    
    # Load WAV file
    try:
        with wave.open(wav_file, 'rb') as wf:
            if wf.getnchannels() != 1:
                print("❌ Audio must be mono")
                return None
            
            sample_rate = wf.getframerate()
            frames = wf.getnframes()
            audio_data = wf.readframes(frames)
            
        duration = frames / sample_rate
        print(f"📊 {sample_rate}Hz, {duration:.1f}s, {len(audio_data):,} bytes")
        
    except Exception as e:
        print(f"❌ Error loading WAV: {e}")
        return None
    
    # Try Vosk
    try:
        import vosk
        
        # Initialize model
        model_path = "/home/ubuntu/claude/tournament_tracker/models/vosk-model-small-en-us-0.15"
        if not os.path.exists(model_path):
            print(f"❌ Vosk model not found: {model_path}")
            return None
            
        print("🔄 Loading Vosk model...")
        model = vosk.Model(model_path)
        
        # Create recognizer for the audio's sample rate
        rec = vosk.KaldiRecognizer(model, sample_rate)
        
        print("🎤 Transcribing...")
        
        # Process audio in chunks
        chunk_size = 4000
        results = []
        
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i+chunk_size]
            
            if rec.AcceptWaveform(chunk):
                result = json.loads(rec.Result())
                text = result.get('text', '').strip()
                if text:
                    results.append(text)
                    print(f"   📝 '{text}'")
        
        # Get final result
        final_result = json.loads(rec.FinalResult())
        final_text = final_result.get('text', '').strip()
        if final_text:
            results.append(final_text)
            print(f"   📝 '{final_text}'")
        
        # Combine all results
        full_text = ' '.join(results).strip()
        
        if full_text:
            print(f"\n✅ TRANSCRIPTION: '{full_text}'")
            return full_text
        else:
            print("⚠️ No speech detected")
            return None
            
    except ImportError:
        print("❌ Vosk not available")
        return None
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 simple_transcribe.py <audio_file.wav>")
        print("Example: python3 simple_transcribe.py test_audio_for_transcription.wav")
        return 1
    
    wav_file = sys.argv[1]
    
    print("🎙️ Simple Audio Transcription")
    print("=" * 40)
    
    result = simple_transcribe(wav_file)
    
    if result:
        print(f"\n🎯 Result: '{result}'")
        return 0
    else:
        print("\n❌ Transcription failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())