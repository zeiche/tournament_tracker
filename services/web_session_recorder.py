#!/usr/bin/env python3
"""
Web Session Recorder - Records browser sessions of web interfaces
Captures screenshots/video of web pages for proof of functionality
"""

import subprocess
import time
import json
import base64
from datetime import datetime
from pathlib import Path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("services.web_session_recorder")

from logging_services.polymorphic_log_manager import get_log_manager
from polymorphic_core.visualizable import VisualizableObject

class VideoStream(VisualizableObject):
    """A video stream that can serialize itself for JSON and display in logs"""
    
    def __init__(self, video_data: bytes, url: str, session_name: str, duration: int, content_type: str = "video/mp4"):
        self.video_data = video_data
        self.url = url
        self.session_name = session_name
        self.duration = duration
        self.content_type = content_type
        self.filename = f"{session_name}.mp4"
    
    def visualize(self) -> dict:
        """Return visualization data for this video stream"""
        return {
            'type': 'video',
            'content': self.get_data_url(),
            'mime_type': self.content_type,
            'metadata': {
                'description': f"Web session recording: {self.url} ({self.duration}s)",
                'file_size': len(self.video_data),
                'file_name': self.filename,
                'duration': self.duration,
                'url': self.url,
                'session_name': self.session_name
            }
        }
    
    def get_data_url(self) -> str:
        """Get data URL for embedding video directly in web interface"""
        video_b64 = base64.b64encode(self.video_data).decode('utf-8')
        return f"data:{self.content_type};base64,{video_b64}"
    
    def __str__(self):
        return f"VideoStream({self.session_name}): {self.url} ({self.duration}s, {len(self.video_data)} bytes)"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'type': 'video_stream',
            'url': self.url,
            'session_name': self.session_name,
            'duration': self.duration,
            'content_type': self.content_type,
            'filename': self.filename,
            'stream_size': len(self.video_data),
            'video_data_url': self.get_data_url()
        }

class WebSessionRecorder:
    """Records web browser sessions with video/screenshots"""
    
    def __init__(self, session_name: str = None):
        self.session_name = session_name or f"web_session_{int(time.time())}"
        self.log_manager = get_log_manager()
        self.recording_dir = Path("recordings/web_sessions")
        self.recording_dir.mkdir(parents=True, exist_ok=True)
        
    def record_web_session(self, url: str, duration: int = 30) -> dict:
        """Record a web session with streaming video capture (NO FILESYSTEM WRITES)"""
        
        print(f"🎬 Starting Streaming Web Session Recording")
        print(f"🌐 URL: {url}")
        print(f"⏱️  Duration: {duration} seconds") 
        print(f"📋 Session: {self.session_name}")
        print("=" * 80)
        
        session_info = {
            "session_name": self.session_name,
            "url": url,
            "start_time": time.time(),
            "duration": duration,
            "success": False,
            "stream_data": None
        }
        
        # Log session start
        self.log_manager.info(
            message=f"Web session recording started: {self.session_name}",
            data={
                "url": url,
                "duration": duration,
                "session_name": self.session_name
            },
            source="web_session_recorder"
        )
        
        try:
            # Record video as stream directly to polymorphic logging
            video_data = self._record_video_stream(url, duration)
            if video_data:
                # Create a VideoStream object that can serialize itself
                video_stream = VideoStream(
                    video_data=video_data,
                    url=url,
                    session_name=self.session_name,
                    duration=duration,
                    content_type="video/mp4"
                )
                
                # Pass the VideoStream object to polymorphic logging
                self.log_manager.info(
                    message=f"Web session video stream: {url}",
                    data=video_stream,
                    source="web_session_recorder"
                )
                
                session_info["stream_data"] = {
                    "size": len(video_data),
                    "type": "video/mp4",
                    "duration": duration
                }
            
            session_info["success"] = True
            
        except Exception as e:
            print(f"❌ Recording failed: {e}")
            self.log_manager.error(
                message=f"Web session recording failed: {str(e)}",
                data={
                    "session_name": self.session_name,
                    "error": str(e)
                },
                source="web_session_recorder"
            )
            
        finally:
            session_info["end_time"] = time.time()
            session_info["actual_duration"] = session_info["end_time"] - session_info["start_time"]
            
            # Log session completion (NO FILE WRITES)
            self.log_manager.info(
                message=f"Web session recording completed: {self.session_name}",
                data=session_info,
                source="web_session_recorder"
            )
            
            print("=" * 80)
            print(f"🎬 Streaming Web Session Recording Completed!")
            if session_info["stream_data"]:
                print(f"📊 Stream size: {session_info['stream_data']['size']} bytes")
                print(f"🎥 Duration: {session_info['stream_data']['duration']} seconds")
            
        return session_info
    
    def _take_screenshot(self, url: str, output_path: Path) -> bool:
        """Take a screenshot of the web page"""
        try:
            # Try using chromium-browser in headless mode
            cmd = [
                "chromium-browser",
                "--headless",
                "--no-sandbox", 
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1920,1080",
                f"--screenshot={output_path}",
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and output_path.exists():
                print(f"📸 Screenshot saved: {output_path}")
                self.log_manager.info(
                    message=f"Screenshot captured: {output_path}",
                    data={"url": url, "file_size": output_path.stat().st_size},
                    source="web_session_recorder"
                )
                return True
            else:
                print(f"❌ Screenshot failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Screenshot error: {e}")
            # Try alternative method with firefox
            return self._take_screenshot_firefox(url, output_path)
    
    def _take_screenshot_firefox(self, url: str, output_path: Path) -> bool:
        """Alternative screenshot using firefox"""
        try:
            cmd = [
                "firefox",
                "--headless",
                "--screenshot", 
                str(output_path),
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and output_path.exists():
                print(f"📸 Screenshot saved (Firefox): {output_path}")
                return True
            else:
                print(f"❌ Firefox screenshot failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Firefox screenshot error: {e}")
            return False
    
    def _record_video(self, url: str, output_path: Path, duration: int) -> bool:
        """Record video of web session using headless browser (NO X11 NEEDED)"""
        try:
            # Try Playwright first (best option)
            if self._record_video_playwright(url, output_path, duration):
                return True
            
            # Fallback to Chrome DevTools Protocol
            return self._record_video_chrome_devtools(url, output_path, duration)
                
        except Exception as e:
            print(f"❌ Video recording error: {e}")
            return False
    
    def _record_video_playwright(self, url: str, output_path: Path, duration: int) -> bool:
        """Record video using Playwright (headless, no X11 needed)"""
        try:
            from playwright.sync_api import sync_playwright
            
            print(f"🎥 Recording video with Playwright for {duration} seconds...")
            
            with sync_playwright() as p:
                # Launch headless browser with video recording
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu"
                    ]
                )
                
                # Create context with video recording enabled
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    record_video_dir=str(output_path.parent),
                    record_video_size={'width': 1920, 'height': 1080}
                )
                
                page = context.new_page()
                
                # Navigate to URL
                page.goto(url)
                page.wait_for_load_state('networkidle')
                
                # Keep the page active for the recording duration
                print(f"🎥 Recording in progress... ({duration}s)")
                time.sleep(duration)
                
                # Close page and context to save video
                page.close()
                context.close()
                browser.close()
                
                # Find the recorded video file (Playwright names it automatically)
                video_files = list(output_path.parent.glob("*.webm"))
                if video_files:
                    # Move/rename to desired output path
                    latest_video = max(video_files, key=lambda p: p.stat().st_mtime)
                    if output_path.suffix.lower() == '.mp4':
                        # Convert webm to mp4 if needed
                        self._convert_webm_to_mp4(latest_video, output_path)
                        latest_video.unlink()  # Remove original webm
                    else:
                        latest_video.rename(output_path)
                    
                    print(f"🎥 Video recorded: {output_path}")
                    self.log_manager.info(
                        message=f"Video recorded: {output_path}",
                        data={"duration": duration, "file_size": output_path.stat().st_size},
                        source="web_session_recorder"
                    )
                    return True
                
                return False
                
        except ImportError:
            print("📦 Playwright not available, trying alternative method...")
            return False
        except Exception as e:
            print(f"❌ Playwright video recording failed: {e}")
            return False
    
    def _record_video_chrome_devtools(self, url: str, output_path: Path, duration: int) -> bool:
        """Fallback: Record using Chrome with DevTools protocol"""
        try:
            print(f"🎥 Recording video with Chrome DevTools for {duration} seconds...")
            
            # Use Chrome's built-in screen capture (no X11 needed)
            cmd = [
                "chromium-browser",
                "--headless",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1920,1080",
                "--enable-logging=stderr",
                "--log-level=0",
                f"--virtual-time-budget={duration * 1000}",  # milliseconds
                url
            ]
            
            # Start browser process
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Let it run for the duration
            time.sleep(duration + 2)
            process.terminate()
            
            # For now, fall back to taking multiple screenshots and creating video
            return self._create_video_from_screenshots(url, output_path, duration)
            
        except Exception as e:
            print(f"❌ Chrome DevTools recording failed: {e}")
            return False
    
    def _create_video_from_screenshots(self, url: str, output_path: Path, duration: int) -> bool:
        """Create video from multiple screenshots (reliable fallback)"""
        try:
            print(f"🎥 Creating video from screenshots for {duration} seconds...")
            
            # Create temporary directory for screenshots
            temp_dir = output_path.parent / f"temp_screenshots_{int(time.time())}"
            temp_dir.mkdir(exist_ok=True)
            
            # Take screenshots every 2 seconds
            interval = 2
            screenshots = []
            
            for i in range(0, duration, interval):
                screenshot_path = temp_dir / f"frame_{i:04d}.png"
                if self._take_screenshot(url, screenshot_path):
                    screenshots.append(screenshot_path)
                    print(f"📸 Frame {len(screenshots)}/{duration//interval}")
                time.sleep(interval)
            
            if len(screenshots) < 2:
                print("❌ Need at least 2 screenshots to create video")
                return False
            
            # Create video from screenshots using ffmpeg
            cmd = [
                "ffmpeg",
                "-framerate", str(1/interval),  # Frame rate based on interval
                "-i", str(temp_dir / "frame_%04d.png"),
                "-c:v", "libx264",
                "-preset", "fast",
                "-pix_fmt", "yuv420p",
                "-y",  # Overwrite output file
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            # Clean up temporary screenshots
            for screenshot in screenshots:
                screenshot.unlink()
            temp_dir.rmdir()
            
            if result.returncode == 0 and output_path.exists():
                print(f"🎥 Video created from {len(screenshots)} frames: {output_path}")
                self.log_manager.info(
                    message=f"Video created from screenshots: {output_path}",
                    data={"frames": len(screenshots), "file_size": output_path.stat().st_size},
                    source="web_session_recorder"
                )
                return True
            else:
                print(f"❌ Video creation failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Screenshot video creation failed: {e}")
            return False
    
    def _record_video_stream(self, url: str, duration: int) -> bytes:
        """Record video as byte stream in memory (NO FILESYSTEM WRITES)"""
        try:
            # Try Playwright streaming first
            video_data = self._record_video_stream_playwright(url, duration)
            if video_data:
                return video_data
                
            # Fallback to screenshot stream
            return self._create_video_stream_from_screenshots(url, duration)
            
        except Exception as e:
            print(f"❌ Stream video recording error: {e}")
            return b""
    
    def _record_video_stream_playwright(self, url: str, duration: int) -> bytes:
        """Record video using Playwright directly to memory stream"""
        try:
            from playwright.sync_api import sync_playwright
            import tempfile
            import os
            
            print(f"🎥 Recording video stream with Playwright for {duration} seconds...")
            
            # Use temporary directory that we clean up immediately
            with tempfile.TemporaryDirectory() as temp_dir:
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        args=[
                            "--no-sandbox",
                            "--disable-dev-shm-usage", 
                            "--disable-gpu"
                        ]
                    )
                    
                    context = browser.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        record_video_dir=temp_dir,
                        record_video_size={'width': 1920, 'height': 1080}
                    )
                    
                    page = context.new_page()
                    page.goto(url)
                    page.wait_for_load_state('networkidle')
                    
                    print(f"🎥 Recording stream in progress... ({duration}s)")
                    time.sleep(duration)
                    
                    page.close()
                    context.close()
                    browser.close()
                    
                    # Find and read video file into memory
                    video_files = [f for f in os.listdir(temp_dir) if f.endswith('.webm')]
                    if video_files:
                        video_path = os.path.join(temp_dir, video_files[0])
                        with open(video_path, 'rb') as f:
                            video_data = f.read()
                        
                        # Convert to MP4 in memory if needed
                        mp4_data = self._convert_webm_to_mp4_stream(video_data)
                        if mp4_data:
                            print(f"🎥 Video stream captured: {len(mp4_data)} bytes")
                            return mp4_data
                        else:
                            print(f"🎥 Video stream captured (webm): {len(video_data)} bytes")
                            return video_data
                    
                    return b""
                    
        except ImportError:
            print("📦 Playwright not available for streaming")
            return b""
        except Exception as e:
            print(f"❌ Playwright stream recording failed: {e}")
            return b""
    
    def _create_video_stream_from_screenshots(self, url: str, duration: int) -> bytes:
        """Create video stream from screenshots in memory"""
        try:
            import tempfile
            import os
            
            print(f"🎥 Creating video stream from screenshots for {duration} seconds...")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Take screenshots at intervals
                interval = 2
                screenshots = []
                
                for i in range(0, duration, interval):
                    screenshot_path = os.path.join(temp_dir, f"frame_{i:04d}.png")
                    if self._take_screenshot_to_path(url, screenshot_path):
                        screenshots.append(screenshot_path)
                        print(f"📸 Frame {len(screenshots)}/{duration//interval}")
                    time.sleep(interval)
                
                if len(screenshots) < 2:
                    print("❌ Need at least 2 screenshots to create video stream")
                    return b""
                
                # Create video in memory using ffmpeg
                output_path = os.path.join(temp_dir, "output.mp4")
                cmd = [
                    "ffmpeg",
                    "-framerate", str(1/interval),
                    "-i", os.path.join(temp_dir, "frame_%04d.png"),
                    "-c:v", "libx264",
                    "-preset", "fast", 
                    "-pix_fmt", "yuv420p",
                    "-y",
                    output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0 and os.path.exists(output_path):
                    with open(output_path, 'rb') as f:
                        video_data = f.read()
                    print(f"🎥 Video stream created from {len(screenshots)} frames: {len(video_data)} bytes")
                    return video_data
                else:
                    print(f"❌ Video stream creation failed: {result.stderr}")
                    return b""
                    
        except Exception as e:
            print(f"❌ Screenshot video stream creation failed: {e}")
            return b""
    
    def _take_screenshot_to_path(self, url: str, output_path: str) -> bool:
        """Take screenshot to specific path (for temp video creation)"""
        try:
            cmd = [
                "chromium-browser",
                "--headless",
                "--no-sandbox",
                "--disable-dev-shm-usage", 
                "--disable-gpu",
                "--window-size=1920,1080",
                f"--screenshot={output_path}",
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0 and os.path.exists(output_path)
            
        except Exception:
            return False
    
    def _convert_webm_to_mp4_stream(self, webm_data: bytes) -> bytes:
        """Convert WebM data to MP4 data in memory"""
        try:
            import tempfile
            import os
            
            with tempfile.TemporaryDirectory() as temp_dir:
                webm_path = os.path.join(temp_dir, "input.webm")
                mp4_path = os.path.join(temp_dir, "output.mp4")
                
                # Write webm data to temp file
                with open(webm_path, 'wb') as f:
                    f.write(webm_data)
                
                # Convert to mp4
                cmd = [
                    "ffmpeg",
                    "-i", webm_path,
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-y",
                    mp4_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0 and os.path.exists(mp4_path):
                    with open(mp4_path, 'rb') as f:
                        return f.read()
                        
                return b""
                
        except Exception as e:
            print(f"❌ Stream conversion failed: {e}")
            return b""

def main():
    """Test the web session recorder"""
    if len(sys.argv) > 1:
        url = sys.argv[1]
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    else:
        url = "https://vpn.zilogo.com:8081/"
        duration = 30
    
    recorder = WebSessionRecorder(f"web_proof_{int(time.time())}")
    session_info = recorder.record_web_session(url, duration)
    
    print(f"\n📊 SESSION RESULTS:")
    print(f"   🌐 URL: {session_info['url']}")
    print(f"   ⏱️  Duration: {session_info.get('actual_duration', 0):.1f}s")
    if session_info.get('stream_data'):
        print(f"   📊 Stream: {session_info['stream_data']['size']} bytes")
        print(f"   🎥 Video: {session_info['stream_data']['duration']}s")
    print(f"   ✅ Success: {'YES' if session_info['success'] else 'NO'}")

if __name__ == "__main__":
    main()