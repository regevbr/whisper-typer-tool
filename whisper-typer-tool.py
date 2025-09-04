#!/usr/bin/env python3

import sys
import time
import pyaudio
import wave
from RealtimeSTT import AudioToTextRecorder
import pyperclip
from pynput import keyboard

# Configuration
WHISPER_MODEL = "base"
SILENCE_THRESHOLD = 4    # seconds before auto-stop

# Track what we've already typed to avoid duplicates
last_typed_text = ""

def play_audio_file(filename):
    """Play audio file using pyaudio"""
    try:
        audio = pyaudio.PyAudio()
        wf = wave.open(filename, 'rb')
        
        stream = audio.open(
            format=audio.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True
        )
        
        data = wf.readframes(1024)
        while data:
            stream.write(data)
            data = wf.readframes(1024)
        
        stream.stop_stream()
        stream.close()
        wf.close()
        audio.terminate()
    except Exception as e:
        print(f"Warning: Could not play audio file {filename}: {e}")


def type_text_realtime(text):
    """Type only new text from real-time transcription updates"""
    global last_typed_text
    
    if not text or not text.strip():
        return
    
    # Only type if this is new content
    if text != last_typed_text and len(text) > len(last_typed_text):
        # Extract only the new part
        new_text = text[len(last_typed_text):]
        
        if new_text.strip():  # Only type if there's actual new content
            print(f"💬 New: '{new_text}'")
            
            try:
                # Use pyperclip for cross-platform clipboard operations
                pyperclip.copy(new_text)
                
                # Small delay to ensure clipboard is set
                time.sleep(0.01)
                
                # Paste using Ctrl+V (cross-platform)
                kb = keyboard.Controller()
                with kb.pressed(keyboard.Key.ctrl):
                    kb.press('v')
                    kb.release('v')
                
                # Update what we've typed
                last_typed_text = text
                
            except Exception as e:
                print(f"Warning: Could not type text '{new_text}': {e}")
    else:
        print(f"💭 Duplicate: '{text}' (skipping)")


def on_recording_stop():
    """Callback when recording stops"""  
    print("\n🔇 Recording stopped")
    play_audio_file("off.wav")


def main():
    """Main entry point"""
    global last_typed_text
    
    print("Loading Whisper model...")
    
    # Reset typed text for new session
    last_typed_text = ""
    
    try:
        # Initialize RealtimeSTT recorder with optimized settings
        with AudioToTextRecorder(
            # Model configuration
            model=WHISPER_MODEL,
            language="en",
            device="cpu",
            compute_type="int8",
            
            # VAD Configuration for better speech detection
            silero_sensitivity=0.4,          # Silero VAD sensitivity (0.0-1.0)
            webrtc_sensitivity=2,            # WebRTC VAD aggressiveness (0-3)
            
            # Recording behavior
            post_speech_silence_duration=SILENCE_THRESHOLD,  # Stop after N seconds of silence
            min_length_of_recording=0.5,     # Minimum recording duration
            
            # Real-time transcription settings
            enable_realtime_transcription=True,
            realtime_processing_pause=0.2,   # Update every 200ms for responsiveness
            realtime_model_type=WHISPER_MODEL,  # Use same model for consistency
            
            # Callbacks
            on_recording_stop=on_recording_stop,
            on_realtime_transcription_update=type_text_realtime,
            
            # Performance settings
            use_microphone=True,
            spinner=False,                   # Disable spinner for cleaner output
            early_transcription_on_silence=1,    # Faster transcription on silence
        ) as recorder:
            
            print(f"✅ {WHISPER_MODEL} model loaded")
            print(f"🎤 Start speaking... (will auto-stop after {SILENCE_THRESHOLD}s of silence)")
            play_audio_file("on.wav")

            recorder.start()
            # Record and get final text
            final_text = recorder.text()
            
            print(f"\n✅ Complete transcription: '{final_text}'")
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        play_audio_file("off.wav")
    except Exception as e:
        print(f"Fatal error: {e}")
        play_audio_file("off.wav")
        sys.exit(1)
    
    print("✅ Exiting...")
    sys.exit(0)


if __name__ == "__main__":
    main()