# Twilio Chunked Audio Streaming - TODO

## Issues Found in twilio_simple_voice_bridge.py

### 1. Fix infinite loop in continuous_mixed_stream endpoint
**Problem:** The `while True` loop in `/continuous_mixed_stream` (lines 218-242) doesn't properly yield audio chunks
**Location:** `twilio_simple_voice_bridge.py:218-242`
**Fix:** Ensure proper audio data is always yielded, not just silence bytes

### 2. Add proper WAV headers for chunked audio stream  
**Problem:** Chunked stream doesn't send WAV format headers that Twilio expects
**Location:** `twilio_simple_voice_bridge.py:209` (generate function)
**Fix:** Add WAV header at start of stream or use proper audio format

### 3. Implement get_music_chunk() method in BonjourAudioMixer
**Problem:** `self.audio_mixer.get_music_chunk()` called at line 234 but method not found
**Location:** `twilio_simple_voice_bridge.py:234` and `bonjour_audio_mixer.py`
**Fix:** Implement the missing method or use existing get_mixed_stream()

### 4. Fix generator exhaustion issue for mix_audio
**Problem:** `audio_service.mix_audio()` returns a generator that gets consumed once (lines 223-229)
**Location:** `twilio_simple_voice_bridge.py:223-229`
**Fix:** Store generator results or recreate generator for each use

### 5. Add Transfer-Encoding: chunked header to Response
**Problem:** Response uses `Cache-Control: no-cache` but missing `Transfer-Encoding: chunked`
**Location:** `twilio_simple_voice_bridge.py:244-245`
**Fix:** Add proper chunked transfer encoding header

### 6. Increase sleep time to prevent CPU spinning
**Problem:** `time.sleep(0.01)` at line 242 might cause high CPU usage
**Location:** `twilio_simple_voice_bridge.py:242`
**Fix:** Increase to 0.02 or 0.05 seconds for 20-50ms chunks

### 7. Test chunked audio streaming with Twilio
**Task:** Verify fixes work with actual Twilio calls
**Test cases:**
- Background music plays continuously
- Speech interrupts music with ducking
- Multiple speech segments queue properly
- No audio dropouts or glitches

## Implementation Notes

The system is trying to:
1. Stream continuous background music to Twilio calls
2. Mix in TTS speech when needed (with audio ducking)
3. Use a single `play()` call with chunked streaming instead of multiple `play()` calls

Current flow:
```
Twilio Call → /voice endpoint → play(/continuous_mixed_stream) → infinite generator
                                                                    ↓
                                                      yields music chunks or
                                                      speech+music mixed chunks
```

## Related Files
- `twilio_simple_voice_bridge.py` - Main Twilio bridge with chunked streaming
- `audio_service.py` - Audio mixing service with mix_audio() generator
- `bonjour_audio_mixer.py` - Background music mixer (needs get_music_chunk())
- `continuous_stream_service.py` - Continuous audio streaming service

## Priority
High - This is blocking proper audio playback on Twilio calls