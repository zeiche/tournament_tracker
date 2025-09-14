#!/usr/bin/env python3
"""
Test script for polymorphic media logging and visualization

This script demonstrates logging various media types that can be clicked
and viewed in the web log interface.
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("test_media_logging")

from logging_services.polymorphic_log_manager import PolymorphicLogManager
from polymorphic_core.visualizable import MediaFile, InteractiveHTML, VisualizableData

def test_media_logging():
    """Test logging various types of media content"""
    
    # Initialize log manager
    log_manager = PolymorphicLogManager()
    print("🗂️ Testing polymorphic media logging system")
    
    # Test 1: Log an image file (if one exists)
    test_images = [
        'tournament_attendance_page.png',
        'tournament_attendance_fullpage.png', 
        'assets/example.png',
        '/tmp/test_image.png'
    ]
    
    for img_path in test_images:
        if os.path.exists(img_path):
            print(f"📷 Logging image: {img_path}")
            media_file = MediaFile(img_path, "Test tournament attendance visualization")
            log_manager.log("INFO", f"Generated attendance visualization: {img_path}", media_file, source="visualization_test")
            break
    else:
        print("⚠️ No test images found - creating a placeholder")
        # Create a simple SVG image for testing
        svg_content = '''
        <svg width="200" height="100" xmlns="http://www.w3.org/2000/svg">
            <rect width="200" height="100" fill="blue"/>
            <text x="50%" y="50%" text-anchor="middle" dy="0.3em" fill="white" font-size="16">Test Image</text>
        </svg>
        '''
        test_svg_path = '/tmp/test_polymorphic_image.svg'
        with open(test_svg_path, 'w') as f:
            f.write(svg_content)
        
        media_file = MediaFile(test_svg_path, "Test SVG image for polymorphic logging")
        log_manager.log("INFO", "Created test SVG image for visualization demo", media_file, source="media_test")
        print(f"✅ Created and logged test SVG: {test_svg_path}")
    
    # Test 2: Log interactive HTML content
    print("📄 Logging interactive HTML content")
    interactive_chart = '''
    <div style="background: linear-gradient(45deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 8px;">
        <h3>🏆 Tournament Statistics</h3>
        <p>Total Tournaments: <strong>42</strong></p>
        <p>Total Players: <strong>1,337</strong></p>
        <p>Active Organizations: <strong>15</strong></p>
        <div style="width: 100%; height: 20px; background: #fff; border-radius: 10px; margin: 10px 0;">
            <div style="width: 75%; height: 100%; background: #4CAF50; border-radius: 10px;"></div>
        </div>
        <p><small>75% growth this quarter</small></p>
        <button onclick="alert('Interactive content clicked!')" style="background: #fff; color: #667eea; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">Click Me!</button>
    </div>
    '''
    
    html_content = InteractiveHTML(interactive_chart, "Interactive tournament dashboard widget")
    log_manager.log("INFO", "Generated interactive tournament dashboard", html_content, source="dashboard_generator")
    
    # Test 3: Log structured data that can be visualized as JSON/table
    print("📊 Logging structured data")
    tournament_data = {
        "tournament_id": 12345,
        "name": "SoCal FGC Weekly #42",
        "date": "2024-09-11",
        "participants": 64,
        "games": ["Street Fighter 6", "Tekken 8", "Granblue Fantasy Versus Rising"],
        "top_players": [
            {"name": "PLAYER1", "placement": 1, "points": 1000},
            {"name": "PLAYER2", "placement": 2, "points": 700},
            {"name": "PLAYER3", "placement": 3, "points": 500}
        ],
        "venue": {
            "name": "Game Center",
            "address": "123 Gaming St, Los Angeles, CA",
            "capacity": 100
        }
    }
    
    viz_data = VisualizableData(tournament_data, "Tournament results data structure", "json")
    log_manager.log("INFO", "Tournament results processed and stored", viz_data, source="tournament_processor")
    
    # Test 4: Log a file path directly (auto-detection)
    print("📁 Logging file path for auto-detection")
    if os.path.exists('tournament_tracker.db'):
        log_manager.log("DEBUG", "Database file accessed for queries", 'tournament_tracker.db', source="database_monitor")
    
    # Test 5: Create and log a simple audio test file (if possible)
    try:
        import wave
        import numpy as np
        
        # Generate a simple beep sound
        duration = 1.0  # seconds
        sample_rate = 44100
        frequency = 440.0  # A4 note
        
        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit integers
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Save as WAV file
        test_audio_path = '/tmp/test_beep.wav'
        with wave.open(test_audio_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes per sample
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        audio_file = MediaFile(test_audio_path, "Test beep sound (440Hz)")
        log_manager.log("INFO", f"Generated test audio file: {test_audio_path}", audio_file, source="audio_generator")
        print(f"🔊 Created and logged test audio: {test_audio_path}")
        
    except ImportError:
        print("⚠️ NumPy not available - skipping audio generation")
    except Exception as e:
        print(f"⚠️ Audio generation failed: {e}")
    
    print("✅ Media logging tests completed!")
    print("🌐 Start the web editor to view clickable log entries:")
    print("   ./go.py --web")
    print("   Then visit: http://localhost:8081/logs")
    print("   Click on log entries with media icons (🖼️ 🔊 👁️) to view content!")

if __name__ == '__main__':
    test_media_logging()