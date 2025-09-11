#!/usr/bin/env python3
"""
DTMF Detector Service - Real-time DTMF tone detection
Processes raw audio streams and detects DTMF keypresses in real-time
"""

import numpy as np
from polymorphic_core import announcer, register_capability

class DTMFDetector:
    """Real-time DTMF detection service using Goertzel algorithm"""
    
    # DTMF frequency pairs
    DTMF_FREQS = {
        '1': (697, 1209), '2': (697, 1336), '3': (697, 1477),
        '4': (770, 1209), '5': (770, 1336), '6': (770, 1477),
        '7': (852, 1209), '8': (852, 1336), '9': (852, 1477),
        '*': (941, 1209), '0': (941, 1336), '#': (941, 1477)
    }
    
    def __init__(self, sample_rate=8000, threshold=1000):
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.last_detection = None
        self.detection_count = 0
        
        # Register as audio service
        register_capability('dtmf_detector', self)
        
        # Announce our service
        announcer.announce(
            "DTMF Detector",
            [
                "I detect DTMF key presses in real-time audio streams",
                "I use the Goertzel algorithm for efficient tone detection", 
                "I work with 8kHz mulaw audio from Twilio streams",
                "I announce DTMF_DETECTED when keys are pressed",
                "I prevent false positives with confirmation logic"
            ]
        )
    
    def detect_from_audio_bytes(self, audio_bytes, format='mulaw'):
        """
        Detect DTMF from raw audio bytes in real-time
        
        Args:
            audio_bytes: Raw audio data
            format: 'mulaw' (default) or 'linear16'
            
        Returns:
            str: Detected digit ('1'-'9', '*', '#') or None
        """
        try:
            # Convert audio to numpy array
            if format == 'mulaw':
                # Convert mulaw to linear PCM (approximate)
                audio_samples = self._mulaw_to_linear(audio_bytes)
            else:
                audio_samples = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
            
            # Need sufficient samples for frequency analysis
            if len(audio_samples) < 160:  # ~20ms at 8kHz
                return None
            
            # Detect DTMF using Goertzel algorithm
            detected_digit = self._detect_dtmf_goertzel(audio_samples)
            
            if detected_digit:
                # Confirmation logic to prevent false positives
                if detected_digit == self.last_detection:
                    self.detection_count += 1
                    if self.detection_count >= 2:  # Require 2 consecutive detections
                        self._announce_detection(detected_digit)
                        self.detection_count = 0
                        return detected_digit
                else:
                    self.last_detection = detected_digit
                    self.detection_count = 1
            else:
                self.last_detection = None
                self.detection_count = 0
            
            return None
            
        except Exception as e:
            print(f"❌ DTMF detection error: {e}")
            return None
    
    def _mulaw_to_linear(self, mulaw_bytes):
        """Convert mulaw audio to linear PCM (simplified)"""
        mulaw_array = np.frombuffer(mulaw_bytes, dtype=np.uint8)
        # Simplified mulaw decode (proper implementation would use tables)
        linear = ((mulaw_array.astype(np.float32) - 128) * 256).astype(np.float32)
        return linear
    
    def _detect_dtmf_goertzel(self, samples):
        """Detect DTMF using Goertzel algorithm for efficiency"""
        # Check each DTMF digit
        for digit, (low_freq, high_freq) in self.DTMF_FREQS.items():
            low_power = self._goertzel_filter(samples, low_freq)
            high_power = self._goertzel_filter(samples, high_freq)
            
            # Both frequencies must be present with sufficient power
            if low_power > self.threshold and high_power > self.threshold:
                # Check ratio to ensure it's a clean tone
                total_power = np.sum(samples ** 2)
                if total_power > 0:
                    tone_ratio = (low_power + high_power) / total_power
                    if tone_ratio > 0.1:  # Tone dominates the signal
                        return digit
        
        return None
    
    def _goertzel_filter(self, samples, target_freq):
        """Goertzel algorithm for single frequency detection"""
        N = len(samples)
        k = int(0.5 + (N * target_freq) / self.sample_rate)
        w = (2.0 * np.pi * k) / N
        cosine = np.cos(w)
        coeff = 2.0 * cosine
        
        q0 = q1 = q2 = 0.0
        for sample in samples:
            q0 = coeff * q1 - q2 + sample
            q2 = q1
            q1 = q0
        
        # Calculate power
        power = q1 * q1 + q2 * q2 - q1 * q2 * coeff
        return power
    
    def _announce_detection(self, digit):
        """Announce DTMF detection"""
        import time
        announcer.announce(
            "DTMF_DETECTED",
            [
                f"DIGIT: {digit}",
                f"TIMESTAMP: {time.time()}",
                "SOURCE: real_time_audio_stream",
                "CONFIDENCE: high"
            ]
        )
        print(f"🔢 DTMF detected: {digit}")

# Global instance
_dtmf_detector = None

def get_dtmf_detector():
    """Get the global DTMF detector instance"""
    global _dtmf_detector
    if _dtmf_detector is None:
        _dtmf_detector = DTMFDetector()
    return _dtmf_detector

if __name__ == "__main__":
    # Test the detector
    detector = get_dtmf_detector()
    print("🔢 DTMF Detector service running...")
    print("📡 Ready to detect key presses in audio streams")