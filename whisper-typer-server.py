#!/usr/bin/env python3

import sys
import signal
import threading
import time
from pynput import keyboard
from app import WhisperTyperApp

# Configuration
WHISPER_MODEL = "tiny"
SILENCE_THRESHOLD = 4    # seconds before auto-stop
HOTKEY = keyboard.Key.menu  # Menu key as default hotkey


class WhisperTyperServer:
    """Server mode for whisper-typer-tool with persistent model and hotkey activation"""
    
    def __init__(self, model_name=WHISPER_MODEL, silence_threshold=SILENCE_THRESHOLD, hotkey=HOTKEY):
        self.model_name = model_name
        self.silence_threshold = silence_threshold
        self.hotkey = hotkey
        self.app = None
        self.is_recording = False
        self.is_shutting_down = False
        self.recording_lock = threading.Lock()
        self.hotkey_listener = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🔔 Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def _on_key_press(self, key):
        """Handle hotkey press events"""
        if self.is_shutting_down:
            return False  # Stop listener
            
        try:
            if key == self.hotkey:
                with self.recording_lock:
                    if not self.is_recording:
                        self._start_recording()
        except Exception as e:
            print(f"⚠️ Hotkey error: {e}")
    
    def _start_recording(self):
        """Start a recording session in a separate thread"""
        if self.is_recording:
            return
            
        self.is_recording = True
        print("🎤 Hotkey pressed - starting recording...")
        
        # Start recording in separate thread to avoid blocking hotkey listener
        recording_thread = threading.Thread(target=self._record_session, daemon=True)
        recording_thread.start()
    
    def _record_session(self):
        """Handle a single recording session"""
        try:
            # Use the persistent app instance to record
            if self.app:
                self.app.record_once()
        except Exception as e:
            print(f"⚠️ Recording error: {e}")
        finally:
            with self.recording_lock:
                self.is_recording = False
    
    def start(self):
        """Start the server and begin listening for hotkeys"""
        print("🚀 Starting Whisper Typer Server...")
        print(f"📝 Model: {self.model_name}")
        print(f"🔇 Silence threshold: {self.silence_threshold}s")
        print(f"⌨️ Hotkey: {self.hotkey}")
        print("Loading Whisper model (this may take a moment)...")
        
        try:
            # Initialize the WhisperTyperApp in server mode
            self.app = WhisperTyperApp(self.model_name, self.silence_threshold, server_mode=True)
            self.app.__enter__()  # Initialize resources
            
            print("✅ Model loaded and ready!")
            print(f"🎧 Server running - press {self.hotkey} to start recording")
            print("💡 Press Ctrl+C to stop the server")
            
            # Start hotkey listener
            self.hotkey_listener = keyboard.Listener(on_press=self._on_key_press)
            self.hotkey_listener.start()
            
            # Keep the main thread alive
            while not self.is_shutting_down:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user")
            self.shutdown()
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            self.shutdown()
            sys.exit(1)
    
    def shutdown(self):
        """Clean shutdown of server"""
        if self.is_shutting_down:
            return
            
        self.is_shutting_down = True
        print("🔄 Shutting down server...")
        
        # Stop hotkey listener
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        
        # Wait for any ongoing recording to finish
        max_wait = 10  # seconds
        wait_count = 0
        while self.is_recording and wait_count < max_wait:
            print(f"⏳ Waiting for recording to finish... ({wait_count}/{max_wait})")
            time.sleep(1)
            wait_count += 1
        
        # Clean up app resources
        if self.app:
            try:
                self.app.__exit__(None, None, None)
            except Exception as e:
                print(f"⚠️ Cleanup error: {e}")
        
        print("✅ Server shutdown complete")


def main():
    """Main entry point for server mode"""
    server = WhisperTyperServer()
    server.start()


if __name__ == "__main__":
    main()