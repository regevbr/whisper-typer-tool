#!/usr/bin/env python3

import sys
from contextlib import ExitStack
from audio import AudioManager
from text_typing import TypeController
from transcription import TranscriptionHandler


class WhisperTyperApp:
    """Main application class with proper resource management"""
    
    def __init__(self, model_name="base", silence_threshold=4):
        self.model_name = model_name
        self.silence_threshold = silence_threshold
        self.audio_manager = None
        self.type_controller = None
        self.transcription_handler = None
    
    def __enter__(self):
        """Initialize all components as context manager"""
        self.audio_manager = AudioManager()
        self.type_controller = TypeController()
        self.transcription_handler = TranscriptionHandler(
            self.model_name, 
            self.silence_threshold
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up all resources"""
        if self.audio_manager:
            self.audio_manager.cleanup()
        return False
    
    def on_recording_stop(self):
        """Callback when recording stops"""  
        print("\n🔇 Recording stopped")
        self.audio_manager.play_audio_file("off.wav")
    
    def run(self):
        """Main application loop"""
        print("Loading Whisper model...")
        
        # Reset typing state for new session
        self.type_controller.reset()
        
        try:
            # Initialize RealtimeSTT recorder with optimized settings
            with self.transcription_handler.create_recorder(
                on_realtime_transcription_callback=self.type_controller.type_text_realtime,
                on_recording_stop_callback=self.on_recording_stop
            ) as recorder:
                
                print(f"✅ {self.model_name} model loaded")
                print(f"🎤 Start speaking... (will auto-stop after {self.silence_threshold}s of silence)")
                self.audio_manager.play_audio_file("on.wav")

                recorder.start()
                # Record and get final text
                final_text = recorder.text()

                self.type_controller.type_text_realtime(final_text)
                
                print(f"\n✅ Complete transcription: '{final_text}'")
            
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user")
            self.audio_manager.play_audio_file("off.wav")
            raise
        except Exception as e:
            print(f"Fatal error: {e}")
            self.audio_manager.play_audio_file("off.wav")
            raise