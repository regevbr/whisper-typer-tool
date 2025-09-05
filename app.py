#!/usr/bin/env python3

import sys
from contextlib import ExitStack
from audio import AudioManager
from text_typing import TypeController
from transcription import TranscriptionHandler


class WhisperTyperApp:
    """Main application class with proper resource management"""
    
    def __init__(self, model_name="base", silence_threshold=4, server_mode=False):
        self.model_name = model_name
        self.silence_threshold = silence_threshold
        self.server_mode = server_mode
        self.audio_manager = None
        self.type_controller = None
        self.transcription_handler = None
        self.recorder = None  # Always create persistent recorder
    
    def __enter__(self):
        """Initialize all components as context manager"""
        self.audio_manager = AudioManager()
        self.type_controller = TypeController()
        self.transcription_handler = TranscriptionHandler(
            self.model_name, 
            self.silence_threshold
        )
        
        # Always initialize persistent recorder (unified architecture)
        print("Initializing persistent recorder...")
        self.recorder = self.transcription_handler.create_recorder(
            on_realtime_transcription_callback=self.type_controller.type_text_realtime,
            on_recording_stop_callback=self.on_recording_stop
        )
        print(f"✅ {self.model_name} model loaded")
        # Pre-initialize the recorder's model
        self.recorder.__enter__()
            
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up all resources"""
        # Clean up persistent recorder (always present now)
        if self.recorder:
            try:
                self.recorder.__exit__(exc_type, exc_val, exc_tb)
            except Exception as e:
                print(f"⚠️ Recorder cleanup error: {e}")
        
        if self.audio_manager:
            self.audio_manager.cleanup()
        return False
    
    def on_recording_stop(self):
        """Callback when recording stops"""  
        print("\n🔇 Recording stopped")
        self.audio_manager.play_audio_file("off.wav")
    
    def record_once(self):
        """Record a single session using the persistent recorder"""
        if not self.recorder:
            raise RuntimeError("record_once() called before recorder initialization")
        
        # Reset typing state for new session
        self.type_controller.reset()
        
        try:
            print(f"🎤 Recording... (will auto-stop after {self.silence_threshold}s of silence)")
            self.audio_manager.play_audio_file("on.wav")
            
            # Start recording using persistent recorder
            self.recorder.start()
            final_text = self.recorder.text()
            
            # Ensure final text is typed
            self.type_controller.type_text_realtime(final_text)
            
            print(f"\n✅ Complete transcription: '{final_text}'")
            
        except Exception as e:
            print(f"⚠️ Recording error: {e}")
            self.audio_manager.play_audio_file("off.wav")
            raise
